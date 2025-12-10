"""Embeddings adapter (development stub)

Provides a minimal pluggable interface to produce embeddings. Real providers
should be implemented behind this adapter (OpenAI, Ollama, etc.).
"""
from typing import List


def get_embedding(text: str, model: str | None = None) -> List[float]:
    """Return a mock embedding vector for development.

    Replace with a provider-specific implementation that calls OpenAI or a local model.
    """
    # simple deterministic mock: length of text split by whitespace -> small vector
    n = max(1, min(1536, len(text.split())))
    # return a tiny vector for now
    return [0.0] * 8
