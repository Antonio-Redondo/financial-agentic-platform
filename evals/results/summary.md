# Model eval summary

_Generated 2026-06-24 06:15:15 · 6 queries · judge `qwen2.5:3b` · num_predict 384_

## Overall (per model)

| Model | n | judge (1–5) | coverage | latency mean (s) | p95 (s) |
|---|---|---|---|---|---|
| `llama3.2:1b` | 6 | 2.5 | 0.778 | 58.115 | 84.72 |
| `qwen2.5:3b` | 6 | 3 | 0.778 | 50.055 | 61.24 |

## By complexity

| Model | complexity | judge | coverage | latency mean (s) |
|---|---|---|---|---|
| `llama3.2:1b` | simple | 2.5 | 0.778 | 58.115 |
| `llama3.2:1b` | complex | — | — | — |
| `qwen2.5:3b` | simple | 3 | 0.778 | 50.055 |
| `qwen2.5:3b` | complex | — | — | — |

## Derived router policy

- **fast model:** `qwen2.5:3b`
- **strong model:** `llama3.2:1b`
- **route:** simple → `qwen2.5:3b`, complex → `qwen2.5:3b`
- **rationale:** simple: qwen2.5:3b (Δjudge -0.50 ≤ 0.4); complex: qwen2.5:3b (Δjudge +0.00 ≤ 0.4)
