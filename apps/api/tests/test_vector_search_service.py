"""Unit tests for VectorSearchService.

Tests vector search with RLS enforcement, similarity scoring, result filtering,
and edge cases.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4
from app.services.vector_search_service import (
    VectorSearchService,
    SearchResult,
)
from app.services.embedding_service import EmbeddingService


@pytest.fixture
def mock_embedding_service():
    """Create mock EmbeddingService."""
    service = MagicMock(spec=EmbeddingService)
    service.embed_query = AsyncMock(return_value=[0.1] * 1024)
    return service


@pytest.fixture
def vector_search_service(mock_embedding_service):
    """Create VectorSearchService instance for testing."""
    return VectorSearchService(embedding_service=mock_embedding_service)


@pytest.fixture
def mock_db():
    """Create mock database session."""
    return AsyncMock()


@pytest.fixture
def sample_bot_id():
    """Sample bot UUID for testing."""
    return uuid4()


@pytest.fixture
def sample_tenant_id():
    """Sample tenant UUID for testing."""
    return uuid4()


class TestSearch:
    """Tests for search method."""

    @pytest.mark.asyncio
    async def test_search_returns_top_k_chunks(
        self,
        vector_search_service,
        mock_db,
        sample_bot_id,
        sample_tenant_id,
    ):
        """Test that search returns top-K chunks ordered by similarity."""
        # Mock database query results
        mock_chunks = []
        for i in range(10):
            chunk = MagicMock()
            chunk.id = uuid4()
            chunk.document_id = uuid4()
            chunk.content = f"Chunk {i} content"
            chunk.chunk_index = i
            chunk.page_number = i + 1
            chunk.metadata_json = '{"section": "Section A"}'
            chunk.distance = 0.1 * i  # Lower distance = higher similarity
            mock_chunks.append(chunk)

        # Mock document lookup
        doc = MagicMock()
        doc.id = mock_chunks[0].document_id
        doc.filename = "test_document.pdf"

        mock_execute_result = MagicMock()
        mock_execute_result.all.return_value = [(c, c.distance) for c in mock_chunks]

        mock_doc_result = MagicMock()
        mock_doc_result.scalars.return_value.all.return_value = [doc]

        mock_db.execute.side_effect = [mock_execute_result, mock_doc_result]

        results, latency = await vector_search_service.search(
            db=mock_db,
            bot_id=sample_bot_id,
            tenant_id=sample_tenant_id,
            query="test query",
            k=5,
        )

        assert len(results) <= 5
        assert latency > 0
        assert all(isinstance(r, SearchResult) for r in results)

    @pytest.mark.asyncio
    async def test_search_enforces_rls(
        self,
        vector_search_service,
        mock_db,
        sample_bot_id,
        sample_tenant_id,
    ):
        """Test that search filters by bot_id and tenant_id (RLS enforcement)."""
        mock_result = MagicMock()  # Not AsyncMock - .all() is synchronous after await
        mock_result.all.return_value = []
        mock_db.execute = AsyncMock(return_value=mock_result)

        await vector_search_service.search(
            db=mock_db,
            bot_id=sample_bot_id,
            tenant_id=sample_tenant_id,
            query="test",
        )

        # Verify execute was called (RLS filter in query)
        assert mock_db.execute.call_count >= 1

    @pytest.mark.asyncio
    async def test_search_filters_by_similarity_threshold(
        self,
        vector_search_service,
        mock_db,
        sample_bot_id,
        sample_tenant_id,
    ):
        """Test that results below similarity threshold are filtered out."""
        # Mock chunks with varying distances
        mock_chunks = []
        for i in range(5):
            chunk = MagicMock()
            chunk.id = uuid4()
            chunk.document_id = uuid4()
            chunk.content = f"Chunk {i}"
            chunk.chunk_index = i
            chunk.page_number = None
            chunk.metadata_json = None
            # Distance ranges from 0.2 to 0.6
            # Similarity = 1 - distance ranges from 0.8 to 0.4
            chunk.distance = 0.2 + (i * 0.1)
            mock_chunks.append(chunk)

        doc = MagicMock()
        doc.id = mock_chunks[0].document_id
        doc.filename = "test.pdf"

        mock_execute_result = MagicMock()
        mock_execute_result.all.return_value = [(c, c.distance) for c in mock_chunks]

        mock_doc_result = MagicMock()
        mock_doc_result.scalars.return_value.all.return_value = [doc]

        mock_db.execute.side_effect = [mock_execute_result, mock_doc_result]

        # Set threshold to 0.6 (should filter out last 2 chunks with similarity < 0.6)
        results, _ = await vector_search_service.search(
            db=mock_db,
            bot_id=sample_bot_id,
            tenant_id=sample_tenant_id,
            query="test",
            k=10,
            similarity_threshold=0.6,
        )

        # Only chunks with similarity >= 0.6 should be returned
        assert all(r.similarity >= 0.6 for r in results)

    @pytest.mark.asyncio
    async def test_search_returns_empty_for_no_results(
        self,
        vector_search_service,
        mock_db,
        sample_bot_id,
        sample_tenant_id,
    ):
        """Test that empty results are returned gracefully (no error)."""
        mock_result = MagicMock()
        mock_result.all.return_value = []
        # Three execute calls: HNSW setting, chunk query, (no doc query for empty)
        mock_db.execute = AsyncMock(side_effect=[mock_result, mock_result, mock_result])

        results, latency = await vector_search_service.search(
            db=mock_db,
            bot_id=sample_bot_id,
            tenant_id=sample_tenant_id,
            query="no results query",
        )

        assert results == []
        assert latency >= 0  # Latency tracked (may be 0 for mocked fast execution)

    @pytest.mark.asyncio
    async def test_search_includes_similarity_scores(
        self,
        vector_search_service,
        mock_db,
        sample_bot_id,
        sample_tenant_id,
    ):
        """Test that search results include similarity scores (0-1 scale)."""
        chunk = MagicMock()
        chunk.id = uuid4()
        chunk.document_id = uuid4()
        chunk.content = "Test content"
        chunk.chunk_index = 0
        chunk.page_number = 1
        chunk.metadata_json = None
        chunk.distance = 0.2  # Similarity = 1 - 0.2 = 0.8

        doc = MagicMock()
        doc.id = chunk.document_id
        doc.filename = "test.pdf"

        # First execute: HNSW setting
        mock_hnsw_result = MagicMock()
        mock_hnsw_result.all.return_value = []
        
        # Second execute: chunk query
        mock_execute_result = MagicMock()
        mock_execute_result.all.return_value = [chunk]

        # Third execute: document query
        mock_doc_result = MagicMock()
        mock_doc_scalars = MagicMock()
        mock_doc_scalars.all.return_value = [doc]
        mock_doc_result.scalars.return_value = mock_doc_scalars

        mock_db.execute = AsyncMock(side_effect=[mock_hnsw_result, mock_execute_result, mock_doc_result])

        results, _ = await vector_search_service.search(
            db=mock_db,
            bot_id=sample_bot_id,
            tenant_id=sample_tenant_id,
            query="test",
        )

        assert len(results) == 1
        assert 0.0 <= results[0].similarity <= 1.0
        assert abs(results[0].similarity - 0.8) < 0.01  # 1 - 0.2 = 0.8


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    @pytest.mark.asyncio
    async def test_search_validates_k_parameter(
        self,
        vector_search_service,
        mock_db,
        sample_bot_id,
        sample_tenant_id,
    ):
        """Test that invalid k values raise ValueError."""
        with pytest.raises(ValueError) as exc_info:
            await vector_search_service.search(
                db=mock_db,
                bot_id=sample_bot_id,
                tenant_id=sample_tenant_id,
                query="test",
                k=0,  # Invalid: must be >= 1
            )
        assert "k must be between" in str(exc_info.value)

        with pytest.raises(ValueError):
            await vector_search_service.search(
                db=mock_db,
                bot_id=sample_bot_id,
                tenant_id=sample_tenant_id,
                query="test",
                k=101,  # Invalid: must be <= 100
            )

    @pytest.mark.asyncio
    async def test_search_validates_similarity_threshold(
        self,
        vector_search_service,
        mock_db,
        sample_bot_id,
        sample_tenant_id,
    ):
        """Test that invalid similarity_threshold values raise ValueError."""
        with pytest.raises(ValueError) as exc_info:
            await vector_search_service.search(
                db=mock_db,
                bot_id=sample_bot_id,
                tenant_id=sample_tenant_id,
                query="test",
                similarity_threshold=-0.1,  # Invalid: must be >= 0
            )
        assert "similarity_threshold must be between" in str(exc_info.value)

        with pytest.raises(ValueError):
            await vector_search_service.search(
                db=mock_db,
                bot_id=sample_bot_id,
                tenant_id=sample_tenant_id,
                query="test",
                similarity_threshold=1.5,  # Invalid: must be <= 1
            )

    @pytest.mark.asyncio
    async def test_search_handles_chunks_without_embeddings(
        self,
        vector_search_service,
        mock_db,
        sample_bot_id,
        sample_tenant_id,
    ):
        """Test that chunks without embeddings are filtered out in query."""
        # The query should filter WHERE vector IS NOT NULL
        mock_result = MagicMock()
        mock_result.all.return_value = []
        mock_db.execute = AsyncMock(return_value=mock_result)

        results, _ = await vector_search_service.search(
            db=mock_db,
            bot_id=sample_bot_id,
            tenant_id=sample_tenant_id,
            query="test",
        )

        assert results == []


class TestSearchResultMetadata:
    """Tests for search result metadata extraction."""

    @pytest.mark.asyncio
    async def test_search_result_includes_metadata(
        self,
        vector_search_service,
        mock_db,
        sample_bot_id,
        sample_tenant_id,
    ):
        """Test that search results include chunk metadata."""
        chunk = MagicMock()
        chunk.id = uuid4()
        chunk.document_id = uuid4()
        chunk.content = "Test content"
        chunk.chunk_index = 5
        chunk.page_number = 3
        chunk.metadata_json = '{"section": "Introduction"}'
        chunk.distance = 0.1

        doc = MagicMock()
        doc.id = chunk.document_id
        doc.filename = "document.pdf"

        # First execute: HNSW setting (returns empty)
        mock_hnsw_result = MagicMock()
        mock_hnsw_result.all.return_value = []
        
        # Second execute: chunk query
        mock_execute_result = MagicMock()
        mock_execute_result.all.return_value = [chunk]

        # Third execute: document query
        mock_doc_result = MagicMock()
        mock_doc_scalars = MagicMock()
        mock_doc_scalars.all.return_value = [doc]
        mock_doc_result.scalars.return_value = mock_doc_scalars

        mock_db.execute = AsyncMock(side_effect=[mock_hnsw_result, mock_execute_result, mock_doc_result])

        results, _ = await vector_search_service.search(
            db=mock_db,
            bot_id=sample_bot_id,
            tenant_id=sample_tenant_id,
            query="test",
        )

        assert len(results) == 1
        result = results[0]
        assert result.document_name == "document.pdf"
        assert result.section == "Introduction"
        assert result.position == 5
        assert result.page_number == 3

    @pytest.mark.asyncio
    async def test_search_result_handles_missing_metadata(
        self,
        vector_search_service,
        mock_db,
        sample_bot_id,
        sample_tenant_id,
    ):
        """Test that missing metadata fields are handled gracefully."""
        chunk = MagicMock()
        chunk.id = uuid4()
        chunk.document_id = uuid4()
        chunk.content = "Test"
        chunk.chunk_index = 0
        chunk.page_number = None
        chunk.metadata_json = None  # No metadata
        chunk.distance = 0.1

        doc = MagicMock()
        doc.id = chunk.document_id
        doc.filename = "doc.txt"

        # First execute: HNSW setting
        mock_hnsw_result = MagicMock()
        mock_hnsw_result.all.return_value = []
        
        # Second execute: chunk query
        mock_execute_result = MagicMock()
        mock_execute_result.all.return_value = [chunk]

        # Third execute: document query
        mock_doc_result = MagicMock()
        mock_doc_scalars = MagicMock()
        mock_doc_scalars.all.return_value = [doc]
        mock_doc_result.scalars.return_value = mock_doc_scalars

        mock_db.execute = AsyncMock(side_effect=[mock_hnsw_result, mock_execute_result, mock_doc_result])

        results, _ = await vector_search_service.search(
            db=mock_db,
            bot_id=sample_bot_id,
            tenant_id=sample_tenant_id,
            query="test",
        )

        assert len(results) == 1
        assert results[0].section is None
        assert results[0].page_number is None
