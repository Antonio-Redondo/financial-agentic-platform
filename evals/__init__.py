"""Offline evaluation harness for the financial analyst models.

Measures answer quality (deterministic key-point coverage + LLM-as-judge) and
latency for each candidate Ollama model, then derives the model-router policy.

Run with:  python -m evals.run_evals
Needs Ollama running; does NOT need Postgres.
"""
