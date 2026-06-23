"""High-level guardrail facade used by the rest of the app.

One object, three checkpoints, mirroring the data flow through the graph:

    user query ──▶ check_input ──▶ planner/retriever
    retrieved chunks ──▶ sanitize_context ──▶ analyst prompt
    analyst answer ──▶ filter_output ──▶ UI / storage / trace

Plus two helpers used off the hot path:

    scrub_for_log(text)        — PII-safe string for logs / traces
    scan_document(text)        — PII summary + optional redaction at ingest

Everything degrades gracefully: if ``GUARDRAILS_ENABLED=false`` the methods are
near pass-throughs, and any internal error never blocks a query (guardrails
fail open for availability, but log the failure).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Tuple

from . import injection, pii
from .config import GuardrailConfig, load


@dataclass
class InputDecision:
    """Outcome of :meth:`Guardrails.check_input`."""
    allowed: bool
    reason: str = ""                       # user-facing message when blocked
    sanitized_query: str = ""              # PII-scrubbed copy for logging only
    injection: Optional[injection.InjectionResult] = None
    pii_summary: Dict[str, int] = field(default_factory=dict)
    notes: List[str] = field(default_factory=list)


@dataclass
class OutputResult:
    """Outcome of :meth:`Guardrails.filter_output`."""
    text: str
    redacted: bool = False
    pii_summary: Dict[str, int] = field(default_factory=dict)
    notes: List[str] = field(default_factory=list)


class _Passthrough:
    """No-op stream wrapper used when output redaction is off."""

    def __init__(self, emit: Callable[[str], None]):
        self._emit = emit

    def feed(self, token: str) -> None:
        if token:
            self._emit(token)

    def flush(self) -> None:
        pass


class StreamRedactor:
    """Redacts PII in a streamed token flow before it reaches the screen.

    PII spans multiple tokens (``"123" "-" "45" "-" "6789"``), so tokens can't
    be masked independently. This buffers the live text and only commits the
    prefix that is *stable* — i.e. far enough from the end that no future token
    could extend a PII match into it. The held-back window
    (``stream_hold_chars``) must exceed the longest possible match. Any match
    straddling the commit boundary pushes the boundary back to the match start,
    so a number is never half-emitted before it can be masked.
    """

    def __init__(self, guard: "Guardrails", emit: Callable[[str], None]):
        self._guard = guard
        self._emit = emit
        self._hold = max(16, guard.config.stream_hold_chars)
        self._buf = ""

    def feed(self, token: str) -> None:
        if not token:
            return
        self._buf += token
        cut = len(self._buf) - self._hold
        if cut <= 0:
            return
        # Don't cut through a PII match that straddles the boundary.
        for f in pii.detect(self._buf, enabled=self._guard._pii_enabled):
            if f.start < cut < f.end:
                cut = min(cut, f.start)
        if cut <= 0:
            return
        committed, self._buf = self._buf[:cut], self._buf[cut:]
        red, _ = self._guard._redact(committed)
        if red:
            self._emit(red)

    def flush(self) -> None:
        if self._buf:
            red, _ = self._guard._redact(self._buf)
            self._buf = ""
            if red:
                self._emit(red)


# A generic refusal that doesn't echo the offending text back.
_INJECTION_REFUSAL = (
    "⚠️ This request looks like an attempt to override the assistant's "
    "instructions, so it was blocked by the safety guardrails. Please rephrase "
    "your question about the financial documents or analysis."
)
_TOO_LONG_REFUSAL = (
    "⚠️ Your message is longer than the {limit:,}-character limit. "
    "Please shorten it and try again."
)


class Guardrails:
    """Stateless policy enforcer. Cheap to construct; reads config once."""

    def __init__(self, config: Optional[GuardrailConfig] = None):
        self.config = config or load()

    # ----------------------------------------------------------- helpers
    def _pii_enabled(self, name: str) -> bool:
        return self.config.acts_on(name)

    def _redact(self, text: str) -> Tuple[str, List[pii.Finding]]:
        return pii.redact(text, strategy=self.config.pii_strategy,
                          enabled=self._pii_enabled)

    # ----------------------------------------------------------- 1) input
    def check_input(self, query: str) -> InputDecision:
        """Validate a user query before it enters the graph."""
        cfg = self.config
        if not cfg.enabled:
            return InputDecision(allowed=True, sanitized_query=query)

        query = query or ""
        notes: List[str] = []

        # Abuse / unbounded-consumption guard (LLM10).
        if len(query) > cfg.max_input_chars:
            return InputDecision(
                allowed=False,
                reason=_TOO_LONG_REFUSAL.format(limit=cfg.max_input_chars),
                notes=[f"input rejected: {len(query)} > {cfg.max_input_chars} chars"],
            )

        # Direct prompt-injection (LLM01).
        inj = injection.scan(query)
        if inj.detected:
            notes.append(f"prompt-injection heuristics fired: {inj.summary}")
            if cfg.injection_action == "block":
                return InputDecision(
                    allowed=False, reason=_INJECTION_REFUSAL,
                    injection=inj, notes=notes,
                )

        # PII in the query — scrubbed copy for logging/tracing only. The model
        # still receives the original text so it can answer the user's question.
        sanitized, pii_summary = query, {}
        if cfg.pii_enabled and cfg.pii_redact_input:
            sanitized, findings = self._redact(query)
            pii_summary = pii.summarize(findings)
            if pii_summary:
                notes.append(f"PII in query (scrubbed for logs): {pii_summary}")

        return InputDecision(
            allowed=True, sanitized_query=sanitized, injection=inj,
            pii_summary=pii_summary, notes=notes,
        )

    # -------------------------------------------------------- 2) context
    def sanitize_context(self, context: str) -> Tuple[str, List[str]]:
        """Clean retrieved document context before it reaches the analyst prompt.

        Defends against indirect prompt-injection and (optionally) strips PII
        out of the grounding text so it can't be echoed into the answer.
        Returns ``(clean_context, notes)``.
        """
        cfg = self.config
        notes: List[str] = []
        if not cfg.enabled or not context:
            return context, notes

        # Indirect injection (LLM01): defang instruction-like lines.
        context, inj = injection.neutralize_context(context)
        if inj.detected:
            notes.append(f"indirect-injection neutralized in context: {inj.summary}")

        # PII in retrieved chunks (LLM02): mask before it can be echoed.
        if cfg.pii_enabled and cfg.pii_scan_context:
            context, findings = self._redact(context)
            summary = pii.summarize(findings)
            if summary:
                notes.append(f"PII masked in retrieved context: {summary}")

        return context, notes

    # --------------------------------------------------------- 3) output
    def filter_output(self, text: str) -> OutputResult:
        """Scrub the model's answer before it is shown / stored / traced."""
        cfg = self.config
        if not cfg.enabled or not text:
            return OutputResult(text=text)

        notes: List[str] = []
        redacted = False
        summary: Dict[str, int] = {}

        if cfg.pii_enabled and cfg.pii_redact_output:
            new_text, findings = self._redact(text)
            summary = pii.summarize(findings)
            if summary:
                redacted = True
                notes.append(f"PII redacted from answer: {summary}")
                text = new_text

        return OutputResult(text=text, redacted=redacted,
                            pii_summary=summary, notes=notes)

    # ------------------------------------------------ prompt-bound PII
    def redact_for_prompt(self, text: str) -> str:
        """Redact PII from text that is about to be sent to a model.

        When ``GUARDRAILS_PII_REDACT_PROMPTS`` is on (default), the query and
        chat history are scrubbed before any LLM call — so the planner, rewrite
        and analyst never see raw PII, and nothing raw is sent to an off-machine
        trace. Returns the text unchanged when the flag is off (the model then
        sees the user's raw input, e.g. to act on their own data)."""
        cfg = self.config
        if not (cfg.enabled and cfg.pii_enabled and cfg.pii_redact_prompts) or not text:
            return text
        scrubbed, _ = self._redact(text)
        return scrubbed

    def output_stream(self, emit: Callable[[str], None]):
        """Wrap a token callback so the live stream is PII-redacted.

        Returns an object with ``feed(token)`` / ``flush()``. Falls back to a
        transparent passthrough when output redaction is disabled."""
        cfg = self.config
        if cfg.enabled and cfg.pii_enabled and cfg.pii_redact_output:
            return StreamRedactor(self, emit)
        return _Passthrough(emit)

    # ----------------------------------------------------- off-hot-path
    def scrub_for_log(self, text: str) -> str:
        """PII-safe version of any string headed for stdout / a trace."""
        if not self.config.enabled or not self.config.pii_enabled or not text:
            return text
        scrubbed, _ = self._redact(text)
        return scrubbed

    def scan_document(self, text: str) -> Tuple[str, Dict[str, int]]:
        """At ingest: summarize PII and (optionally) redact before embedding.

        Returns ``(text_or_redacted, summary)``. When
        ``GUARDRAILS_PII_REDACT_ON_INGEST`` is false (default) the text is
        returned unchanged but the summary still records what was found, so the
        operator can see which documents carry sensitive data.
        """
        cfg = self.config
        if not cfg.enabled or not cfg.pii_enabled or not text:
            return text, {}
        findings = pii.detect(text, enabled=self._pii_enabled)
        summary = pii.summarize(findings)
        if cfg.pii_redact_on_ingest and findings:
            text, _ = self._redact(text)
        return text, summary


# Module-level singleton for the common case.
_default: Optional[Guardrails] = None


def get_guardrails() -> Guardrails:
    """Shared :class:`Guardrails` built from the current environment."""
    global _default
    if _default is None:
        _default = Guardrails()
    return _default


def reset() -> None:
    """Drop the singleton (tests, after changing env)."""
    global _default
    _default = None
