"""LLM-as-judge — rate an analyst answer 1–5 on correctness and relevance.

Deliberately strict and terse so a small local model can act as judge. The
deterministic key-point coverage in :mod:`evals.metrics` anchors this noisier
signal.
"""
from __future__ import annotations

import re
from typing import List

from langchain_core.messages import HumanMessage

_DIGIT = re.compile(r"[1-5]")


def build_judge_prompt(query: str, answer: str, key_points: List[str]) -> str:
    points = "\n".join(f"- {kp}" for kp in key_points) or "- (none provided)"
    return (
        "You are a strict grader of a financial analyst's answer. Rate the answer "
        "on a scale of 1 to 5 for CORRECTNESS and RELEVANCE to the question:\n"
        "  5 = fully correct, directly answers, no errors\n"
        "  4 = mostly correct and relevant, minor gaps\n"
        "  3 = partially correct or incomplete\n"
        "  2 = largely wrong or off-topic\n"
        "  1 = incorrect, irrelevant, or empty\n\n"
        f"QUESTION:\n{query}\n\n"
        f"POINTS A GOOD ANSWER SHOULD COVER:\n{points}\n\n"
        f"ANSWER TO GRADE:\n{answer}\n\n"
        "Reply with ONLY a single integer from 1 to 5. No words."
    )


def judge_answer(query: str, answer: str, key_points: List[str], judge_llm) -> int:
    """Return an integer score 1–5 (3 on parse failure / empty answer)."""
    if not (answer or "").strip():
        return 1
    prompt = build_judge_prompt(query, answer, key_points)
    try:
        resp = judge_llm.invoke([HumanMessage(content=prompt)])
        text = resp.content if hasattr(resp, "content") else str(resp)
    except Exception as e:  # judge failure shouldn't abort the whole run
        print(f"   ⚠️ judge error: {e}", flush=True)
        return 3
    m = _DIGIT.search(text or "")
    return int(m.group()) if m else 3
