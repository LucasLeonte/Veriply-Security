"""Vector search service for semantic document chunk retrieval.

Performs pgvector cosine similarity search with RLS enforcement for multi-tenant
bot isolation. Integrates with EmbeddingService for query embedding.
"""

import logging
import time
from typing import List, Optional
from uuid import UUID
from dataclasses import dataclass

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chunk import Chunk
from app.models.document import Document
from app.services.embedding_service import EmbeddingService, EmbeddingError

logger = logging.getLogger(__name__)

# Default search parameters
DEFAULT_TOP_K = 5
DEFAULT_SIMILARITY_THRESHOLD = 0.5
HNSW_EF_SEARCH = 40  # Runtime parameter for HNSW index


@dataclass
class SearchResult:
    """Search result containing chunk data and similarity score."""

    chunk_id: str
    document_id: str
    document_name: str
    section: Optional[str]
    text: str
    similarity: float
    position: int
    page_number: Optional[int] = None


class VectorSearchService:
    """Service for semantic vector search with RLS enforcement."""

    def __init__(self, embedding_service: EmbeddingService):
        """Initialize vector search service.

        Args:
            embedding_service: Service for generating query embeddings
        """
        self.embedding_service = embedding_service

    async def search(
        self,
        db: AsyncSession,
        bot_id: UUID,
        tenant_id: UUID,
        query: str,
        k: int = DEFAULT_TOP_K,
        similarity_threshold: float = DEFAULT_SIMILARITY_THRESHOLD,
    ) -> tuple[List[SearchResult], int]:
        """Perform semantic vector search with RLS enforcement.

        Args:
            db: Database session
            bot_id: Bot ID for RLS filtering
            tenant_id: Tenant ID for RLS filtering
            query: Search query text
            k: Number of top results to return
            similarity_threshold: Minimum similarity score (0-1)

        Returns:
            Tuple of (search results, latency in milliseconds)

        Raises:
            EmbeddingError: If query embedding fails
            ValueError: If parameters are invalid
        """
        start_time = time.time()

        # Validate parameters
        if k < 1 or k > 100:
            raise ValueError("k must be between 1 and 100")
        if similarity_threshold < 0 or similarity_threshold > 1:
            raise ValueError("similarity_threshold must be between 0 and 1")

        # Generate query embedding
        try:
            query_embedding = await self.embedding_service.embed_query(query)
        except EmbeddingError as e:
            logger.error(f"Failed to embed query: {e}")
            raise

        # Set HNSW search parameter for this session
        await db.execute(text(f"SET hnsw.ef_search = {HNSW_EF_SEARCH}"))

        # Perform vector search with RLS filtering
        # Use pgvector's cosine distance operator (<=>)
        # Lower distance = higher similarity
        stmt = (
            select(
                Chunk.id,
                Chunk.document_id,
                Chunk.content,
                Chunk.chunk_index,
                Chunk.page_number,
                Chunk.metadata_json,
                Chunk.vector.cosine_distance(query_embedding).label("distance"),
            )
            .where(Chunk.bot_id == bot_id)
            .where(Chunk.tenant_id == tenant_id)
            .where(Chunk.vector.isnot(None))  # Only chunks with embeddings
            .order_by(text("distance"))
            .limit(k * 2)  # Get extra results for threshold filtering
        )

        result = await db.execute(stmt)
        rows = result.all()

        # Convert distance to similarity and filter by threshold
        # Cosine similarity = 1 - cosine distance
        results = []
        for row in rows:
            similarity = 1.0 - row.distance
            if similarity >= similarity_threshold:
                results.append((row, similarity))
            if len(results) >= k:
                break

        # Fetch document names for results
        if results:
            document_ids = [row[0].document_id for row in results]
            doc_stmt = select(Document).where(Document.id.in_(document_ids))
            doc_result = await db.execute(doc_stmt)
            documents = {doc.id: doc for doc in doc_result.scalars().all()}
        else:
            documents = {}

        # Build search results
        search_results = []
        for row, similarity in results:
            chunk = row
            doc = documents.get(chunk.document_id)
            document_name = doc.filename if doc else "Unknown"

            # Extract section from metadata if available
            section = None
            if chunk.metadata_json:
                try:
                    import json

                    metadata = json.loads(chunk.metadata_json)
                    section = metadata.get("section")
                except (json.JSONDecodeError, AttributeError):
                    pass

            search_results.append(
                SearchResult(
                    chunk_id=str(chunk.id),
                    document_id=str(chunk.document_id),
                    document_name=document_name,
                    section=section,
                    text=chunk.content,
                    similarity=round(similarity, 4),
                    position=chunk.chunk_index,
                    page_number=chunk.page_number,
                )
            )

        latency_ms = int((time.time() - start_time) * 1000)
        logger.info(
            f"Vector search completed: query='{query[:50]}...', "
            f"bot_id={bot_id}, results={len(search_results)}, latency={latency_ms}ms"
        )

        return search_results, latency_ms


class VectorSearchError(Exception):
    """Exception raised when vector search fails."""

    pass
