"""Semantic response cache for the financial agent.

Generating an answer is the most expensive step in a query (a full LLM
completion on CPU). When the same — or a very similar — question is asked
again, this cache returns the previously generated answer instead of
re-running the graph.

How it works
------------
* **Exact hits** are O(1): the normalized query text is looked up in a dict
  (no embedding call needed).
* **Semantic hits** embed the query (same local Ollama model used for
  retrieval) and return the cached answer of the most similar prior query when
  cosine similarity ≥ ``RESPONSE_CACHE_THRESHOLD``.
* Entries are scoped to a **namespace** (model + corpus signature). When the
  indexed corpus changes (chunk count moves) or the active model changes, old
  answers no longer match — so the cache self-invalidates on the changes that
  would make a cached answer wrong.
* Bounded **LRU** with optional **TTL**. Thread-safe (Streamlit reruns on
  worker threads).

The threshold defaults high (0.97) on purpose: in finance, "CPR for pool A"
and "CPR for pool B" embed very closely, and returning the wrong pool's answer
is worse than a cache miss. Tune via ``RESPONSE_CACHE_THRESHOLD``.
"""
from __future__ import annotations

import os
import threading
import time
from collections import OrderedDict
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional

import numpy as np

_TRUTHY = {"1", "true", "yes", "on"}


def enabled() -> bool:
    return os.getenv("RESPONSE_CACHE_ENABLED", "true").strip().lower() in _TRUTHY


def _threshold() -> float:
    try:
        return float(os.getenv("RESPONSE_CACHE_THRESHOLD", "0.97"))
    except ValueError:
        return 0.97


def _max_size() -> int:
    try:
        return int(os.getenv("RESPONSE_CACHE_MAX", "256"))
    except ValueError:
        return 256


def _ttl() -> float:
    """Seconds before an entry expires. 0 (default) = never expire."""
    try:
        return float(os.getenv("RESPONSE_CACHE_TTL", "0"))
    except ValueError:
        return 0.0


def _normalize(text: str) -> str:
    return " ".join((text or "").lower().split())


@dataclass
class CacheEntry:
    query: str
    answer: str
    payload: Dict          # full process_query result (trace, route, model, …)
    namespace: str
    embedding: Optional[np.ndarray] = None
    created_at: float = field(default_factory=time.time)


@dataclass
class CacheStats:
    hits_exact: int = 0
    hits_semantic: int = 0
    misses: int = 0
    stores: int = 0
    evictions: int = 0

    @property
    def hits(self) -> int:
        return self.hits_exact + self.hits_semantic

    @property
    def lookups(self) -> int:
        return self.hits + self.misses

    @property
    def hit_rate(self) -> float:
        return self.hits / self.lookups if self.lookups else 0.0


class SemanticResponseCache:
    """Bounded, namespaced, embedding-keyed answer cache."""

    def __init__(self, embed_fn: Optional[Callable[[str], List[float]]] = None):
        # Injected so tests can avoid Ollama; defaults to the real embedder.
        self._embed_fn = embed_fn
        self._lock = threading.RLock()
        # key: (namespace, normalized_query) -> CacheEntry. OrderedDict = LRU.
        self._store: "OrderedDict[tuple, CacheEntry]" = OrderedDict()
        self.stats = CacheStats()

    # ------------------------------------------------------------- internals
    def _embed(self, text: str) -> Optional[np.ndarray]:
        fn = self._embed_fn
        if fn is None:
            # Imported lazily so importing this module doesn't pull storage/db.
            from ..storage.embeddings import embed_query
            fn = embed_query
        try:
            vec = np.asarray(fn(text), dtype=np.float32)
            norm = np.linalg.norm(vec)
            return vec / norm if norm else None
        except Exception as e:  # noqa: BLE001 — cache must never break a query
            print(f"⚠️  response-cache embed failed: {e}", flush=True)
            return None

    def _expired(self, entry: CacheEntry) -> bool:
        ttl = _ttl()
        return ttl > 0 and (time.time() - entry.created_at) > ttl

    def _evict_if_needed(self) -> None:
        cap = _max_size()
        while len(self._store) > cap:
            self._store.popitem(last=False)  # drop least-recently-used
            self.stats.evictions += 1

    # ------------------------------------------------------------------- API
    def get(self, query: str, namespace: str) -> Optional[Dict]:
        """Return a cached payload for ``query`` in ``namespace`` or ``None``."""
        if not enabled() or not query.strip():
            return None

        norm = _normalize(query)
        with self._lock:
            # 1) Exact match — no embedding cost.
            exact = self._store.get((namespace, norm))
            if exact is not None and not self._expired(exact):
                self._store.move_to_end((namespace, norm))
                self.stats.hits_exact += 1
                return self._as_hit(exact, similarity=1.0, kind="exact")

            # Snapshot candidate entries in this namespace for similarity scan.
            candidates = [
                (key, e) for key, e in self._store.items()
                if e.namespace == namespace and e.embedding is not None
                and not self._expired(e)
            ]

        # 2) Semantic match (embedding done outside the lock — it's the slow bit).
        if not candidates:
            with self._lock:
                self.stats.misses += 1
            return None

        q_vec = self._embed(query)
        if q_vec is None:
            with self._lock:
                self.stats.misses += 1
            return None

        best_key, best_sim = None, -1.0
        for key, e in candidates:
            sim = float(np.dot(q_vec, e.embedding))  # both unit-normalized
            if sim > best_sim:
                best_key, best_sim = key, sim

        with self._lock:
            if best_key is not None and best_sim >= _threshold():
                entry = self._store.get(best_key)
                if entry is not None and not self._expired(entry):
                    self._store.move_to_end(best_key)
                    self.stats.hits_semantic += 1
                    return self._as_hit(entry, similarity=best_sim, kind="semantic")
            self.stats.misses += 1
        return None

    def put(self, query: str, payload: Dict, namespace: str) -> None:
        """Store ``payload`` (a process_query result) for ``query``."""
        if not enabled() or not query.strip():
            return
        answer = (payload or {}).get("output", "")
        if not answer:
            return
        embedding = self._embed(query)  # may be None → still cached for exact hits
        norm = _normalize(query)
        with self._lock:
            self._store[(namespace, norm)] = CacheEntry(
                query=query, answer=answer, payload=dict(payload),
                namespace=namespace, embedding=embedding,
            )
            self._store.move_to_end((namespace, norm))
            self.stats.stores += 1
            self._evict_if_needed()

    def clear(self) -> None:
        """Drop all entries (e.g. after ingesting new documents)."""
        with self._lock:
            self._store.clear()

    def size(self) -> int:
        with self._lock:
            return len(self._store)

    # ------------------------------------------------------------- helpers
    @staticmethod
    def _as_hit(entry: CacheEntry, similarity: float, kind: str) -> Dict:
        payload = dict(entry.payload)
        payload["cached"] = True
        payload["cache_similarity"] = round(similarity, 4)
        payload["cache_kind"] = kind
        return payload


# Process-wide singleton (shared across Streamlit sessions in the same process).
_default: Optional[SemanticResponseCache] = None
_default_lock = threading.Lock()


def get_cache() -> SemanticResponseCache:
    global _default
    if _default is None:
        with _default_lock:
            if _default is None:
                _default = SemanticResponseCache()
    return _default


def reset() -> None:
    """Drop the singleton (tests)."""
    global _default
    with _default_lock:
        _default = None
