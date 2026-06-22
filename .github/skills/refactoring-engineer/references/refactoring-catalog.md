# Refactoring Catalog — Python, This Codebase's Style

Canonical refactors with before/after, sized for this repo. Each entry
names the smell, shows the smallest mechanical fix, and calls out the
repo-specific catch (if any).

---

## Extract Function

**Smell:** a function has clearly separable phases marked by blank lines
or comments. Each phase doesn't fit in your head independently.

**Before:**
```python
def planner_node(self, state):
    query = state["query"]
    history = state.get("history") or []
    _emit(f"\n=== run | query: {query!r} ===")

    # phase 1: conversational rewrite
    search_query = query
    if retrieval.enabled_rewrite() and history:
        rewritten = retrieval.rewrite_conversational(query, history, self.planner_llm)
        if rewritten and rewritten.strip().lower() != query.strip().lower():
            search_query = rewritten
            _emit(f"🪄 Rewrite → {search_query!r}")

    # phase 2: classify
    prompt = (...)
    raw = self._ask(self.planner_llm, prompt).strip().upper()
    route = "document" if "DOCUMENT" in raw else "general"
    complexity = "complex" if "COMPLEX" in raw else "simple"

    # phase 3: backstops
    ...
```

**After (only if the extracted function genuinely earns its own name):**
```python
def planner_node(self, state):
    query = state["query"]
    history = state.get("history") or []
    _emit(f"\n=== run | query: {query!r} ===")

    search_query = self._maybe_rewrite(query, history)
    route, complexity = self._classify(search_query)
    route, complexity = self._apply_backstops(search_query, route, complexity)
    ...
```

**Repo catch:** If `_maybe_rewrite` has exactly one caller and is two
lines, **don't extract**. The repo's discipline rule bans helpers for
one-off operations. Extract only when (a) the phase has a name worth
saying, AND (b) it would be testable on its own, OR (c) it's a clearly
separable unit of work even with one caller.

---

## Replace Conditional with Guard Clause

**Smell:** the body of a function is wrapped in `if good_case:` with a
long block; the bad case is a one-liner at the bottom.

**Before:**
```python
def pick_model(complexity):
    complexity = (complexity or "simple").lower()
    policy = load_policy()
    if policy and isinstance(policy.get("route"), dict):
        chosen = policy["route"].get(complexity)
        if chosen:
            return chosen
    return _DEFAULT_FAST if complexity == "simple" else _DEFAULT_STRONG
```

**After:**
```python
def pick_model(complexity):
    complexity = (complexity or "simple").lower()
    policy = load_policy()
    route_map = (policy or {}).get("route") or {}
    chosen = route_map.get(complexity) if isinstance(route_map, dict) else None
    if chosen:
        return chosen
    return _DEFAULT_FAST if complexity == "simple" else _DEFAULT_STRONG
```

Flat is better than nested. The early return makes the happy path
obvious.

---

## Inline Variable

**Smell:** a variable is assigned once and used once, on the next line,
and the name doesn't add explanation.

**Before:**
```python
extension_upper = ext.upper()
icon = FILE_ICONS.get(extension_upper, "📄")
```

**After:**
```python
icon = FILE_ICONS.get(ext.upper(), "📄")
```

**Repo catch:** keep the intermediate variable when it carries
meaning that the expression alone doesn't (e.g., `safe_name = os.path.basename(...)`
in [src/ingestion/pipeline.py](../../../../src/ingestion/pipeline.py) —
the name tells the reader *what* basename is doing).

---

## Replace Magic Number / String with Named Constant

**Smell:** a number or string appears in code without explanation, and
the same value appears in 2+ places.

**Before:**
```python
results = self.vector_store.search_documents(query, k=20, ...)
...
fetch_k = int(os.getenv("RETRIEVAL_FETCH_K", "20"))
```

**After:** if 20 is the *default*, define it once:
```python
_DEFAULT_FETCH_K = 20
...
fetch_k = int(os.getenv("RETRIEVAL_FETCH_K", str(_DEFAULT_FETCH_K)))
```

**Repo catch:** numbers used in only one place (`num_predict=24` for the
planner classifier) don't need extracting — they're already documented by
the surrounding code.

---

## Remove Dead Code

**Smell:** a function has no callers, or a branch is gated on an
always-true / always-false expression.

**Procedure:**
1. Verify with the language server (`vscode_listCodeUsages`) — string
   searches miss method calls through aliases.
2. If there are zero callers across `src/`, `tests/`, and `evals/`,
   delete.
3. If callers exist only in tests, the function is being tested but
   never used in production — flag for the human to decide.

**Repo catch:** `last_ingestion` and `rescan_documents` are reachable
only through the Streamlit UI's sidebar button — string search may miss
them. Verify before deleting anything in `FinancialAgent`.

---

## Replace Repeated `os.getenv` with a Settings Read

**Smell:** the same env var is read in three places with three default
values (drift waiting to happen).

**Before:**
```python
# in graph.py
k = int(os.getenv("RETRIEVAL_K", "6"))
# in retrieval.py
k = int(os.getenv("RETRIEVAL_K", "5"))   # default drifted!
# in vector_store.py
k = int(os.getenv("RETRIEVAL_K", "6"))
```

**After:**
```python
# in retrieval.py (or a small src/agents/settings.py)
def retrieval_k() -> int:
    return int(os.getenv("RETRIEVAL_K", "6"))
```

**Repo catch:** this repo *deliberately* reads env on every call so
flags can be flipped without restarting (see `RETRIEVAL_*` knobs in
`.env`). Don't cache the result at module import — keep the function
call.

---

## Replace Comment with Better Name

**Smell:** a comment explains what a variable means; the name doesn't.

**Before:**
```python
# fetch more candidates so rerank has room to reorder
n = 20
```

**After:**
```python
fetch_k_for_rerank = 20
```

Then the comment is redundant — delete it.

---

## Collapse Trivial Wrapper

**Smell:** a function exists only to call one other function with the
same arguments.

**Before:**
```python
def get_document_stats(self) -> Dict:
    return self._stats()

def _stats(self) -> Dict:
    return self.vector_store.stats()
```

**After:**
```python
def get_document_stats(self) -> Dict:
    return self.vector_store.stats()
```

**Repo catch:** keep the wrapper when it documents a layering boundary
(e.g., `FinancialAgent.process_query` is the UI's contract with the
agent layer — even if it currently just delegates, the wrapper is the
seam).

---

## Don't-Refactor List for This Codebase

These look like smells but are load-bearing. Leave them alone.

- **`stream_run` duplicates the compiled graph's control flow.** Required
  because LangGraph runs nodes off-thread and `st.*` is main-thread-only.
  See the comment in [src/agents/graph.py](../../../../src/agents/graph.py).
- **`_emit` prints AND returns the message.** Used in both stdout
  logging and the per-turn trace expander. Splitting would force every
  call site to repeat itself.
- **`_DOCUMENT_HINTS` / `_COMPLEX_HINTS` keyword backstops.** They look
  hacky next to the LLM classifier, but they catch real classifier
  failures on small local models. Documented in the planner node.
- **`save_upload` does basename + commonpath checks.** Both checks; not
  one. They guard different attacks.
- **Env vars read on every call** (retrieval flags, mode, K). Allows
  live toggling without restart — don't cache at import.
- **`policy.json` cached at process start** in
  [src/agents/router.py](../../../../src/agents/router.py). Restart-on-change
  is documented behavior; don't "fix" it to reload.
