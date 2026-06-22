# Retrieval Knobs

Every retrieval stage in this app, ordered by cost. All knobs live in
`.env` and are read on every retrieval call — no restart needed.

## Stages

```
       query
         │
         ▼
 ┌────────────────┐  (RETRIEVAL_REWRITE=true, on by default in code path
 │ conv. rewrite  │   when history exists — resolves follow-ups like
 └───────┬────────┘   "what about Q2?")
         │
         ▼
 ┌────────────────┐  (RETRIEVAL_MULTI_QUERY=true)
 │ multi-query    │   N variants → union → dedup
 └───────┬────────┘
         │
         ▼
 ┌────────────────┐  (RETRIEVAL_HYDE=true)
 │ HyDE pseudo-doc│   LLM hallucinates a plausible answer, embed THAT
 └───────┬────────┘
         │
         ▼
 ┌────────────────┐  RETRIEVAL_MODE = vector | keyword | hybrid
 │ retrieve       │   vector = dense (mxbai-embed-large)
 │ (vector_store) │   keyword = lexical (tsvector / ILIKE)
 │                │   hybrid  = RRF fuse of the two
 └───────┬────────┘
         │
         ▼
 ┌────────────────┐  (RETRIEVAL_RERANK=true) — expensive
 │ LLM rerank     │   score N candidates 0–10, keep top RETRIEVAL_K
 └───────┬────────┘
         │
         ▼
       chunks
```

## Knob reference

| Env var | Default | Cost | When to enable |
|---|---|---|---|
| `RETRIEVAL_MODE` | `hybrid` | low | `hybrid` almost always wins. `vector` if your queries are paraphrased far from the doc text. `keyword` for exact term hits (codes, IDs, jargon). |
| `RETRIEVAL_K` | `6` | free | Final chunks passed to analyst. Raise if answers feel under-grounded; lower if context bloats prompts. |
| `RETRIEVAL_FETCH_K` | `20` | free unless rerank | Candidates fetched before rerank. Only matters when `RETRIEVAL_RERANK=true`. |
| `RETRIEVAL_REWRITE` | `true` | one fast-model call | Cheap, large win on follow-ups. Turn off only if all queries are standalone. |
| `RETRIEVAL_MULTI_QUERY` | `false` | N fast-model calls | Enable for sparse / paraphrased corpora. Costs latency on every query. |
| `RETRIEVAL_HYDE` | `false` | one fast-model call | Helps when query vocab ≠ document vocab. Doesn't compose well with multi-query (redundant). |
| `RETRIEVAL_RERANK` | `false` | one strong-model call with N chunks | Biggest precision lift — and biggest latency cost. Pair with higher `FETCH_K` (e.g. 20–30). |

## Chunking

Lives in [src/agents/vector_store.py](../../../../src/agents/vector_store.py):

```python
RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)
```

- `500/100` is sized for `mxbai-embed-large` (512-token context).
- Going larger gives more context per chunk but truncates at the embedding
  boundary — silent quality loss.
- **Changing chunk size requires re-ingestion.** Existing rows aren't
  re-chunked. Drop and re-ingest, or live with the mix.

## Decision flow

1. **Below 0.6 judge baseline?** Check the corpus first — is the answer
   actually in the indexed text? Use `docker exec pgvector psql ...` to
   grep. Retrieval can't surface content that isn't indexed.
2. **Off-topic chunks coming back?** Try `RETRIEVAL_MODE=hybrid` (if you
   were on `vector`). Then `RETRIEVAL_RERANK=true` with `FETCH_K=20`.
3. **Follow-up questions misbehave?** Confirm `RETRIEVAL_REWRITE=true`.
4. **Right chunks ranked too low?** `RETRIEVAL_RERANK=true`.
5. **Query vocabulary mismatched (asks "income", doc says "revenue")?**
   `RETRIEVAL_HYDE=true` or `RETRIEVAL_MULTI_QUERY=true` (pick one).
6. **Latency budget blown?** Turn rerank off first; it's the heaviest
   stage.

## Composing stages

- `multi_query` and `HyDE` are **alternates**, not partners. Both expand
  the search space; running both wastes calls.
- `rerank` composes well with anything — it's a precision filter applied
  after recall expansion.
- `rewrite` is cheap, on by default, and orthogonal to everything else.
  Leave it on.

## Cost cheat sheet

For a single query with a small local model (rough order of magnitude):

| Config | Extra LLM calls | Added latency |
|---|---|---|
| Default (hybrid, rewrite if history) | 0–1 fast | ~0.3s |
| + multi-query (N=3) | 3 fast | ~1s |
| + HyDE | 1 fast | ~0.3s |
| + rerank | 1 strong with N chunks | 2–5s |
| All on | 4–5 calls | 4–7s |
