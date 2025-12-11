"""Integration tests for semantic vector search.

Tests end-to-end search flow including document upload, processing,
embedding generation, and vector search with RLS enforcement.
"""

import pytest
from httpx import AsyncClient
from uuid import uuid4, UUID
from app.main import app
from app.core.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.integration
@pytest.mark.asyncio
class TestSearchIntegration:
    """Integration tests for POST /api/bots/{bot_id}/search."""

    async def test_search_returns_relevant_chunks(
        self,
        client: AsyncClient,
        authenticated_headers: dict,
        bot_id: UUID,
        tenant_id: UUID,
        db: AsyncSession,
    ):
        """Test E2E: upload doc → process → embed → search → verify results."""
        # This test requires:
        # 1. Document processing pipeline (Story 2.4) to be working
        # 2. Ollama service running with nomic-embed-text model
        # 3. pgvector extension enabled in database

        # Upload a test document
        upload_response = await client.post(
            f"/api/bots/{bot_id}/documents",
            headers=authenticated_headers,
            files={
                "file": ("test_policy.txt", b"Refund policy: 30-day money back guarantee")
            },
        )
        assert upload_response.status_code == 201
        document_id = upload_response.json()["id"]

        # Wait for document processing to complete (in real env, use polling)
        # For now, assume processing completes synchronously or via background job

        # Perform search
        search_response = await client.post(
            f"/api/bots/{bot_id}/search",
            headers=authenticated_headers,
            json={
                "query": "What is the refund policy?",
                "k": 5,
                "similarity_threshold": 0.5,
            },
        )

        assert search_response.status_code == 200
        data = search_response.json()

        assert "query" in data
        assert "results" in data
        assert "search_latency_ms" in data
        assert data["query"] == "What is the refund policy?"
        assert len(data["results"]) > 0

        # Verify result structure
        result = data["results"][0]
        assert "chunk_id" in result
        assert "document_id" in result
        assert "document_name" in result
        assert "text" in result
        assert "similarity" in result
        assert 0.0 <= result["similarity"] <= 1.0

        # Verify search latency is within target (<200ms)
        assert data["search_latency_ms"] < 200

    async def test_search_enforces_rls_isolation(
        self,
        client: AsyncClient,
        authenticated_headers: dict,
        bot_a_id: UUID,
        bot_b_id: UUID,
        tenant_id: UUID,
    ):
        """Test RLS: search bot A only returns bot A chunks (never bot B)."""
        # Upload document to bot A
        upload_a = await client.post(
            f"/api/bots/{bot_a_id}/documents",
            headers=authenticated_headers,
            files={"file": ("doc_a.txt", b"Bot A content about pricing")},
        )
        assert upload_a.status_code == 201

        # Upload document to bot B
        upload_b = await client.post(
            f"/api/bots/{bot_b_id}/documents",
            headers=authenticated_headers,
            files={"file": ("doc_b.txt", b"Bot B content about shipping")},
        )
        assert upload_b.status_code == 201

        # Wait for processing...

        # Search bot A for "pricing"
        search_a = await client.post(
            f"/api/bots/{bot_a_id}/search",
            headers=authenticated_headers,
            json={"query": "pricing", "k": 10},
        )
        assert search_a.status_code == 200
        results_a = search_a.json()["results"]

        # Verify all results belong to bot A documents
        doc_a_id = upload_a.json()["id"]
        doc_b_id = upload_b.json()["id"]
        for result in results_a:
            assert result["document_id"] != doc_b_id
            # Should only see bot A documents

        # Search bot B for "shipping"
        search_b = await client.post(
            f"/api/bots/{bot_b_id}/search",
            headers=authenticated_headers,
            json={"query": "shipping", "k": 10},
        )
        assert search_b.status_code == 200
        results_b = search_b.json()["results"]

        # Verify all results belong to bot B documents
        for result in results_b:
            assert result["document_id"] != doc_a_id

    async def test_search_with_no_results(
        self,
        client: AsyncClient,
        authenticated_headers: dict,
        bot_id: UUID,
    ):
        """Test search with query that has no relevant chunks returns empty array."""
        # Search for gibberish query with no matching chunks
        response = await client.post(
            f"/api/bots/{bot_id}/search",
            headers=authenticated_headers,
            json={
                "query": "xyz123 complete gibberish nonsense query",
                "k": 5,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["results"] == []  # Empty results, no error

    async def test_search_latency_under_200ms(
        self,
        client: AsyncClient,
        authenticated_headers: dict,
        bot_with_1000_chunks: UUID,
    ):
        """Test search latency <200ms p95 with 1000 chunks."""
        # Run 10 concurrent searches and measure p95 latency
        import asyncio

        async def run_search():
            response = await client.post(
                f"/api/bots/{bot_with_1000_chunks}/search",
                headers=authenticated_headers,
                json={"query": "test query", "k": 5},
            )
            return response.json()["search_latency_ms"]

        latencies = await asyncio.gather(*[run_search() for _ in range(10)])

        # Calculate p95 latency
        sorted_latencies = sorted(latencies)
        p95_index = int(len(sorted_latencies) * 0.95)
        p95_latency = sorted_latencies[p95_index]

        assert p95_latency < 200, f"p95 latency {p95_latency}ms exceeds 200ms target"

    async def test_search_invalid_bot_id(
        self,
        client: AsyncClient,
        authenticated_headers: dict,
    ):
        """Test search with invalid bot_id returns 404."""
        invalid_bot_id = uuid4()
        response = await client.post(
            f"/api/bots/{invalid_bot_id}/search",
            headers=authenticated_headers,
            json={"query": "test"},
        )

        assert response.status_code == 404

    async def test_search_unauthenticated(self, client: AsyncClient, bot_id: UUID):
        """Test search without authentication returns 401."""
        response = await client.post(
            f"/api/bots/{bot_id}/search",
            json={"query": "test"},
        )

        assert response.status_code == 401

    async def test_search_validates_request_parameters(
        self,
        client: AsyncClient,
        authenticated_headers: dict,
        bot_id: UUID,
    ):
        """Test search validates k and similarity_threshold parameters."""
        # Invalid k (too large)
        response = await client.post(
            f"/api/bots/{bot_id}/search",
            headers=authenticated_headers,
            json={"query": "test", "k": 101},
        )
        assert response.status_code == 422  # Validation error

        # Invalid similarity_threshold (negative)
        response = await client.post(
            f"/api/bots/{bot_id}/search",
            headers=authenticated_headers,
            json={"query": "test", "similarity_threshold": -0.5},
        )
        assert response.status_code == 422

    async def test_search_handles_special_characters(
        self,
        client: AsyncClient,
        authenticated_headers: dict,
        bot_id: UUID,
    ):
        """Test search handles special characters and non-ASCII text correctly."""
        response = await client.post(
            f"/api/bots/{bot_id}/search",
            headers=authenticated_headers,
            json={"query": "Café! @#$% 中文 日本語", "k": 5},
        )

        assert response.status_code == 200
        data = response.json()
        assert "results" in data

    async def test_search_deterministic_results(
        self,
        client: AsyncClient,
        authenticated_headers: dict,
        bot_id: UUID,
    ):
        """Test identical queries return identical results (deterministic)."""
        query = "test refund policy"

        # Run search twice
        response1 = await client.post(
            f"/api/bots/{bot_id}/search",
            headers=authenticated_headers,
            json={"query": query, "k": 5},
        )
        response2 = await client.post(
            f"/api/bots/{bot_id}/search",
            headers=authenticated_headers,
            json={"query": query, "k": 5},
        )

        assert response1.status_code == 200
        assert response2.status_code == 200

        results1 = response1.json()["results"]
        results2 = response2.json()["results"]

        # Verify same number of results
        assert len(results1) == len(results2)

        # Verify chunk IDs match in same order
        chunk_ids_1 = [r["chunk_id"] for r in results1]
        chunk_ids_2 = [r["chunk_id"] for r in results2]
        assert chunk_ids_1 == chunk_ids_2

        # Verify similarity scores match
        similarities_1 = [r["similarity"] for r in results1]
        similarities_2 = [r["similarity"] for r in results2]
        assert similarities_1 == similarities_2


@pytest.mark.integration
@pytest.mark.asyncio
class TestSearchPerformance:
    """Performance tests for vector search."""

    async def test_large_knowledge_base_performance(
        self,
        client: AsyncClient,
        authenticated_headers: dict,
        bot_with_10000_chunks: UUID,
    ):
        """Test search performance with large knowledge base (10K chunks)."""
        response = await client.post(
            f"/api/bots/{bot_with_10000_chunks}/search",
            headers=authenticated_headers,
            json={"query": "common term search", "k": 5},
        )

        assert response.status_code == 200
        data = response.json()

        # Verify top 5 results returned
        assert len(data["results"]) <= 5

        # Verify similarity scores are correct
        similarities = [r["similarity"] for r in data["results"]]
        assert similarities == sorted(similarities, reverse=True)  # Descending order

        # Performance should still be acceptable
        assert data["search_latency_ms"] < 500  # More lenient for large KB


# Fixtures for integration tests


@pytest.fixture
async def bot_id(client: AsyncClient, authenticated_headers: dict) -> UUID:
    """Create a test bot and return its ID."""
    response = await client.post(
        "/api/bots",
        headers=authenticated_headers,
        json={"name": "Test Search Bot", "description": "Bot for search tests"},
    )
    return UUID(response.json()["id"])


@pytest.fixture
async def bot_a_id(client: AsyncClient, authenticated_headers: dict) -> UUID:
    """Create bot A for RLS testing."""
    response = await client.post(
        "/api/bots",
        headers=authenticated_headers,
        json={"name": "Bot A", "description": "First bot"},
    )
    return UUID(response.json()["id"])


@pytest.fixture
async def bot_b_id(client: AsyncClient, authenticated_headers: dict) -> UUID:
    """Create bot B for RLS testing."""
    response = await client.post(
        "/api/bots",
        headers=authenticated_headers,
        json={"name": "Bot B", "description": "Second bot"},
    )
    return UUID(response.json()["id"])


@pytest.fixture
async def bot_with_1000_chunks(
    client: AsyncClient, authenticated_headers: dict, db: AsyncSession
) -> UUID:
    """Create a bot with 1000 chunks for performance testing."""
    # Implementation would seed database with 1000 chunks
    # For now, return placeholder
    pass


@pytest.fixture
async def bot_with_10000_chunks(
    client: AsyncClient, authenticated_headers: dict, db: AsyncSession
) -> UUID:
    """Create a bot with 10,000 chunks for large KB testing."""
    # Implementation would seed database with 10K chunks
    pass
