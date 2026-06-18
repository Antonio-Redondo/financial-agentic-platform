"""LLM-powered retrieval helpers used by the graph's retrieve step.

All helpers reuse the existing local Ollama chat model (no extra ML deps):

  * :func:`rewrite_conversational` — turn a follow-up like "what about Q2?"
    into a self-contained question using prior turns.
  * :func:`expand_queries` — generate paraphrases for multi-query retrieval.
  * :func:`hyde_query` — generate a hypothetical answer to embed instead of
    (or alongside) the original question.
  * :func:`rerank_llm` — score candidate chunks with the LLM and reorder.

Every helper is defensive: if the LLM output is malformed, the original
query / order is returned so the pipeline keeps working.
"""
from __future__ import annotations

import json
import os
import re
from typing import Callable, Dict, List, Optional

from langchain_core.messages import HumanMessage

from .vector_store import _rrf_fuse


_JSON_BLOCK = re.compile(r"\[.*\]|\{.*\}", re.DOTALL)


def _ask(llm, prompt: str) -> str:
    resp = llm.invoke([HumanMessage(content=prompt)])
    return (resp.content if hasattr(resp, "content") else str(resp)).strip()


def _extract_json(text: str):
    """Best-effort JSON extraction from an LLM response."""
    try:
        return json.loads(text)
    except Exception:
        pass
    match = _JSON_BLOCK.search(text)
    if not match:
        return None
    try:
        return json.loads(match.group(0))
    except Exception:
        return None


# --------------------------------------------------------------------- toggles
def _flag(name: str, default: bool) -> bool:
    return os.getenv(name, str(default)).lower() in ("1", "true", "yes", "on")


def enabled_rewrite() -> bool:    return _flag("RETRIEVAL_REWRITE", True)
def enabled_multi_query() -> bool: return _flag("RETRIEVAL_MULTI_QUERY", False)
def enabled_hyde() -> bool:        return _flag("RETRIEVAL_HYDE", False)
def enabled_rerank() -> bool:      return _flag("RETRIEVAL_RERANK", False)


# --------------------------------------------------------- conversational rewrite
def rewrite_conversational(query: str, history: List[Dict], llm) -> str:
    """Rewrite ``query`` into a standalone question using ``history``.

    ``history`` is a list of ``{"role": "user"|"assistant", "content": str}``
    dicts (the same shape the Streamlit UI stores). Only the last few turns
    are included so the prompt stays small.
    """
    if not history:
        return query
    recent = history[-6:]
    convo = "\n".join(f"{m['role'].upper()}: {m['content']}" for m in recent)
    prompt = (
        "Rewrite the user's latest question as a standalone search query "
        "that includes any context implied by the conversation. If the "
        "question is already standalone, return it unchanged.\n\n"
        "Respond with ONLY the rewritten question — no preamble, no quotes.\n\n"
        f"=== CONVERSATION ===\n{convo}\n\n"
        f"=== LATEST QUESTION ===\n{query}\n\n"
        "STANDALONE QUESTION:"
    )
    try:
        out = _ask(llm, prompt)
    except Exception as e:  # noqa: BLE001
        print(f"⚠️  rewrite failed: {e}", flush=True)
        return query
    # Strip surrounding quotes/markdown the model sometimes adds.
    out = out.strip().strip('"').strip("'").strip("`").strip()
    return out.splitlines()[0] if out else query


# ------------------------------------------------------------------ multi-query
def expand_queries(query: str, llm, n: int = 3) -> List[str]:
    """Generate ``n`` paraphrases of ``query`` for multi-query retrieval."""
    prompt = (
        f"Generate {n} alternative search queries that capture different "
        "phrasings or sub-topics of the user's question. Respond ONLY with a "
        "JSON array of strings, no commentary.\n\n"
        f"USER QUESTION: {query}\n\nJSON:"
    )
    try:
        raw = _ask(llm, prompt)
        parsed = _extract_json(raw) or []
        variants = [str(v).strip() for v in parsed if str(v).strip()]
    except Exception as e:  # noqa: BLE001
        print(f"⚠️  multi-query expansion failed: {e}", flush=True)
        variants = []
    # Always include the original query first.
    seen, out = set(), []
    for q in [query, *variants]:
        if q and q.lower() not in seen:
            seen.add(q.lower())
            out.append(q)
        if len(out) >= n + 1:
            break
    return out


# ------------------------------------------------------------------------- HyDE
def hyde_query(query: str, llm) -> Optional[str]:
    """Generate a hypothetical short answer to embed as a HyDE proxy.

    Returns ``None`` if the model returns nothing useful; the caller should
    fall back to the original query in that case.
    """
    prompt = (
        "Write a concise (2-4 sentence) hypothetical answer to the user's "
        "question, in the style of a financial document excerpt. Do not say "
        "you don't know — invent plausible specifics. The text will be used "
        "only as a search probe, not shown to the user.\n\n"
        f"QUESTION: {query}\n\nHYPOTHETICAL ANSWER:"
    )
    try:
        out = _ask(llm, prompt)
    except Exception as e:  # noqa: BLE001
        print(f"⚠️  HyDE failed: {e}", flush=True)
        return None
    return out or None


# -------------------------------------------------------------- multi-query fuse
def multi_query_search(query: str, vector_store, llm, k: int,
                       fetch_k: int, mode: str,
                       filters: Optional[Dict] = None) -> List[Dict]:
    """Run retrieval for several query variants and RRF-fuse the lists.

    Uses :func:`expand_queries` and (optionally) :func:`hyde_query` to widen
    coverage. The fused top-``k`` is what the graph passes to the analyst.
    """
    queries: List[str] = []
    if enabled_multi_query():
        queries.extend(expand_queries(query, llm))
    else:
        queries.append(query)

    if enabled_hyde():
        hy = hyde_query(query, llm)
        if hy:
            queries.append(hy)

    seen, deduped = set(), []
    for q in queries:
        key = q.strip().lower()
        if key and key not in seen:
            seen.add(key)
            deduped.append(q)

    result_lists: List[List[Dict]] = []
    for q in deduped:
        result_lists.append(
            vector_store.search_documents(q, k=fetch_k, mode=mode, filters=filters)
        )
    if len(result_lists) == 1:
        return result_lists[0][:k]
    return _rrf_fuse(result_lists, k=k)


# ---------------------------------------------------------------------- rerank
def rerank_llm(query: str, results: List[Dict], llm,
               top_k: int) -> List[Dict]:
    """LLM-as-cross-encoder rerank. Cheap-ish: one prompt for the whole batch.

    Asks the LLM to score each candidate 0–10 and returns the top ``top_k``
    by score. On any parse failure, the original order is preserved.
    """
    if not results:
        return results
    # Cap to a manageable batch — long prompts slow CPU inference dramatically.
    candidates = results[:20]
    blocks = []
    for i, r in enumerate(candidates):
        snippet = (r["content"] or "")[:600].replace("\n", " ")
        blocks.append(f"[{i}] {snippet}")
    joined = "\n\n".join(blocks)
    prompt = (
        "You are scoring how well each PASSAGE answers the QUESTION. "
        "Reply with ONLY a JSON array of objects "
        '`[{"id": <int>, "score": <0-10>}]`, no commentary.\n\n'
        f"QUESTION: {query}\n\nPASSAGES:\n{joined}\n\nJSON:"
    )
    try:
        raw = _ask(llm, prompt)
        parsed = _extract_json(raw)
        if not isinstance(parsed, list):
            return results[:top_k]
        scores = {int(item["id"]): float(item["score"])
                  for item in parsed
                  if isinstance(item, dict) and "id" in item and "score" in item}
    except Exception as e:  # noqa: BLE001
        print(f"⚠️  rerank failed: {e}", flush=True)
        return results[:top_k]

    scored = [
        (scores.get(i, -1.0), i, r) for i, r in enumerate(candidates)
    ]
    scored.sort(key=lambda x: x[0], reverse=True)
    reranked = []
    for score, _, r in scored:
        r = dict(r)
        r["relevance_score"] = max(0.0, score / 10.0)
        reranked.append(r)
    return reranked[:top_k]
