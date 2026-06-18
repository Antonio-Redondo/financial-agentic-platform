"""Shared fixtures and fakes for the unit suite.

Nothing in here should touch Ollama or Postgres. Tests that need either belong
under ``tests/integration/`` and must be marked ``@pytest.mark.integration``
(skipped by default).
"""
from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

import pytest


# --------------------------------------------------------------------- FakeLLM
class FakeLLM:
    """A drop-in stand-in for ``langchain_core``'s chat models.

    Returns canned ``content`` strings (in order) for successive ``invoke``
    calls, or raises a preset exception. Records every prompt it saw so tests
    can assert on what the helper actually sent.
    """

    class _Resp:
        def __init__(self, content: str):
            self.content = content

    def __init__(
        self,
        responses: Optional[List[str]] = None,
        raises: Optional[BaseException] = None,
    ):
        self.responses = list(responses or [])
        self.raises = raises
        self.calls: List[List[Any]] = []

    def invoke(self, messages):
        self.calls.append(messages)
        if self.raises is not None:
            raise self.raises
        if not self.responses:
            return FakeLLM._Resp("")
        return FakeLLM._Resp(self.responses.pop(0))

    # Some helpers call ``llm.stream(...)`` instead of ``invoke``.
    def stream(self, messages):
        yield FakeLLM._Resp(self.invoke(messages).content)

    @property
    def last_prompt(self) -> str:
        """Convenience: text of the most recent prompt sent to the model."""
        if not self.calls:
            return ""
        msgs = self.calls[-1]
        # langchain message objects expose .content; tests can also pass strings.
        msg = msgs[0] if isinstance(msgs, list) else msgs
        return getattr(msg, "content", str(msg))


@pytest.fixture
def fake_llm():
    return FakeLLM()


# ------------------------------------------------------------- fake psycopg
class FakeCursor:
    """Records every ``execute`` call so tests can assert on SQL + params."""

    def __init__(self, fetchone_value=None, fetchall_value=None):
        self.executed: List[tuple] = []
        self._fetchone_value = fetchone_value
        self._fetchall_value = fetchall_value or []
        self.rowcount = 0

    def execute(self, sql, params=None):
        self.executed.append((sql, params))

    def executemany(self, sql, seq):
        for params in seq:
            self.executed.append((sql, params))

    def fetchone(self):
        return self._fetchone_value

    def fetchall(self):
        return list(self._fetchall_value)

    # context-manager protocol so ``with conn.cursor() as cur:`` works
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class FakeConnection:
    def __init__(self, cursor: FakeCursor):
        self._cursor = cursor
        self.committed = False
        self.closed = False

    def cursor(self):
        return self._cursor

    def commit(self):
        self.committed = True

    def close(self):
        self.closed = True

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


@pytest.fixture
def fake_cursor():
    return FakeCursor()


@pytest.fixture
def fake_conn(fake_cursor):
    return FakeConnection(fake_cursor)


# -------------------------------------------------- sample retrieval results
def _result(content: str, source_path: str = "doc.pdf",
            filename: Optional[str] = None, score: float = 0.5) -> Dict:
    return {
        "content": content,
        "metadata": {
            "source_path": source_path,
            "filename": filename or os.path.basename(source_path),
        },
        "relevance_score": score,
    }


@pytest.fixture
def make_result():
    return _result


@pytest.fixture
def sample_chunks():
    """Three distinct chunks; first 80 chars differ so RRF won't collide them."""
    return [
        _result("Alpha chunk about revenue growth in Q1.", "a.pdf", score=0.9),
        _result("Beta chunk about expenses and operating margin.", "b.pdf", score=0.7),
        _result("Gamma chunk about cash position and runway.", "c.pdf", score=0.5),
    ]


@pytest.fixture
def sample_history():
    return [
        {"role": "user", "content": "Tell me about Q1 revenue."},
        {"role": "assistant", "content": "Q1 revenue was $5M."},
        {"role": "user", "content": "What about Q2?"},
    ]


# ----------------------------------------------------- fake vector store
class FakeVectorStore:
    """Records ``search_documents`` calls and serves canned results."""

    def __init__(
        self,
        results_by_query: Optional[Dict[str, List[Dict]]] = None,
        default: Optional[List[Dict]] = None,
        raises: Optional[BaseException] = None,
        chunk_count_value: int = 100,
    ):
        self.results_by_query = dict(results_by_query or {})
        self.default = list(default or [])
        self.raises = raises
        self._chunk_count = chunk_count_value
        self.calls: List[Dict] = []

    def search_documents(self, query, k=5, mode=None, filters=None,
                         fetch_k=None):
        self.calls.append({
            "query": query, "k": k, "mode": mode,
            "filters": filters, "fetch_k": fetch_k,
        })
        if self.raises is not None:
            raise self.raises
        results = self.results_by_query.get(query, self.default)
        return [dict(r) for r in results[:k]]

    def chunk_count(self):
        return self._chunk_count


@pytest.fixture
def fake_vector_store():
    return FakeVectorStore()


# ------------------------------------------------- env reset for retrieval flags
@pytest.fixture(autouse=True)
def _retrieval_env_defaults(monkeypatch):
    """Force every test to start from a known retrieval-flag baseline."""
    for k in (
        "RETRIEVAL_REWRITE", "RETRIEVAL_MULTI_QUERY",
        "RETRIEVAL_HYDE", "RETRIEVAL_RERANK",
        "RETRIEVAL_MODE", "RETRIEVAL_K", "RETRIEVAL_FETCH_K",
    ):
        monkeypatch.delenv(k, raising=False)
    # Defaults that mirror production: rewrite on, fusion/rerank off.
    monkeypatch.setenv("RETRIEVAL_REWRITE", "true")
    monkeypatch.setenv("RETRIEVAL_MULTI_QUERY", "false")
    monkeypatch.setenv("RETRIEVAL_HYDE", "false")
    monkeypatch.setenv("RETRIEVAL_RERANK", "false")
