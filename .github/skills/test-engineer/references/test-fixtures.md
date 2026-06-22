# Test Fixtures — Repo Patterns

The project's unit-test fakes live in [tests/conftest.py](../../../../tests/conftest.py).
Use them; don't reinvent.

## `FakeLLM`

Drop-in replacement for any LangChain chat model. Records every prompt
it saw.

```python
from tests.conftest import FakeLLM

def test_planner_uses_classifier_reply():
    llm = FakeLLM(responses=["DOCUMENT COMPLEX"])
    # ... wire llm into the unit under test ...
    assert "DOCUMENT" in llm.last_prompt   # what we sent
```

### API

| Attribute / method | What it does |
|---|---|
| `FakeLLM(responses=["..."], raises=None)` | Pop replies in order; or raise once. |
| `.invoke(messages)` | Returns a `_Resp(content=...)`. |
| `.stream(messages)` | Yields one `_Resp` with the same content as `invoke`. |
| `.calls` | List of every `messages` argument seen. |
| `.last_prompt` | Text of the most recent prompt (str). |

### Common patterns

**Multi-step interaction** (planner → rerank):

```python
llm = FakeLLM(responses=[
    "DOCUMENT COMPLEX",       # planner classifier
    '[{"id": 1, "score": 8}]' # rerank reply
])
```

**Forced failure** (test the except branch):

```python
llm = FakeLLM(raises=RuntimeError("ollama down"))
```

**Streaming consumer** — `FakeLLM.stream` yields once, then stops; good
enough for testing token-callback logic without a real LLM.

## `FakeConnection` / `FakeCursor`

Stand in for a psycopg connection. Record every `execute` call.

```python
from tests.conftest import FakeConnection, FakeCursor

def test_sample_chunks_uses_random_order(monkeypatch):
    cur = FakeCursor(fetchall_value=[
        ("chunk-1", "doc1.pdf", "/tmp/doc1.pdf"),
    ])
    monkeypatch.setattr("src.agents.vector_store.get_conn",
                        lambda: FakeConnection(cur))
    vs = VectorStore()
    rows = vs.sample_chunks(k=1)
    sql, params = cur.executed[0]      # last SQL we issued
    assert "ORDER BY random()" in sql
    assert params == (1,)
    assert rows[0]["metadata"]["filename"] == "doc1.pdf"
```

### API

| Attribute | What it does |
|---|---|
| `FakeCursor(fetchone_value=..., fetchall_value=...)` | Canned return data. |
| `.executed` | `[(sql, params), ...]` — every `execute`/`executemany`. |
| `.rowcount` | Mutable int the unit under test can read. |
| Context manager (`with conn.cursor() as cur:`) | Supported. |
| `FakeConnection(cursor)` | Wraps a single cursor. Sets `.committed` on `commit()`. |

### Patching `get_conn`

The project uses a single `get_conn()` factory in
[src/storage/db.py](../../../../src/storage/db.py). Patch *there*:

```python
monkeypatch.setattr("src.storage.db.get_conn",
                    lambda: FakeConnection(cur))
```

Or patch at the import site (`src.agents.vector_store.get_conn`) when
the module re-imports.

## Environment fixture pattern

The retrieval / router code reads env on every call. Use
`monkeypatch.setenv` for the test, never the real `.env`:

```python
def test_router_prefers_policy_over_env(monkeypatch, tmp_path):
    monkeypatch.setenv("ROUTER_FAST_MODEL", "env-model")
    policy = tmp_path / "policy.json"
    policy.write_text('{"fast_model": "policy-model"}')
    monkeypatch.setattr("src.agents.router._POLICY_PATH", policy)
    monkeypatch.setattr("src.agents.router._policy_loaded", False)
    monkeypatch.setattr("src.agents.router._policy_cache", None)
    assert router.fast_model() == "policy-model"
```

Note the cache reset — `router` caches policy after first load.

## `xfail` for known bugs

Three live examples in this suite document real bugs awaiting a fix:

```python
@pytest.mark.xfail(reason="RRF dedup keys on content[:80]; distinct "
                          "chunks with shared prefix get fused.")
def test_distinct_chunks_with_same_prefix_should_stay_separate():
    ...
```

Pattern:

1. Write the test for the **correct** behavior.
2. Mark `xfail` with a one-line reason naming the bug.
3. When fixed, the test goes green and `xfail` becomes `xpassed` —
   remove the marker.

## What to **avoid**

- Don't import `langchain_ollama` in tests. The `build_llm` factory is
  the seam.
- Don't write to `evals/results/`. Use `tmp_path`.
- Don't mock `os.path` — use `tmp_path` fixtures.
- Don't rely on dict insertion order in assertions unless the test
  itself controls the order.
