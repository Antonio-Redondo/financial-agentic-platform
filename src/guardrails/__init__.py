"""Guardrails layer for the financial agentic platform.

A small, dependency-free security layer that sits at the three I/O boundaries
of the multi-agent graph:

  * **Input**  — validate user queries (length, prompt-injection) and scrub PII
    from anything that gets logged or traced.
  * **Context** — neutralize indirect prompt-injection in retrieved documents
    and mask PII before it reaches the analyst prompt.
  * **Output** — redact PII (SSN, bank account, card, routing, email, …) from
    the model's answer before it is shown, stored, or sent off-machine.

Threat model and mapping to OWASP LLM Top 10 live in
``.github/skills/security-auditor/references/owasp-llm-top-10.md``. Configuration
is environment-driven — see :mod:`src.guardrails.config` and ``.env.example``.

Typical use::

    from src.guardrails import get_guardrails
    g = get_guardrails()
    decision = g.check_input(user_query)
    if not decision.allowed:
        return decision.reason
    clean_context, _ = g.sanitize_context(retrieved_context)
    safe = g.filter_output(model_answer).text
"""
from .config import GuardrailConfig, load as load_config, reload as reload_config
from .guard import (
    Guardrails,
    InputDecision,
    OutputResult,
    StreamRedactor,
    get_guardrails,
    reset,
)
from . import pii, injection

__all__ = [
    "Guardrails",
    "InputDecision",
    "OutputResult",
    "StreamRedactor",
    "GuardrailConfig",
    "get_guardrails",
    "reset",
    "load_config",
    "reload_config",
    "pii",
    "injection",
]
