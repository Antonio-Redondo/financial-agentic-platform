"""PII detection and redaction engine (pure-Python, no extra dependencies).

Detects and masks personally identifiable / sensitive financial information so
it never reaches the user, the logs, or an off-machine trace. Built for a
financial assistant, so the detector set is weighted toward financial
identifiers (SSN, bank account, ABA routing, credit card, IBAN, EIN) alongside
the usual contact identifiers (email, phone).

Design notes
------------
* **Regex + validators, not ML.** Keeps the local-only, dependency-light
  philosophy of the app. Each detector pairs a pattern with an optional
  ``validator`` (Luhn for cards, ABA checksum for routing numbers, area-number
  rules for SSNs) to cut false positives on arbitrary digit runs.
* **Context-gated detectors.** Generic things like "a bank account number" are
  indistinguishable from any integer, so those detectors only fire when a
  nearby keyword ("account", "acct", "routing", …) is present.
* **Overlap resolution.** All matches are collected, then overlapping spans are
  resolved by priority (a card number shouldn't also be reported as a phone
  number) before the string is rebuilt in a single pass.

Public API
----------
* :func:`detect` → list of :class:`Finding` (no mutation).
* :func:`redact` → ``(redacted_text, findings)``.
* :func:`summarize` → ``{type: count}`` for metadata / logging.
"""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Validators — reduce false positives on bare digit runs.
# ---------------------------------------------------------------------------


def _digits(s: str) -> str:
    return re.sub(r"\D", "", s)


def luhn_ok(value: str) -> bool:
    """Luhn (mod-10) checksum — credit/debit card validation."""
    digits = _digits(value)
    if not (13 <= len(digits) <= 19):
        return False
    total, alt = 0, False
    for ch in reversed(digits):
        d = ord(ch) - 48
        if alt:
            d *= 2
            if d > 9:
                d -= 9
        total += d
        alt = not alt
    return total % 10 == 0


def ssn_ok(value: str) -> bool:
    """Reject SSNs that the SSA never issues (area 000/666/900-999, etc.)."""
    digits = _digits(value)
    if len(digits) != 9:
        return False
    area, group, serial = digits[:3], digits[3:5], digits[5:]
    if area in ("000", "666") or area[0] == "9":
        return False
    if group == "00" or serial == "0000":
        return False
    if digits == digits[0] * 9:  # 000000000, 111111111, …
        return False
    return True


def aba_ok(value: str) -> bool:
    """ABA routing-number checksum (9 digits, weighted mod-10)."""
    d = _digits(value)
    if len(d) != 9:
        return False
    checksum = (
        3 * (int(d[0]) + int(d[3]) + int(d[6]))
        + 7 * (int(d[1]) + int(d[4]) + int(d[7]))
        + 1 * (int(d[2]) + int(d[5]) + int(d[8]))
    )
    return checksum % 10 == 0 and d[0] in "0123"  # first digit: Fed district


def iban_ok(value: str) -> bool:
    """IBAN mod-97 checksum (ISO 13616)."""
    s = re.sub(r"\s", "", value).upper()
    if not re.fullmatch(r"[A-Z]{2}\d{2}[A-Z0-9]{10,30}", s):
        return False
    rearranged = s[4:] + s[:4]
    numeric = "".join(
        str(ord(c) - 55) if c.isalpha() else c for c in rearranged
    )
    try:
        return int(numeric) % 97 == 1
    except ValueError:
        return False


# ---------------------------------------------------------------------------
# Detector definitions
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Detector:
    name: str                       # e.g. "US_SSN"
    label: str                      # human label for placeholders, e.g. "SSN"
    pattern: re.Pattern
    priority: int = 50              # higher wins on overlap
    validator: Optional[Callable[[str], bool]] = None
    # If set, the match only counts when one of these keywords appears within
    # ``context_window`` chars before the match (gates generic numeric runs).
    context_keywords: Tuple[str, ...] = ()
    context_window: int = 40
    keep_last: int = 4              # digits kept visible by the "partial" masker


@dataclass(frozen=True)
class Finding:
    type: str       # detector name
    label: str      # human label
    start: int
    end: int
    value: str      # the raw matched text (kept in-process only)

    @property
    def preview(self) -> str:
        """A non-sensitive description for logs (never the raw value)."""
        return f"{self.label}@{self.start}:{self.end}"


_KW = {
    "account": ("account", "acct", "a/c", "iban", "bank"),
    "routing": ("routing", "aba", "rtn", "transit"),
}

DETECTORS: List[Detector] = [
    # --- Contact identifiers ---
    Detector(
        name="EMAIL", label="EMAIL", priority=70,
        pattern=re.compile(r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b"),
    ),
    Detector(
        name="PHONE", label="PHONE", priority=30,
        pattern=re.compile(
            r"(?<!\d)(?:\+?1[\s.\-]?)?(?:\(\d{3}\)|\d{3})[\s.\-]\d{3}[\s.\-]\d{4}(?!\d)"
        ),
    ),
    Detector(
        name="IP_ADDRESS", label="IP", priority=40,
        pattern=re.compile(
            r"\b(?:(?:25[0-5]|2[0-4]\d|1?\d?\d)\.){3}(?:25[0-5]|2[0-4]\d|1?\d?\d)\b"
        ),
    ),
    # --- Government identifiers ---
    Detector(
        name="US_SSN", label="SSN", priority=90, validator=ssn_ok,
        pattern=re.compile(r"(?<!\d)\d{3}[-\s]\d{2}[-\s]\d{4}(?!\d)"),
    ),
    Detector(
        name="US_EIN", label="EIN", priority=80,
        pattern=re.compile(r"(?<!\d)\d{2}-\d{7}(?!\d)"),
        context_keywords=("ein", "employer id", "tax id", "tin", "federal id"),
    ),
    # --- Financial identifiers ---
    Detector(
        name="CREDIT_CARD", label="CARD", priority=85, validator=luhn_ok,
        pattern=re.compile(r"(?<!\d)(?:\d[ -]?){13,19}(?!\d)"),
    ),
    Detector(
        name="IBAN", label="IBAN", priority=80, validator=iban_ok,
        pattern=re.compile(r"\b[A-Z]{2}\d{2}(?:[ ]?[A-Z0-9]){10,30}\b"),
    ),
    Detector(
        name="ABA_ROUTING", label="ROUTING", priority=75, validator=aba_ok,
        pattern=re.compile(r"(?<!\d)\d{9}(?!\d)"),
        context_keywords=_KW["routing"],
    ),
    Detector(
        name="BANK_ACCOUNT", label="ACCOUNT", priority=60,
        pattern=re.compile(r"(?<!\d)\d{6,17}(?!\d)"),
        context_keywords=_KW["account"], keep_last=4,
    ),
]


# ---------------------------------------------------------------------------
# Masking strategies
# ---------------------------------------------------------------------------


def _mask_partial(value: str, det: Detector) -> str:
    """Keep the last ``keep_last`` digits/chars, mask the rest, keep separators."""
    keep = det.keep_last
    visible = 0
    out = []
    for ch in reversed(value):
        if ch.isalnum():
            if visible < keep:
                out.append(ch)
                visible += 1
            else:
                out.append("•")
        else:
            out.append(ch)  # preserve dashes/spaces/@ structure
    return "".join(reversed(out))


def _mask_label(value: str, det: Detector) -> str:
    return f"[REDACTED_{det.label}]"


def _mask_hash(value: str, det: Detector) -> str:
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()[:10]
    return f"[{det.label}:{digest}]"


def _mask_remove(value: str, det: Detector) -> str:
    return f"[{det.label}]"


_MASKERS: Dict[str, Callable[[str, Detector], str]] = {
    "partial": _mask_partial,
    "label": _mask_label,
    "hash": _mask_hash,
    "remove": _mask_remove,
}


def mask_value(value: str, det: Detector, strategy: str = "partial") -> str:
    masker = _MASKERS.get(strategy, _mask_partial)
    return masker(value, det)


# ---------------------------------------------------------------------------
# Detection + redaction
# ---------------------------------------------------------------------------


def _context_ok(det: Detector, text: str, start: int) -> bool:
    if not det.context_keywords:
        return True
    window = text[max(0, start - det.context_window): start].lower()
    return any(kw in window for kw in det.context_keywords)


def detect(text: str, enabled: Optional[Callable[[str], bool]] = None) -> List[Finding]:
    """Return non-overlapping PII findings in ``text``.

    ``enabled`` is an optional predicate ``name -> bool`` so the caller's policy
    can switch individual detectors off. Overlapping matches are resolved by
    detector priority (then by longer span), so e.g. a 16-digit card is reported
    once as CARD, not also as ACCOUNT.
    """
    if not text:
        return []

    raw: List[Tuple[Finding, int]] = []  # (finding, priority)
    for det in DETECTORS:
        if enabled is not None and not enabled(det.name):
            continue
        for m in det.pattern.finditer(text):
            value = m.group(0)
            if det.validator is not None and not det.validator(value):
                continue
            if not _context_ok(det, text, m.start()):
                continue
            raw.append(
                (Finding(det.name, det.label, m.start(), m.end(), value), det.priority)
            )

    # Resolve overlaps: prefer higher priority, then longer span.
    raw.sort(key=lambda fp: (fp[1], fp[0].end - fp[0].start), reverse=True)
    chosen: List[Finding] = []
    for finding, _ in raw:
        if any(not (finding.end <= c.start or finding.start >= c.end) for c in chosen):
            continue  # overlaps an already-accepted, higher-priority finding
        chosen.append(finding)

    chosen.sort(key=lambda f: f.start)
    return chosen


# Detector lookup for the redaction pass.
_BY_NAME = {d.name: d for d in DETECTORS}


def redact(text: str, strategy: str = "partial",
           enabled: Optional[Callable[[str], bool]] = None
           ) -> Tuple[str, List[Finding]]:
    """Return ``(redacted_text, findings)``. Non-destructive to the input."""
    findings = detect(text, enabled=enabled)
    if not findings:
        return text, []
    out, cursor = [], 0
    for f in findings:
        out.append(text[cursor:f.start])
        out.append(mask_value(f.value, _BY_NAME[f.type], strategy))
        cursor = f.end
    out.append(text[cursor:])
    return "".join(out), findings


def summarize(findings: List[Finding]) -> Dict[str, int]:
    """``{detector_name: count}`` — safe to log / store as metadata."""
    counts: Dict[str, int] = {}
    for f in findings:
        counts[f.type] = counts.get(f.type, 0) + 1
    return counts
