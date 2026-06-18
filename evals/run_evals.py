"""Run the model evals and derive the router policy.

    python -m evals.run_evals                      # default fast vs strong
    python -m evals.run_evals --models llama3.2:1b,qwen2.5:3b --judge qwen2.5:3b
    python -m evals.run_evals --limit 6            # quick smoke run

Needs Ollama running. Does NOT need Postgres (uses the analyst prompt directly).
Writes results + summary + policy.json under evals/results/.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from statistics import mean
from typing import Dict, List

# Make the project root importable so we reuse the app's real analyst prompt.
_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.agents.llm import build_llm                     # noqa: E402
from src.agents.graph import analyst_prompt              # noqa: E402
from evals.dataset import DATASET                        # noqa: E402
from evals import metrics                                # noqa: E402
from evals.judge import judge_answer                     # noqa: E402

_DEFAULT_MODELS = ["llama3.2:1b", "qwen2.5:3b"]
_RESULTS_DIR = _ROOT / "evals" / "results"
_COMPLEXITIES = ["simple", "complex"]


def generate(model_llm, query: str) -> str:
    from langchain_core.messages import HumanMessage
    resp = model_llm.invoke([HumanMessage(content=analyst_prompt(query))])
    return resp.content if hasattr(resp, "content") else str(resp)


def run_model(model: str, dataset: List[Dict], judge_llm, num_predict: int) -> List[Dict]:
    """Generate + grade every query for one model. Returns per-query rows."""
    print(f"\n=== Evaluating model: {model} ===", flush=True)
    model_llm = build_llm(num_predict=num_predict, temperature=0.7, model=model)
    rows: List[Dict] = []
    for i, item in enumerate(dataset, 1):
        try:
            answer, latency = metrics.time_call(generate, model_llm, item["query"])
            error = None
        except Exception as e:  # noqa: BLE001
            answer, latency, error = "", 0.0, str(e)
            print(f"   ⚠️ generation error on {item['id']}: {e}", flush=True)

        coverage = metrics.key_point_coverage(answer, item["key_points"])
        score = judge_answer(item["query"], answer, item["key_points"], judge_llm)
        rows.append({
            "id": item["id"],
            "category": item["category"],
            "complexity": item["complexity"],
            "model": model,
            "latency_s": round(latency, 2),
            "coverage": round(coverage, 3),
            "judge": score,
            "answer_chars": len(answer),
            "error": error,
        })
        print(f"   [{i:>2}/{len(dataset)}] {item['id']:<24} "
              f"judge={score} cov={coverage:.2f} {latency:5.1f}s", flush=True)
    return rows


def summarize(rows: List[Dict], model: str, complexity: str = None) -> Dict:
    sub = [r for r in rows if r["model"] == model
           and (complexity is None or r["complexity"] == complexity)]
    agg = metrics.aggregate(sub, ["judge", "coverage", "latency_s"])
    return agg


def derive_policy(rows: List[Dict], models: List[str], tolerance: float) -> Dict:
    """Pick fast/strong models from the data and a per-complexity route.

    fast   = lowest mean latency; strong = highest mean judge.
    For each complexity, choose the fast model unless the strong model's judge
    advantage exceeds ``tolerance`` (on the 1–5 scale).
    """
    def mean_metric(model, metric, complexity=None):
        sub = [r[metric] for r in rows if r["model"] == model
               and (complexity is None or r["complexity"] == complexity)
               and isinstance(r.get(metric), (int, float))]
        return mean(sub) if sub else 0.0

    fast = min(models, key=lambda m: mean_metric(m, "latency_s"))
    strong = max(models, key=lambda m: mean_metric(m, "judge"))
    if strong == fast and len(models) > 1:
        # Latency-fastest is also quality-best → still expose a distinct strong.
        strong = max((m for m in models if m != fast),
                     key=lambda m: mean_metric(m, "judge"))

    route, notes = {}, []
    for cx in _COMPLEXITIES:
        jf, js = mean_metric(fast, "judge", cx), mean_metric(strong, "judge", cx)
        if fast == strong or (js - jf) <= tolerance:
            route[cx] = fast
            notes.append(f"{cx}: {fast} (Δjudge {js - jf:+.2f} ≤ {tolerance})")
        else:
            route[cx] = strong
            notes.append(f"{cx}: {strong} (Δjudge {js - jf:+.2f} > {tolerance})")

    return {
        "fast_model": fast,
        "strong_model": strong,
        "route": route,
        "quality_tolerance": tolerance,
        "rationale": "; ".join(notes),
        "source": "evals.run_evals",
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    }


def write_summary_md(path: Path, rows: List[Dict], models: List[str],
                     policy: Dict, config: Dict) -> None:
    lines = ["# Model eval summary", "",
             f"_Generated {policy['generated_at']} · "
             f"{config['queries']} queries · judge `{config['judge']}` · "
             f"num_predict {config['num_predict']}_", "",
             "## Overall (per model)", "",
             "| Model | n | judge (1–5) | coverage | latency mean (s) | p95 (s) |",
             "|---|---|---|---|---|---|"]
    for m in models:
        a = summarize(rows, m)
        lines.append(
            f"| `{m}` | {a.get('n', 0)} | {a.get('judge_mean', '—')} | "
            f"{a.get('coverage_mean', '—')} | {a.get('latency_s_mean', '—')} | "
            f"{a.get('latency_s_p95', '—')} |")

    lines += ["", "## By complexity", "",
              "| Model | complexity | judge | coverage | latency mean (s) |",
              "|---|---|---|---|---|"]
    for m in models:
        for cx in _COMPLEXITIES:
            a = summarize(rows, m, cx)
            lines.append(
                f"| `{m}` | {cx} | {a.get('judge_mean', '—')} | "
                f"{a.get('coverage_mean', '—')} | {a.get('latency_s_mean', '—')} |")

    lines += ["", "## Derived router policy", "",
              f"- **fast model:** `{policy['fast_model']}`",
              f"- **strong model:** `{policy['strong_model']}`",
              f"- **route:** simple → `{policy['route']['simple']}`, "
              f"complex → `{policy['route']['complex']}`",
              f"- **rationale:** {policy['rationale']}", ""]
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser(description="Run model evals + derive router policy.")
    ap.add_argument("--models", default=",".join(_DEFAULT_MODELS),
                    help="Comma-separated Ollama model names to compare.")
    ap.add_argument("--judge", default=None,
                    help="Judge model (default: the last/strongest --models entry).")
    ap.add_argument("--num-predict", type=int, default=384,
                    help="Max answer tokens per generation (bounds runtime).")
    ap.add_argument("--limit", type=int, default=0,
                    help="Evaluate only the first N queries (0 = all).")
    ap.add_argument("--quality-tolerance", type=float, default=0.4,
                    help="Max judge gain (1–5 scale) before preferring the strong model.")
    args = ap.parse_args()

    models = [m.strip() for m in args.models.split(",") if m.strip()]
    judge_model = args.judge or models[-1]
    dataset = DATASET[: args.limit] if args.limit else DATASET

    print(f"Models: {models} | judge: {judge_model} | queries: {len(dataset)} | "
          f"num_predict: {args.num_predict}", flush=True)
    judge_llm = build_llm(num_predict=8, temperature=0.0, model=judge_model)

    all_rows: List[Dict] = []
    for m in models:
        all_rows.extend(run_model(m, dataset, judge_llm, args.num_predict))

    policy = derive_policy(all_rows, models, args.quality_tolerance)
    config = {"models": models, "judge": judge_model, "queries": len(dataset),
              "num_predict": args.num_predict}

    _RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    ts = time.strftime("%Y%m%d-%H%M%S")
    per_model = {m: {"overall": summarize(all_rows, m),
                     **{cx: summarize(all_rows, m, cx) for cx in _COMPLEXITIES}}
                 for m in models}

    (_RESULTS_DIR / f"results_{ts}.json").write_text(
        json.dumps({"config": config, "policy": policy,
                    "per_model": per_model, "rows": all_rows}, indent=2),
        encoding="utf-8")
    (_RESULTS_DIR / "policy.json").write_text(json.dumps(policy, indent=2),
                                              encoding="utf-8")
    write_summary_md(_RESULTS_DIR / "summary.md", all_rows, models, policy, config)

    # ---- stdout summary ----
    print("\n================ SUMMARY ================", flush=True)
    for m in models:
        a = summarize(all_rows, m)
        print(f"{m:<16} judge={a.get('judge_mean','—')}  "
              f"cov={a.get('coverage_mean','—')}  "
              f"latency={a.get('latency_s_mean','—')}s", flush=True)
    print(f"\nPolicy → fast={policy['fast_model']}  strong={policy['strong_model']}")
    print(f"  route: simple→{policy['route']['simple']}  "
          f"complex→{policy['route']['complex']}")
    print(f"  {policy['rationale']}")
    print(f"\nWrote: {_RESULTS_DIR / 'policy.json'}  +  summary.md  +  results_{ts}.json")


if __name__ == "__main__":
    main()
