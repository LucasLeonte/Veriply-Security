"""Unit tests for EmbeddingService.

Tests embedding generation, normalization, truncation, retry logic,
and error handling.
"""

import pytest
import httpx
from unittest.mock import AsyncMock, patch, MagicMock
from app.services.embedding_service import (
    EmbeddingService,
    EmbeddingError,
    EMBEDDING_DIMENSIONS,
    MAX_QUERY_TOKENS,
)


@pytest.fixture
def embedding_service():
    """Create EmbeddingService instance for testing."""
    return EmbeddingService(ollama_url="http://localhost:11434")


@pytest.fixture
def mock_embedding_response():
    """Mock successful Ollama API embedding response."""
    return {
        "embedding": [0.1] * EMBEDDING_DIMENSIONS  # 1024 dimensions
    }


class TestEmbedQuery:
    """Tests for embed_query method."""

    @pytest.mark.asyncio
    async def test_embed_query_returns_1024_dimensions(
        self, embedding_service, mock_embedding_response
    ):
        """Test that embed_query returns 1024-dimensional vector."""
        with patch.object(
            embedding_service.client, "post", new_callable=AsyncMock
        ) as mock_post:
            mock_response = MagicMock()
            mock_response.json.return_value = mock_embedding_response
            mock_response.raise_for_status = MagicMock()
            mock_post.return_value = mock_response

            result = await embedding_service.embed_query("test query")

            assert len(result) == EMBEDDING_DIMENSIONS
            assert all(isinstance(x, float) for x in result)

    @pytest.mark.asyncio
    async def test_embed_query_normalizes_vector(
        self, embedding_service, mock_embedding_response
    ):
        """Test that embedding vector is normalized to unit length."""
        with patch.object(
            embedding_service.client, "post", new_callable=AsyncMock
        ) as mock_post:
            mock_response = MagicMock()
            mock_response.json.return_value = mock_embedding_response
            mock_response.raise_for_status = MagicMock()
            mock_post.return_value = mock_response

            result = await embedding_service.embed_query("test query")

            # Check unit norm (sum of squares ≈ 1)
            import numpy as np

            norm = np.linalg.norm(result)
            assert abs(norm - 1.0) < 0.01  # Allow small floating point error

    @pytest.mark.asyncio
    async def test_embed_query_truncates_long_queries(
        self, embedding_service, mock_embedding_response
    ):
        """Test that queries >500 tokens are truncated."""
        long_query = "word " * (MAX_QUERY_TOKENS * 2)  # Exceed token limit

        with patch.object(
            embedding_service.client, "post", new_callable=AsyncMock
        ) as mock_post:
            mock_response = MagicMock()
            mock_response.json.return_value = mock_embedding_response
            mock_response.raise_for_status = MagicMock()
            mock_post.return_value = mock_response

            await embedding_service.embed_query(long_query)

            # Check that API was called with truncated text
            call_args = mock_post.call_args
            sent_query = call_args[1]["json"]["prompt"]
            max_chars = MAX_QUERY_TOKENS * 4
            assert len(sent_query) <= max_chars

    @pytest.mark.asyncio
    async def test_embed_query_handles_special_characters(
        self, embedding_service, mock_embedding_response
    ):
        """Test that special characters and non-ASCII text are handled."""
        special_query = "Café! @#$% 中文 日本語"

        with patch.object(
            embedding_service.client, "post", new_callable=AsyncMock
        ) as mock_post:
            mock_response = MagicMock()
            mock_response.json.return_value = mock_embedding_response
            mock_response.raise_for_status = MagicMock()
            mock_post.return_value = mock_response

            result = await embedding_service.embed_query(special_query)

            assert len(result) == EMBEDDING_DIMENSIONS
            # Verify API was called with original text
            call_args = mock_post.call_args
            assert special_query in call_args[1]["json"]["prompt"]

    @pytest.mark.asyncio
    async def test_embed_query_handles_short_queries(
        self, embedding_service, mock_embedding_response
    ):
        """Test that very short queries (1-2 words) produce valid embeddings."""
        short_query = "refund"

        with patch.object(
            embedding_service.client, "post", new_callable=AsyncMock
        ) as mock_post:
            mock_response = MagicMock()
            mock_response.json.return_value = mock_embedding_response
            mock_response.raise_for_status = MagicMock()
            mock_post.return_value = mock_response

            result = await embedding_service.embed_query(short_query)

            assert len(result) == EMBEDDING_DIMENSIONS


class TestRetryLogic:
    """Tests for retry logic with exponential backoff."""

    @pytest.mark.asyncio
    async def test_retry_on_failure_succeeds_on_second_attempt(
        self, embedding_service, mock_embedding_response
    ):
        """Test that retry logic works and succeeds on second attempt."""
        with patch.object(
            embedding_service.client, "post", new_callable=AsyncMock
        ) as mock_post:
            # First call fails, second succeeds
            mock_response_success = MagicMock()
            mock_response_success.json.return_value = mock_embedding_response
            mock_response_success.raise_for_status = MagicMock()

            mock_post.side_effect = [
                httpx.HTTPError("Connection failed"),
                mock_response_success,
            ]

            result = await embedding_service.embed_query("test")

            assert len(result) == EMBEDDING_DIMENSIONS
            assert mock_post.call_count == 2

    @pytest.mark.asyncio
    async def test_retry_fails_after_max_attempts(self, embedding_service):
        """Test that EmbeddingError is raised after max retries."""
        with patch.object(
            embedding_service.client, "post", new_callable=AsyncMock
        ) as mock_post:
            mock_post.side_effect = httpx.HTTPError("Connection failed")

            with pytest.raises(EmbeddingError) as exc_info:
                await embedding_service.embed_query("test")

            assert "Failed to generate embedding" in str(exc_info.value)
            assert mock_post.call_count == embedding_service.max_retries


class TestErrorHandling:
    """Tests for error handling edge cases."""

    @pytest.mark.asyncio
    async def test_missing_embedding_in_response(self, embedding_service):
        """Test that EmbeddingError is raised when API returns no embedding."""
        with patch.object(
            embedding_service.client, "post", new_callable=AsyncMock
        ) as mock_post:
            mock_response = MagicMock()
            mock_response.json.return_value = {}  # No embedding field
            mock_response.raise_for_status = MagicMock()
            mock_post.return_value = mock_response

            with pytest.raises(EmbeddingError) as exc_info:
                await embedding_service.embed_query("test")

            assert "No embedding returned" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_wrong_dimension_count(self, embedding_service):
        """Test that EmbeddingError is raised for wrong dimension count."""
        with patch.object(
            embedding_service.client, "post", new_callable=AsyncMock
        ) as mock_post:
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "embedding": [0.1] * 512  # Wrong dimensions (512 instead of 1024)
            }
            mock_response.raise_for_status = MagicMock()
            mock_post.return_value = mock_response

            with pytest.raises(EmbeddingError) as exc_info:
                await embedding_service.embed_query("test")

            assert "Expected 1024 dimensions" in str(exc_info.value)


class TestPreprocessing:
    """Tests for query preprocessing."""

    def test_preprocess_strips_whitespace(self, embedding_service):
        """Test that extra whitespace is stripped."""
        result = embedding_service._preprocess_query("  test   query  ")
        assert result == "test query"

    def test_preprocess_handles_empty_query(self, embedding_service):
        """Test that empty queries return empty string."""
        result = embedding_service._preprocess_query("")
        assert result == ""

        result = embedding_service._preprocess_query("   ")
        assert result == ""
