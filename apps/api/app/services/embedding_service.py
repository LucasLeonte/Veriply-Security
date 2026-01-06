"""Embedding service for semantic vector search.

Integrates with Ollama for nomic-embed-text model to generate 768-dimensional
embeddings for queries and documents. Includes retry logic, normalization,
and truncation handling.
"""

import asyncio
import logging
import os
from typing import List
import httpx
import numpy as np

logger = logging.getLogger(__name__)

# Configuration
OLLAMA_BASE_URL = os.getenv("OLLAMA_HOST", "http://localhost:11434")
EMBEDDING_MODEL = os.getenv("EMBED_MODEL", "nomic-embed-text")
EMBEDDING_DIMENSIONS = 768
MAX_QUERY_TOKENS = 500
MAX_RETRIES = 3
RETRY_BACKOFF_BASE = 0.5  # seconds


class EmbeddingService:
    """Service for generating embeddings using Ollama nomic-embed-text model."""

    def __init__(
        self,
        ollama_url: str = OLLAMA_BASE_URL,
        model: str = EMBEDDING_MODEL,
        max_retries: int = MAX_RETRIES,
    ):
        """Initialize embedding service.

        Args:
            ollama_url: Base URL for Ollama API
            model: Name of the embedding model to use
            max_retries: Maximum number of retry attempts on failure
        """
        self.ollama_url = ollama_url.rstrip("/")
        self.model = model
        self.max_retries = max_retries
        self.client = httpx.AsyncClient(timeout=30.0)

    async def close(self):
        """Close HTTP client connection."""
        await self.client.aclose()

    async def embed_query(self, text: str) -> List[float]:
        """Generate normalized embedding vector for a query.

        Args:
            text: Query text to embed

        Returns:
            Normalized 768-dimensional embedding vector

        Raises:
            EmbeddingError: If embedding generation fails after retries
        """
        # Preprocess query
        preprocessed = self._preprocess_query(text)

        # Generate embedding with retry logic
        embedding = await self._generate_embedding_with_retry(preprocessed)

        # Normalize to unit vector for cosine similarity
        normalized = self._normalize_vector(embedding)

        return normalized

    def _preprocess_query(self, text: str) -> str:
        """Preprocess query text before embedding.

        - Truncates to MAX_QUERY_TOKENS if too long
        - Handles special characters and non-ASCII text
        - Strips extra whitespace

        Args:
            text: Raw query text

        Returns:
            Preprocessed text ready for embedding
        """
        if not text or not text.strip():
            return ""

        # Strip extra whitespace
        cleaned = " ".join(text.split())

        # Truncate if too long (rough token estimate: 1 token ≈ 4 chars)
        max_chars = MAX_QUERY_TOKENS * 4
        if len(cleaned) > max_chars:
            cleaned = cleaned[:max_chars]
            logger.warning(
                f"Query truncated from {len(text)} to {max_chars} chars "
                f"(~{MAX_QUERY_TOKENS} tokens)"
            )

        return cleaned

    async def _generate_embedding_with_retry(self, text: str) -> List[float]:
        """Generate embedding with exponential backoff retry.

        Args:
            text: Preprocessed text to embed

        Returns:
            Raw embedding vector from model

        Raises:
            EmbeddingError: If all retries fail
        """
        last_error = None

        for attempt in range(self.max_retries):
            try:
                return await self._call_ollama_api(text)
            except Exception as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    # Exponential backoff: 0.5s, 1s, 2s
                    wait_time = RETRY_BACKOFF_BASE * (2 ** attempt)
                    logger.warning(
                        f"Embedding attempt {attempt + 1}/{self.max_retries} failed: {e}. "
                        f"Retrying in {wait_time}s..."
                    )
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(
                        f"All {self.max_retries} embedding attempts failed: {e}"
                    )

        raise EmbeddingError(
            f"Failed to generate embedding after {self.max_retries} attempts: {last_error}"
        ) from last_error

    async def _call_ollama_api(self, text: str) -> List[float]:
        """Call Ollama API to generate embedding.

        Args:
            text: Text to embed

        Returns:
            Raw embedding vector

        Raises:
            httpx.HTTPError: If API call fails
        """
        # Ollama embeds endpoint uses /api/embed (not /api/embeddings)
        url = f"{self.ollama_url}/api/embed"
        payload = {"model": self.model, "input": text}

        response = await self.client.post(url, json=payload)
        response.raise_for_status()

        data = response.json()
        # Ollama /api/embed returns {"embeddings": [[...]]}
        embedding = None
        if "embedding" in data:
            embedding = data.get("embedding")
        elif "embeddings" in data and data["embeddings"]:
            embedding = data["embeddings"][0]

        if not embedding:
            raise EmbeddingError(
                f"No embedding returned from Ollama API for query: '{text[:50]}...' using model {self.model}"
            )

        if len(embedding) != EMBEDDING_DIMENSIONS:
            raise EmbeddingError(
                f"Expected {EMBEDDING_DIMENSIONS} dimensions, got {len(embedding)} for model {self.model}"
            )

        return embedding

    def _normalize_vector(self, vector: List[float]) -> List[float]:
        """Normalize vector to unit length for cosine similarity.

        Args:
            vector: Raw embedding vector

        Returns:
            Normalized vector (L2 norm = 1)
        """
        arr = np.array(vector, dtype=np.float32)
        norm = np.linalg.norm(arr)

        if norm == 0:
            logger.warning("Zero-norm vector encountered, returning original")
            return vector

        normalized = arr / norm
        return normalized.tolist()


class EmbeddingError(Exception):
    """Exception raised when embedding generation fails."""

    pass
