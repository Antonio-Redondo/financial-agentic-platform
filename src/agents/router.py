"""Model router — pick an Ollama model per query based on its complexity.

The policy is **data-driven**: if ``evals/results/policy.json`` exists (written by
``python -m evals.run_evals``) it overrides the environment defaults below.
Otherwise the router falls back to env vars, then to hardcoded defaults.

Environment:
  MODEL_ROUTER_ENABLED   default "true"
  ROUTER_FAST_MODEL      default "llama3.2:1b"   (simple queries)
  ROUTER_STRONG_MODEL    default "qwen2.5:3b"    (complex queries)

policy.json shape (all keys optional):
  {
    "fast_model":   "llama3.2:1b",
    "strong_model": "qwen2.5:3b",
    "route": {"simple": "llama3.2:1b", "complex": "qwen2.5:3b"},
    "rationale": "..."
  }
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Dict, Optional

_DEFAULT_FAST = "llama3.2:1b"
_DEFAULT_STRONG = "qwen2.5:3b"

# evals/results/policy.json sits two levels up from src/agents/.
_POLICY_PATH = Path(__file__).resolve().parents[2] / "evals" / "results" / "policy.json"

_policy_cache: Optional[Dict] = None
_policy_loaded = False


def _bool_env(name: str, default: bool) -> bool:
    return os.getenv(name, str(default)).strip().lower() in ("1", "true", "yes", "on")


def load_policy() -> Optional[Dict]:
    """Load (and cache) the eval-derived policy, if present."""
    global _policy_cache, _policy_loaded
    if not _policy_loaded:
        _policy_loaded = True
        try:
            _policy_cache = json.loads(_POLICY_PATH.read_text(encoding="utf-8"))
        except Exception:
            _policy_cache = None
    return _policy_cache


def router_enabled() -> bool:
    return _bool_env("MODEL_ROUTER_ENABLED", True)


def fast_model() -> str:
    policy = load_policy()
    if policy and policy.get("fast_model"):
        return policy["fast_model"]
    return os.getenv("ROUTER_FAST_MODEL", _DEFAULT_FAST)


def strong_model() -> str:
    policy = load_policy()
    if policy and policy.get("strong_model"):
        return policy["strong_model"]
    return os.getenv("ROUTER_STRONG_MODEL", _DEFAULT_STRONG)


def pick_model(complexity: str) -> str:
    """Return the model name for a query of the given complexity.

    Prefers the eval-derived route map; falls back to
    ``complex → strong, else → fast``.
    """
    complexity = (complexity or "simple").lower()
    policy = load_policy()
    if policy and isinstance(policy.get("route"), dict):
        chosen = policy["route"].get(complexity)
        if chosen:
            return chosen
    return strong_model() if complexity == "complex" else fast_model()
