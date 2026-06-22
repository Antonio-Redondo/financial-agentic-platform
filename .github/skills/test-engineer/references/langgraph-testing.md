# LangGraph Testing — Without Compiling the Graph

The compiled LangGraph (`StateGraph(...).compile()`) is a black box for
unit tests. This project deliberately keeps each node as a **bound
method** that takes an `AgentState` dict and returns a partial-state
dict — so you can call them directly with a hand-built state and assert
on the result.

## The pattern

```python
def test_planner_routes_obvious_doc_question_to_retrieve(fake_llm,
                                                         monkeypatch):
    # Make the LLM return "GENERAL SIMPLE" so we know the routing came
    # from the keyword backstop, not the classifier.
    fake_llm.responses = ["GENERAL SIMPLE"]

    graph = build_graph_under_test(planner_llm=fake_llm,
                                   document_count=5)

    out = graph.planner_node({
        "query": "summarize the uploaded resume",
        "history": [],
        "filters": {},
        "log": [],
    })

    assert out["route"] == "document"        # backstop kicked in
    assert out["complexity"] == "simple"     # classifier reply respected
    assert any("Planner" in line for line in out["log"])
```

You don't need to call `.invoke()` on the compiled graph. Each node is
testable in isolation.

## Building a graph for tests

`FinancialGraph.__init__` builds LLMs and compiles the graph. Two
testable seams:

**1. Replace `build_llm` at the module level.** The graph reads
`build_llm` from its own module, so:

```python
def make_graph(monkeypatch, planner_llm, analyst_llm=None):
    from src.agents import graph as g_mod
    monkeypatch.setattr(g_mod, "build_llm",
                        lambda **kw: planner_llm if kw.get("num_predict") == 24
                                                else (analyst_llm or planner_llm))
    vs = StubVectorStore()
    return g_mod.FinancialGraph(vs)
```

**2. Stub the VectorStore.** A thin class with the methods the graph
touches:

```python
class StubVectorStore:
    def __init__(self, chunks=()):
        self._chunks = list(chunks)

    def chunk_count(self):
        return len(self._chunks)

    def search_documents(self, query, k=6, mode="hybrid", filters=None):
        return self._chunks[:k]

    def sample_chunks(self, k=6):
        return self._chunks[:k]
```

## Testing each node

### `planner_node`

State in:
```python
{"query": str, "history": List[Dict], "filters": Dict, "log": []}
```

What to assert:
- `route` is `"document"` or `"general"` — verify both classifier path
  and keyword backstop.
- `complexity` is `"simple"` or `"complex"` — verify both classifier
  path and long-query / complexity-hint backstop.
- `search_query` is rewritten when `RETRIEVAL_REWRITE=true` and history
  exists, unchanged otherwise.

### `retrieve_node`

State in:
```python
{"query": str, "search_query": str, "filters": {}, "log": []}
```

What to assert:
- `documents` length respects `RETRIEVAL_K`.
- `context` contains the chunk text plus the `[Source N: filename | ...]`
  header.
- Empty corpus → `context == ""` and a "no documents" log line.
- Vector store exception → `documents == []`, `context == ""`, error
  log line.

### `analyst_node`

State in:
```python
{"query": str, "context": str, "complexity": "simple", ...}
```

What to assert:
- The model passed to `_analyst_for` matches `router.pick_model(...)`
  when routing is on.
- The prompt sent to the LLM contains the context delimiter
  (`=== DOCUMENT CONTENT ===`) when context is non-empty.
- Streaming path: `on_token` is called once per chunk yielded by
  `FakeLLM.stream`.

### `finalize_node`

State in:
```python
{"analysis": "the answer", "log": [...]}
```

What to assert:
- `answer == state["analysis"]`.
- Log gains a `"Finalized answer"` line.

## Compiled-graph smoke test (one only)

Keep one test that runs `.app.invoke({...})` end-to-end with all fakes
in place. This catches edge graph (`add_conditional_edges`) wiring
issues that per-node tests miss. Don't write many of these — they're
slower and noisier.

```python
def test_compiled_graph_routes_general_question_around_retrieve(...):
    out = graph.app.invoke({"query": "what is a CPR?",
                             "history": [], "filters": {}, "log": []})
    assert "documents" not in out or out.get("documents") == []
    assert out["answer"]  # analyst ran
```

## Testing `stream_run`

`stream_run` deliberately bypasses the compiled graph to keep
streaming on the main thread (Streamlit constraint). It calls the same
node methods in order. Test:

- `on_token` is called for each chunk in the stream.
- `add_metadata` is invoked with `route` / `complexity` /
  `analyst_model` (use a small recording shim for
  `observability.add_metadata`).
- The final state contains `answer`, `analyst_model`, and the full
  `log`.

## Testing the router cache

`router._policy_cache` and `_policy_loaded` are module-level. Reset
both via `monkeypatch.setattr` at the start of any test that needs a
clean load:

```python
monkeypatch.setattr("src.agents.router._policy_loaded", False)
monkeypatch.setattr("src.agents.router._policy_cache", None)
```

Otherwise the cache from a previous test leaks across cases.

## Testing the helper modules

`retrieval.rrf_fuse`, `retrieval.rerank_llm`, `retrieval.rewrite_conversational`,
`retrieval.multi_query_search` are all pure-ish and have existing
test files. New retrieval stages should follow the same pattern: pure
function in `src/agents/retrieval.py`, unit test in
`tests/unit/test_retrieval_helpers.py`, integration only if it needs a
real LLM or DB.
