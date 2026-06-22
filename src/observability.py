"""LangSmith tracing wiring.

Tracing is driven entirely by the ``LANGSMITH_*`` block in ``.env``: set
``LANGSMITH_TRACING=true`` plus ``LANGSMITH_API_KEY`` and every LangChain /
LangGraph call (planner, retriever, analyst, embeddings) is captured
automatically — LangChain's callback system does the work, no code change
required. This module adds three conveniences on top:

  * ``traceable``    — re-exported decorator that groups a function's child LLM
    calls under one named run. A cheap pass-through when tracing is disabled,
    so it is safe to leave applied permanently.
  * ``add_metadata`` — tag the active run (route, model, …) so traces are
    filterable in the LangSmith UI. A no-op when no run is active.
  * ``configure``    — log once at startup whether traces are really uploading.

LangSmith is a hosted service (smith.langchain.com), so it is the one part of
this otherwise local-only app that sends data off the machine. It stays OFF
unless explicitly enabled in ``.env``.
"""
from __future__ import annotations

import os

from langsmith import traceable  # noqa: F401 — re-exported for callers
from langsmith.run_helpers import get_current_run_tree

_TRUTHY = {"1", "true", "yes", "on"}


def tracing_enabled() -> bool:
    """Whether LangSmith tracing is switched on via the environment."""
    return os.getenv("LANGSMITH_TRACING", "").strip().lower() in _TRUTHY


def add_metadata(**fields) -> None:
    """Attach metadata to the currently-active LangSmith run, if any.

    Silently does nothing when tracing is off (no run on the stack), so callers
    can sprinkle it in hot paths without guarding.
    """
    run = get_current_run_tree()
    if run is not None:
        run.add_metadata({k: v for k, v in fields.items() if v is not None})


def configure() -> None:
    """Emit a one-line startup status. Makes no network calls when disabled."""
    if not tracing_enabled():
        return
    project = os.getenv("LANGSMITH_PROJECT", "default")
    if os.getenv("LANGSMITH_API_KEY"):
        print(f"🔭 LangSmith tracing ON → project {project!r}", flush=True)
    else:
        print(
            "⚠️  LANGSMITH_TRACING=true but LANGSMITH_API_KEY is unset; "
            "runs will not upload. Add your key to .env.",
            flush=True,
        )
