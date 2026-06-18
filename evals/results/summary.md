# Model eval summary

_Generated 2026-06-18 09:19:02 · 20 queries · judge `qwen2.5:3b` · num_predict 320_

## Overall (per model)

| Model | n | judge (1–5) | coverage | latency mean (s) | p95 (s) |
|---|---|---|---|---|---|
| `llama3.2:1b` | 20 | 2.55 | 0.667 | 63.806 | 86.58 |
| `qwen2.5:3b` | 20 | 3.15 | 0.696 | 90.831 | 135.95 |

## By complexity

| Model | complexity | judge | coverage | latency mean (s) |
|---|---|---|---|---|
| `llama3.2:1b` | simple | 2.5 | 0.767 | 64.964 |
| `llama3.2:1b` | complex | 2.6 | 0.567 | 62.647 |
| `qwen2.5:3b` | simple | 3.6 | 0.8 | 58.448 |
| `qwen2.5:3b` | complex | 2.7 | 0.592 | 123.215 |

## Derived router policy

- **fast model:** `llama3.2:1b`
- **strong model:** `qwen2.5:3b`
- **route:** simple → `qwen2.5:3b`, complex → `llama3.2:1b`
- **rationale:** simple: qwen2.5:3b (Δjudge +1.10 > 0.4); complex: llama3.2:1b (Δjudge +0.10 ≤ 0.4)
