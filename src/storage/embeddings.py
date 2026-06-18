"""Shared local embedding factory (Ollama).

Mirrors `agents.llm` so embedding configuration lives in exactly one place.
The chosen model must be pulled in Ollama first, e.g.:

    ollama pull mxbai-embed-large
"""
from __future__ import annotations

import os
from functools import lru_cache

from langchain_community.embeddings import OllamaEmbeddings


@lru_cache(maxsize=4)
def get_embedder(model: str | None = None) -> OllamaEmbeddings:
    """Return a cached OllamaEmbeddings client for `model` (or $EMBEDDING_MODEL)."""
    return OllamaEmbeddings(
        model=model or os.getenv("EMBEDDING_MODEL", "mxbai-embed-large"),
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
    )


def embed_query(text: str) -> list[float]:
    return get_embedder().embed_query(text)


def embed_documents(texts: list[str]) -> list[list[float]]:
    return get_embedder().embed_documents(texts)
