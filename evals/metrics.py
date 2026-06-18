"""Metric helpers: timing, deterministic key-point coverage, aggregation."""
from __future__ import annotations

import re
import time
from statistics import mean
from typing import Callable, Dict, List, Tuple

_WS = re.compile(r"\s+")


def normalize(text: str) -> str:
    """Lowercase and collapse whitespace for substring matching."""
    return _WS.sub(" ", (text or "").lower()).strip()


def time_call(fn: Callable, *args, **kwargs) -> Tuple[object, float]:
    """Run ``fn`` and return ``(result, wall_seconds)``."""
    t0 = time.perf_counter()
    result = fn(*args, **kwargs)
    return result, time.perf_counter() - t0


def key_point_coverage(answer: str, key_points: List[str]) -> float:
    """Fraction of expected key points present in the answer (0.0–1.0).

    Each key point is matched as a normalized substring, so it tolerates phrasing
    differences. Returns 1.0 when there are no key points to check.
    """
    if not key_points:
        return 1.0
    norm = normalize(answer)
    hits = sum(1 for kp in key_points if normalize(kp) in norm)
    return hits / len(key_points)


def percentile(values: List[float], pct: float) -> float:
    """Nearest-rank percentile (pct in 0–100). Empty → 0.0."""
    if not values:
        return 0.0
    ordered = sorted(values)
    k = max(0, min(len(ordered) - 1, round(pct / 100 * (len(ordered) - 1))))
    return ordered[k]


def aggregate(rows: List[Dict], keys: List[str]) -> Dict:
    """Summarize numeric metrics over a list of per-query result rows."""
    if not rows:
        return {"n": 0}
    out: Dict[str, float] = {"n": len(rows)}
    for key in keys:
        vals = [r[key] for r in rows if isinstance(r.get(key), (int, float))]
        if vals:
            out[f"{key}_mean"] = round(mean(vals), 3)
            out[f"{key}_p50"] = round(percentile(vals, 50), 3)
            out[f"{key}_p95"] = round(percentile(vals, 95), 3)
    return out
