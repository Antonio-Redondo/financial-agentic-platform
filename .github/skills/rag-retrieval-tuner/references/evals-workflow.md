# Evals Workflow

How the local eval harness works, and how to read its output.

## Running

```powershell
# Quick smoke (6 queries, ~1–2 min depending on models)
.\.venv\Scripts\python.exe -m evals.run_evals --limit 6

# Full run (all queries in evals/dataset.py)
.\.venv\Scripts\python.exe -m evals.run_evals

# Pin specific models / judge
.\.venv\Scripts\python.exe -m evals.run_evals --models llama3.2:1b,qwen2.5:3b --judge qwen2.5:3b
```

Needs Ollama running. Does **not** need Postgres — the harness uses the
real `analyst_prompt` directly so retrieval-stage tuning that lives in
`graph.py` retrieve-node is out of scope for this harness. (To eval
retrieval changes end-to-end, use the Streamlit app with sample queries
and inspect the `🧠 Reasoning trace` expander.)

## Output files

```
evals/results/
├── results_<UTC>.json   # per-query rows: judge, coverage, latency, error
├── summary.md           # human-readable aggregate per model × complexity
└── policy.json          # router config: fast_model / strong_model / route
```

`results_*.json` is timestamped — keep history to spot regressions over
time. `summary.md` and `policy.json` are overwritten on every run.

## Reading per-query rows

Each row has:

| Field | Meaning |
|---|---|
| `id` | query id from `evals/dataset.py` |
| `category` | e.g. `prepayment`, `risk`, `general` |
| `complexity` | `simple` or `complex` — used for routing |
| `model` | which model generated the answer |
| `latency_s` | wall-clock generation time |
| `coverage` | fraction of `key_points` substrings present in the answer (0–1) |
| `judge` | LLM-as-judge score 1–5 (see `evals/judge.py`) |
| `error` | non-empty if generation failed |

## Reading `summary.md`

The harness aggregates by `(model, complexity)`. The key numbers per
bucket: `mean(judge)`, `mean(coverage)`, `mean(latency_s)`.

What a real win looks like:

- **Judge +0.5 or more** at equal or lower latency — clear win, keep it.
- **Judge ±0.2 with materially lower latency** — keep it (within
  `quality_tolerance` budget set in `policy.json`).
- **Coverage up, judge down** — model is parroting key points without
  reasoning. Reject.
- **One bucket up, the other down** — the change is differential; you may
  want it for one complexity tier only (route around it via `policy.json`).

## `policy.json` shape

```json
{
  "fast_model":   "llama3.2:1b",
  "strong_model": "qwen2.5:3b",
  "route": { "simple": "qwen2.5:3b", "complex": "llama3.2:1b" },
  "quality_tolerance": 0.4,
  "rationale": "...",
  "source": "evals.run_evals",
  "generated_at": "..."
}
```

The router in [src/agents/router.py](../../../../src/agents/router.py)
prefers `route[complexity]` if present, then `fast_model`/`strong_model`,
then env vars (`ROUTER_FAST_MODEL` / `ROUTER_STRONG_MODEL`), then code
defaults.

**Gotcha:** the router caches `policy.json` at process start. Restart
Streamlit after every harness run.

## Diagnosing a regression

1. Diff the new `results_*.json` against the previous one — find the
   queries whose `judge` or `coverage` dropped.
2. Look at the `error` field. A handful of timeouts can move the mean.
3. Reproduce one regressing query in the UI with the same model.
4. Open the reasoning trace and check which stage is wrong:
   - Bad route → planner; retrieval was skipped or kicked in wrongly.
   - Right route, no chunks → retriever; check chunk count, embedding
     mismatch, or filters.
   - Right chunks, wrong answer → analyst; prompt or model issue.

## Adding a query

Edit `evals/dataset.py`. Each entry is:

```python
{
    "id": "prepay-001",
    "category": "prepayment",
    "complexity": "complex",
    "query": "Compare CPR between Q1 and Q2 of 2025.",
    "key_points": ["CPR", "Q1", "Q2", "2025"],
}
```

`key_points` drives the coverage metric — keep them short, factual,
substring-matchable.
