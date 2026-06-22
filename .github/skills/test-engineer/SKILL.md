---
name: test-engineer
description: 'Write and review tests for this LangGraph + pgvector + Ollama app using the project''s established no-IO patterns. Use when adding tests for a new graph node, a retrieval helper, a router policy, an ingestion loader, or when raising coverage on existing logic. Defaults to unit tests that touch neither Ollama nor Postgres. Pairs with the test-engineer agent.'
---

# Test Engineer

Companion procedure for the [test-engineer](../../agents/test-engineer.md) agent.
The project has a strong "no real LLM / no real DB in unit tests" convention
already in [tests/conftest.py](../../../tests/conftest.py) — match those
fakes instead of inventing new ones, and you'll keep the suite fast and
deterministic.

## When to Use

- Adding a function in `src/agents/`, `src/storage/`, or `src/ingestion/`
  that has any branching logic.
- Reviewing a PR for test coverage gaps.
- Raising coverage on an existing module that has tests but misses edge
  cases.
- Reproducing a bug — write the failing test before the fix.

## Procedure

1. **Place the test correctly.**
   - Pure logic + fakes → `tests/unit/test_<thing>.py`. Runs by default.
   - Real Ollama / Postgres → `tests/integration/` with
     `@pytest.mark.integration`. Skipped by default; opt in with
     `pytest -m integration`.
2. **Reuse the existing fakes** from
   [tests/conftest.py](../../../tests/conftest.py):
   - `FakeLLM(responses=[...])` — canned `invoke` / `stream` outputs.
   - `FakeConnection` / `FakeCursor` — psycopg shape with `executed`
     log for assertions.
   - `fake_llm` fixture — autoconnected empty `FakeLLM`.
   See [references/test-fixtures.md](./references/test-fixtures.md) for
   the full menu.
3. **Test through public seams.** Prefer testing module-level helpers
   (`analyst_prompt`, `retrieval.rrf_fuse`, `router.pick_model`) over
   poking at `FinancialGraph` internals.
4. **For graph nodes**, drive the node method directly with a
   hand-built `AgentState` dict and assert on the returned partial-state
   dict. See
   [references/langgraph-testing.md](./references/langgraph-testing.md).
5. **For known bugs**, prefer an `@pytest.mark.xfail(reason=...)` test
   that documents the bug and asserts the buggy behavior — flips green
   when fixed. Three good examples already in the suite (RRF dedup,
   `_JSON_BLOCK` greedy regex, rerank score clamp).
6. **Run the affected tests** before commit:
   ```powershell
   .\.venv\Scripts\python.exe -m pytest tests/unit/test_<thing>.py -v
   ```

## Naming conventions

- `tests/unit/test_<module_under_test>.py` — one file per source module.
- `Test<Concept>` classes group related cases; pure functions can stay
  flat.
- `test_<does_what_when_given_what>` reads as a sentence.
- For bug-documenting tests, name the test after the bug and link to a
  short note in the xfail `reason`.

## What to mock vs. what to use

| Thing | Approach |
|---|---|
| LLM (`build_llm`, `ChatOllama`) | `FakeLLM` from conftest |
| pgvector / `get_conn` | `FakeConnection` + `monkeypatch` |
| `os.environ` / `.env` flags | `monkeypatch.setenv` |
| `VectorStore` (whole class) | thin subclass with stubbed `search_documents` |
| `random.random` (`sample_chunks`) | not needed — assert on returned shape, not contents |
| `time.time` | `monkeypatch.setattr` if a test depends on it; otherwise leave |
| Streamlit (`st.*`) | don't unit-test UI; if you must, mock specific calls |

## References

- [references/test-fixtures.md](./references/test-fixtures.md) — the
  `FakeLLM` / `FakeConnection` / `FakeCursor` API and patterns in this
  repo.
- [references/langgraph-testing.md](./references/langgraph-testing.md) —
  how to test the planner / retrieve / analyst nodes without compiling
  the graph.

## Anti-patterns

- **Spinning up real Ollama in unit tests.** Slow, flaky, masks logic
  bugs behind model nondeterminism. Use `FakeLLM`.
- **Patching `langchain_ollama.ChatOllama` directly.** The codebase uses
  `build_llm` as the seam — patch that, or pass the LLM in.
- **Testing prompt strings character-by-character.** Assert on the
  structural pieces (delimiters present, context block present), not the
  exact wording.
- **Hitting Postgres for round-trip tests.** Use `FakeConnection`. If
  you genuinely need Postgres semantics (`tsvector`, vector ops), write
  an integration test under `tests/integration/`.
- **Skipping the xfail dance for known bugs.** A green suite that hides
  bugs is worse than a red one that documents them.
