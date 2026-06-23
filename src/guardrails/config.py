"""Environment-driven configuration for the guardrails layer.

Every knob is read from the environment (``.env``) so the security posture can
be tuned per deployment without code changes. Defaults are chosen to be *safe
by default* for a financial app: PII is redacted from anything shown to the
user or sent off-machine, and obvious prompt-injection attempts are flagged.

Read once and cached. Call :func:`reload` in tests to pick up monkeypatched
env vars.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import List

_TRUTHY = {"1", "true", "yes", "on"}


def _bool(name: str, default: bool) -> bool:
    return os.getenv(name, str(default)).strip().lower() in _TRUTHY


def _int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except (TypeError, ValueError):
        return default


def _csv(name: str, default: str) -> List[str]:
    raw = os.getenv(name, default)
    return [item.strip() for item in raw.split(",") if item.strip()]


@dataclass(frozen=True)
class GuardrailConfig:
    """Snapshot of the active guardrail policy."""

    enabled: bool = True

    # ---- Input guards (LLM01 / LLM10) ----
    max_input_chars: int = 8_000
    # "block" → refuse the query; "flag" → annotate the trace but proceed.
    injection_action: str = "flag"

    # ---- PII (LLM02) ----
    pii_enabled: bool = True
    # Where PII is acted on. Output + logging default ON; ingestion redaction
    # defaults OFF so retrieval quality isn't silently degraded (findings are
    # still detected and recorded as metadata at ingest time).
    pii_redact_output: bool = True
    pii_redact_input: bool = True          # what gets logged/traced
    pii_redact_on_ingest: bool = False
    pii_scan_context: bool = True          # scan retrieved chunks before they hit the analyst prompt
    # Redact PII from the query (and chat history) BEFORE it reaches any model
    # call — so the planner / analyst / rewrite never see raw PII and nothing
    # raw is sent to an off-machine trace (LangSmith). On by default.
    pii_redact_prompts: bool = True
    # Hold-back window (chars) for streaming output redaction — must exceed the
    # longest possible PII match so a number split across tokens is never
    # emitted before it can be masked.
    stream_hold_chars: int = 64
    # Masking strategy: "partial" | "label" | "hash" | "remove".
    pii_strategy: str = "partial"
    # Which detectors are active. "all" enables every built-in detector.
    pii_types: List[str] = field(default_factory=lambda: ["all"])

    # ---- Output guards ----
    block_on_output_injection_echo: bool = False

    def acts_on(self, ptype: str) -> bool:
        """Whether a given PII detector name is enabled by this policy."""
        if "all" in self.pii_types:
            return True
        return ptype in self.pii_types


_cache: GuardrailConfig | None = None


def load() -> GuardrailConfig:
    """Return the cached config, building it from the environment on first use."""
    global _cache
    if _cache is None:
        _cache = GuardrailConfig(
            enabled=_bool("GUARDRAILS_ENABLED", True),
            max_input_chars=_int("GUARDRAILS_MAX_INPUT_CHARS", 8_000),
            injection_action=os.getenv("GUARDRAILS_INJECTION_ACTION", "flag").strip().lower(),
            pii_enabled=_bool("GUARDRAILS_PII_ENABLED", True),
            pii_redact_output=_bool("GUARDRAILS_PII_REDACT_OUTPUT", True),
            pii_redact_input=_bool("GUARDRAILS_PII_REDACT_INPUT", True),
            pii_redact_on_ingest=_bool("GUARDRAILS_PII_REDACT_ON_INGEST", False),
            pii_scan_context=_bool("GUARDRAILS_PII_SCAN_CONTEXT", True),
            pii_redact_prompts=_bool("GUARDRAILS_PII_REDACT_PROMPTS", True),
            stream_hold_chars=_int("GUARDRAILS_STREAM_HOLD_CHARS", 64),
            pii_strategy=os.getenv("GUARDRAILS_PII_STRATEGY", "partial").strip().lower(),
            pii_types=_csv("GUARDRAILS_PII_TYPES", "all"),
            block_on_output_injection_echo=_bool("GUARDRAILS_BLOCK_OUTPUT_INJECTION", False),
        )
    return _cache


def reload() -> GuardrailConfig:
    """Drop the cache and rebuild from the current environment (tests)."""
    global _cache
    _cache = None
    return load()
