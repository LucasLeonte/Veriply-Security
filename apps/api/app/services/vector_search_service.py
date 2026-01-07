"""Vector search service for semantic document chunk retrieval.

Performs pgvector cosine similarity search with RLS enforcement for multi-tenant
bot isolation. Integrates with EmbeddingService for query embedding.
Also searches verified Q&A entries for human-approved answers (prioritized).
"""

import logging
import time
from typing import List, Optional
from uuid import UUID
from dataclasses import dataclass

from sqlalchemy import select, text, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chunk import Chunk
from app.models.document import Document
from app.models.bot import Bot
from app.models.bot_document_access import BotDocumentAccess
from app.services.embedding_service import EmbeddingService, EmbeddingError

logger = logging.getLogger(__name__)

# Default search parameters
DEFAULT_TOP_K = 5
DEFAULT_SIMILARITY_THRESHOLD = 0.5
VERIFIED_QA_SIMILARITY_THRESHOLD = 0.6  # Threshold for verified answers (lower than 0.7 to improve recall)
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
    is_verified: bool = False
    verified_answer: Optional[str] = None  # The approved answer if from verified_qa


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

        # Resolve the bot's group for access filtering
        bot = await db.scalar(select(Bot).where(Bot.id == bot_id, Bot.tenant_id == tenant_id))
        if not bot or not bot.group_id:
            logger.info(f"Bot {bot_id} has no group assigned; returning no results")
            return [], int((time.time() - start_time) * 1000)
        group_id_val = bot.group_id

        # ============================================================
        # STEP 1: Search verified Q&A for human-approved answers first
        # ============================================================
        verified_results: List[SearchResult] = []
        try:
            from app.services.verified_qa import search_verified_qa
            
            logger.debug(
                f"Searching verified Q&A: tenant={tenant_id}, group={group_id_val}, "
                f"bot={bot_id}, threshold={VERIFIED_QA_SIMILARITY_THRESHOLD}"
            )
            
            verified_qa_matches = await search_verified_qa(
                db=db,
                tenant_id=tenant_id,
                group_id=group_id_val,
                bot_id=bot_id,
                query_embedding=query_embedding,
                k=k,
                similarity_threshold=VERIFIED_QA_SIMILARITY_THRESHOLD,
            )
            
            logger.debug(f"Verified Q&A search returned {len(verified_qa_matches)} matches")
            
            for verified_qa, similarity in verified_qa_matches:
                # Create SearchResult from verified Q&A
                verified_results.append(
                    SearchResult(
                        chunk_id=f"verified_qa_{verified_qa.id}",
                        document_id=str(verified_qa.id),
                        document_name=f"Verified Q&A: {verified_qa.question_text[:50]}...",
                        section="Verified Knowledge Base",
                        text=verified_qa.question_text,
                        similarity=similarity,
                        position=0,
                        page_number=None,
                        is_verified=True,
                        verified_answer=verified_qa.answer_text,
                    )
                )
            
            if verified_results:
                logger.info(
                    f"Found {len(verified_results)} verified Q&A match(es) for query '{query[:50]}...'"
                )
            else:
                logger.debug(f"No verified Q&A matches found for query '{query[:50]}...'")
        except Exception as e:
            logger.warning(f"Verified Q&A search failed, continuing with document search: {e}", exc_info=True)

        # ============================================================
        # STEP 2: Search document chunks (standard RAG)
        # ============================================================
        
        # Determine document IDs this bot can access using allowlist rules
        # Access logic:
        #  - Explicit document records with is_allowed=true are allowed
        #  - Folder-level is_allowed=true allows all docs in that folder
        #  - Explicit document records with is_allowed=false override folder allow
        # Note: we keep this in-SQL for performance rather than per-row Python checks

        # Subquery: documents explicitly allowed
        allowed_docs_explicit = (
            select(BotDocumentAccess.document_id)
            .where(
                and_(
                    BotDocumentAccess.bot_id == bot_id,
                    BotDocumentAccess.tenant_id == tenant_id,
                    BotDocumentAccess.group_id == group_id_val,
                    BotDocumentAccess.document_id.isnot(None),
                    BotDocumentAccess.is_allowed.is_(True),
                )
            )
        )

        # Subquery: documents allowed via folder allow
        allowed_docs_via_folder = (
            select(Document.id)
            .join(
                BotDocumentAccess,
                and_(
                    BotDocumentAccess.folder_id == Document.folder_id,
                    BotDocumentAccess.bot_id == bot_id,
                    BotDocumentAccess.tenant_id == tenant_id,
                    BotDocumentAccess.group_id == Document.group_id,
                    BotDocumentAccess.is_allowed.is_(True),
                ),
            )
            .where(
                and_(
                    Document.tenant_id == tenant_id,
                    Document.group_id == group_id_val,
                    Document.deleted_at.is_(None),
                )
            )
        )

        # Subquery: documents explicitly denied (to subtract)
        denied_docs_explicit = (
            select(BotDocumentAccess.document_id)
            .where(
                and_(
                    BotDocumentAccess.bot_id == bot_id,
                    BotDocumentAccess.tenant_id == tenant_id,
                    BotDocumentAccess.group_id == group_id_val,
                    BotDocumentAccess.document_id.isnot(None),
                    BotDocumentAccess.is_allowed.is_(False),
                )
            )
        )

        # Final filter condition for accessible documents
        accessible_docs_condition = or_(
            Chunk.document_id.in_(allowed_docs_explicit),
            Chunk.document_id.in_(allowed_docs_via_folder),
        )

        # Perform vector search with RLS filtering and bot allowlist
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
            .where(Chunk.tenant_id == tenant_id)
            .where(Chunk.vector.isnot(None))  # Only chunks with embeddings
            .where(accessible_docs_condition)
            .where(~Chunk.document_id.in_(denied_docs_explicit))
            .order_by(text("distance"))
            .limit(k * 2)  # Get extra results for threshold filtering
        )

        result = await db.execute(stmt)
        rows = result.all()

        # Convert distance to similarity and filter by threshold
        # Cosine similarity = 1 - cosine distance
        chunk_results = []
        for row in rows:
            similarity = 1.0 - row.distance
            if similarity >= similarity_threshold:
                chunk_results.append((row, similarity))
            if len(chunk_results) >= k:
                break

        # Fetch document names for results
        if chunk_results:
            document_ids = [row[0].document_id for row in chunk_results]
            doc_stmt = select(Document).where(Document.id.in_(document_ids))
            doc_result = await db.execute(doc_stmt)
            documents = {doc.id: doc for doc in doc_result.scalars().all()}
        else:
            documents = {}

        # Build search results from document chunks
        document_search_results = []
        for row, similarity in chunk_results:
            chunk = row
            doc = documents.get(chunk.document_id)
            document_name = doc.filename if doc else "Unknown"

            # Extract section from metadata if available
            section = None
            is_verified = False
            if chunk.metadata_json:
                try:
                    import json

                    metadata = json.loads(chunk.metadata_json)
                    section = metadata.get("section")
                    is_verified = bool(metadata.get("verified") or metadata.get("is_verified"))
                except (json.JSONDecodeError, AttributeError):
                    pass

            document_search_results.append(
                SearchResult(
                    chunk_id=str(chunk.id),
                    document_id=str(chunk.document_id),
                    document_name=document_name,
                    section=section,
                    text=chunk.content,
                    similarity=round(similarity, 4),
                    position=chunk.chunk_index,
                    page_number=chunk.page_number,
                    is_verified=is_verified,
                )
            )

        # ============================================================
        # STEP 3: Merge results - verified Q&A takes priority
        # ============================================================
        # If we have verified Q&A matches, they go first (they're human-approved)
        # Then fill remaining slots with document chunk results
        
        search_results = []
        
        # Add verified results first (they're prioritized)
        for vr in verified_results:
            if len(search_results) < k:
                search_results.append(vr)
        
        # Fill remaining slots with document results
        for dr in document_search_results:
            if len(search_results) < k:
                search_results.append(dr)

        latency_ms = int((time.time() - start_time) * 1000)
        verified_count = len([r for r in search_results if r.is_verified])
        logger.info(
            f"Vector search completed: query='{query[:50]}...', "
            f"bot_id={bot_id}, results={len(search_results)} "
            f"(verified={verified_count}), latency={latency_ms}ms"
        )

        return search_results, latency_ms


class VectorSearchError(Exception):
    """Exception raised when vector search fails."""

    pass
