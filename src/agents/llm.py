"""Shared local-LLM factory (Ollama).

Every agent node in the LangGraph workflow builds its own ChatOllama client via
this helper so the Ollama model/endpoint is configured in exactly one place.
"""
import os
from langchain_community.chat_models import ChatOllama


def build_llm(num_predict: int = 1024, temperature: float = 0.7,
              model: str = None) -> ChatOllama:
    """Create a ChatOllama client for a local model.

    Args:
        num_predict: max tokens to generate (small for routing/critique agents,
            large for the writing agent).
        temperature: sampling temperature (0.0 for deterministic routing/review).
        model: Ollama model name; defaults to $OLLAMA_MODEL (or llama3.2:1b).
    """
    return ChatOllama(
        model=model or os.getenv("OLLAMA_MODEL", "llama3.2:1b"),
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        temperature=temperature,
        top_p=0.9,
        num_predict=num_predict,
    )
