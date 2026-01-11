"""Vector search service for semantic document chunk retrieval.

Performs pgvector cosine similarity search with RLS enforcement for multi-tenant
bot isolation. Integrates with EmbeddingService for query embedding.

Story 7.2: Implements two-stage retrieval with verified KB priority. When a high-
confidence match (>= 0.95 similarity) is found in verified_qa, the answer is
returned immediately WITHOUT invoking LLM generation or document retrieval.
"""

import logging
import time
from typing import List, Optional, Tuple
from uuid import UUID
from dataclasses import dataclass

from sqlalchemy import select, text, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chunk import Chunk
from app.models.document import Document
from app.models.bot import Bot
from app.models.bot_document_access import BotDocumentAccess
from app.services.embedding_service import EmbeddingService, EmbeddingError
from app.core.settings import settings

logger = logging.getLogger(__name__)

# Default search parameters
DEFAULT_TOP_K = 5
DEFAULT_SIMILARITY_THRESHOLD = 0.70
# Story 7.2: Configurable threshold for verified KB (default 0.95)
VERIFIED_KB_SIMILARITY_THRESHOLD = settings.VERIFIED_KB_SIMILARITY_THRESHOLD
HNSW_EF_SEARCH = 40  # Runtime parameter for HNSW index


class _TTLCache:
    """Simple in-process TTL cache with a max size.

    Note: This is per-process and best-effort only. Suitable as an optional
    optimization for hot verified questions; correctness does not depend on it.
    """

    def __init__(self, max_size: int = 100):
        self._store: dict[str, Tuple[float, object]] = {}
        self._max_size = max_size

    def get(self, key: str) -> Optional[object]:
        entry = self._store.get(key)
        if not entry:
            return None
        expires_at, value = entry
        now = time.time()
        if now >= expires_at:
            # Expired
            self._store.pop(key, None)
            return None
        return value

    def set(self, key: str, value: object, ttl_seconds: int) -> None:
        if ttl_seconds <= 0:
            return
        # Simple eviction when exceeding size; remove oldest-ish by arbitrary pop
        if len(self._store) >= self._max_size:
            try:
                self._store.pop(next(iter(self._store)))
            except StopIteration:
                pass
        expires_at = time.time() + ttl_seconds
        self._store[key] = (expires_at, value)

    def clear(self) -> None:
        self._store.clear()


_verified_kb_cache = _TTLCache(max_size=200)


def _make_verified_cache_key(
    *, tenant_id: UUID, group_id: UUID, bot_id: UUID, query: str, k: int, threshold: float
) -> str:
    import hashlib

    qnorm = (query or "").strip().lower()
    qhash = hashlib.sha1(qnorm.encode("utf-8")).hexdigest()
    return f"veriq:ten:{tenant_id}:grp:{group_id}:bot:{bot_id}:k:{k}:thr:{threshold:.3f}:q:{qhash}"


@dataclass
class SearchResult:
    """Search result containing chunk data and similarity score.
    
    Story 7.2: Extended with verified KB metadata for provenance tracking.
    """

    chunk_id: str
    document_id: str
    document_name: str
    section: Optional[str]
    text: str
    similarity: float
    position: int
    page_number: Optional[int] = None
    # Story 7.2: Verified KB fields
    is_verified: bool = False
    verified_answer: Optional[str] = None  # The approved answer if from verified_qa
    verified_id: Optional[UUID] = None  # VerifiedQA entry ID for provenance
    verified_citations: Optional[dict] = None  # Source citations from verified entry


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
        verified_only: bool = False,
    ) -> tuple[List[SearchResult], int]:
        """Perform semantic vector search with RLS enforcement.
        
        Story 7.2: Implements two-stage retrieval with verified KB short-circuit.
        When a high-confidence verified match (>= threshold) exists, returns immediately
        WITHOUT performing document search, reducing latency and ensuring consistency.

        Args:
            db: Database session
            bot_id: Bot ID for RLS filtering
            tenant_id: Tenant ID for RLS filtering
            query: Search query text
            k: Number of top results to return
            similarity_threshold: Minimum similarity score for document chunks (0-1)
            verified_only: If True, only search verified KB (skip document search)

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
        # STEP 1: Search verified Q&A FIRST (Story 7.2)
        # ============================================================
        verified_results: List[SearchResult] = []
        verified_latency_ms = 0
        try:
            from app.services.verified_qa import search_verified_qa
            
            verified_start = time.time()
            logger.debug(
                f"[Story 7.2] Searching verified KB: tenant={tenant_id}, group={group_id_val}, "
                f"bot={bot_id}, threshold={VERIFIED_KB_SIMILARITY_THRESHOLD}"
            )

            # Optional cache: return hot verified results quickly
            cache_enabled = bool(getattr(settings, "VERIFIED_KB_CACHE_ENABLED", False))
            cache_ttl = int(getattr(settings, "VERIFIED_KB_CACHE_TTL_SECONDS", 0))
            cache_key = _make_verified_cache_key(
                tenant_id=tenant_id,
                group_id=group_id_val,
                bot_id=bot_id,
                query=query,
                k=k,
                threshold=VERIFIED_KB_SIMILARITY_THRESHOLD,
            )
            if cache_enabled:
                cached_payload = _verified_kb_cache.get(cache_key)
                if cached_payload:
                    logger.info("[Story 7.2] VERIFIED_KB_CACHE_HIT: using cached verified results")
                    # Rehydrate SearchResult objects
                    for item in cached_payload:
                        verified_results.append(
                            SearchResult(
                                chunk_id=item["chunk_id"],
                                document_id=item["document_id"],
                                document_name=item["document_name"],
                                section=item.get("section"),
                                text=item["text"],
                                similarity=item["similarity"],
                                position=item["position"],
                                page_number=item.get("page_number"),
                                is_verified=True,
                                verified_answer=item.get("verified_answer"),
                                verified_id=item.get("verified_id"),
                                verified_citations=item.get("verified_citations"),
                            )
                        )
                    total_latency_ms = int((time.time() - start_time) * 1000)
                    logger.info(
                        f"[Story 7.2] SHORT-CIRCUIT (cache): Returning {len(verified_results)} verified "
                        f"answer(s) (total latency: {total_latency_ms}ms)"
                    )
                    return verified_results, total_latency_ms
            
            verified_qa_matches = await search_verified_qa(
                db=db,
                tenant_id=tenant_id,
                group_id=group_id_val,
                bot_id=bot_id,
                query_embedding=query_embedding,
                k=k,
                similarity_threshold=VERIFIED_KB_SIMILARITY_THRESHOLD,
                query_text=query,
            )
            
            verified_latency_ms = int((time.time() - verified_start) * 1000)
            logger.debug(
                f"[Story 7.2] Verified KB search: {len(verified_qa_matches)} matches "
                f"in {verified_latency_ms}ms"
            )
            
            # Story 7.2: AC #4 - Check latency budget and log metrics
            if verified_latency_ms > settings.VERIFIED_KB_LATENCY_BUDGET_MS:
                logger.warning(
                    f"[Story 7.2] LATENCY_BUDGET_EXCEEDED: Verified KB search took "
                    f"{verified_latency_ms}ms (budget: {settings.VERIFIED_KB_LATENCY_BUDGET_MS}ms) "
                    f"- consider optimization or caching"
                )
            else:
                logger.info(
                    f"[Story 7.2] LATENCY_OK: Verified KB search within budget "
                    f"({verified_latency_ms}ms / {settings.VERIFIED_KB_LATENCY_BUDGET_MS}ms)"
                )
            
            for verified_qa, similarity in verified_qa_matches:
                # Story 7.2: Create SearchResult with full provenance metadata
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
                        verified_id=verified_qa.id,
                        verified_citations=verified_qa.source_citations,
                    )
                )

            # Populate cache for subsequent hot lookups
            if cache_enabled and verified_results:
                payload = [
                    {
                        "chunk_id": r.chunk_id,
                        "document_id": r.document_id,
                        "document_name": r.document_name,
                        "section": r.section,
                        "text": r.text,
                        "similarity": r.similarity,
                        "position": r.position,
                        "page_number": r.page_number,
                        "verified_answer": r.verified_answer,
                        "verified_id": str(r.verified_id) if r.verified_id else None,
                        "verified_citations": r.verified_citations,
                    }
                    for r in verified_results
                ]
                _verified_kb_cache.set(cache_key, payload, ttl_seconds=cache_ttl)
                logger.debug(
                    f"[Story 7.2] VERIFIED_KB_CACHE_SET: stored {len(payload)} result(s) for TTL={cache_ttl}s"
                )
            
            # Story 7.2: SHORT-CIRCUIT LOGIC (AC #2)
            # If we have high-confidence verified match(es), return immediately
            # No need to search documents or invoke LLM
            if verified_results:
                total_latency_ms = int((time.time() - start_time) * 1000)
                logger.info(
                    f"[Story 7.2] SHORT-CIRCUIT: Returning {len(verified_results)} verified "
                    f"answer(s), skipping document search and LLM generation "
                    f"(total latency: {total_latency_ms}ms)"
                )
                return verified_results, total_latency_ms
            
            logger.debug("[Story 7.2] No verified matches, continuing to document search")
            
        except Exception as e:
            logger.warning(f"Verified KB search failed, continuing with document search: {e}", exc_info=True)

        # ============================================================
        # STEP 2: Search document chunks (standard RAG) - Story 7.2: AC #3
        # Only execute if no verified matches found (fallback path)
        # ============================================================
        
        # Story 7.2: Skip document search if verified_only mode
        if verified_only:
            logger.debug("[Story 7.2] verified_only=True, skipping document search")
            return [], int((time.time() - start_time) * 1000)
        
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

        # Story 7.2: Return document results (verified KB already short-circuited above)
        
        # ============================================================
        # STEP 3: Search KB Emails (Union with Documents)
        # ============================================================
        
        # We need to search KBEmail table as well since it stores embeddings separately from Chunks
        from app.models.kb_email import KBEmail
        
        email_stmt = (
            select(
                KBEmail.id,
                KBEmail.subject,
                KBEmail.body_text,
                KBEmail.email_metadata,
                KBEmail.embedding.cosine_distance(query_embedding).label("distance"),
            )
            .where(KBEmail.tenant_id == tenant_id)
            .where(KBEmail.status == 'ready')
            .where(KBEmail.embedding.isnot(None))
            # Basic RLS: User can see emails if they have access to the group
            # (Assuming same group-based access logic applies)
            .where(KBEmail.group_id == group_id_val)
            .order_by(text("distance"))
            .limit(k * 2)
        )
        
        email_result = await db.execute(email_stmt)
        email_rows = email_result.all()
        
        # Normalize Email Results
        for row in email_rows:
            similarity = 1.0 - row.distance
            if similarity >= similarity_threshold:
                # Mock a "chunk" tuple structure or add directly to results list if refactored
                # For minimal refactor, we'll append to a unified list of (item, type, similarity)
                pass

        # REFACTOR: Unified Search Result Construction
        # 1. Document Chunks
        unified_results = []
        
        for row, similarity in chunk_results:
            chunk = row
            doc = documents.get(chunk.document_id)
            doc_name = doc.filename if doc else "Unknown"
            
            section = None
            is_verified = False
            if chunk.metadata_json:
                try:
                    import json
                    meta = json.loads(chunk.metadata_json)
                    section = meta.get("section")
                    is_verified = bool(meta.get("verified") or meta.get("is_verified"))
                except: pass

            unified_results.append(SearchResult(
                chunk_id=str(chunk.id),
                document_id=str(chunk.document_id),
                document_name=doc_name,
                section=section,
                text=chunk.content,
                similarity=round(similarity, 4),
                position=chunk.chunk_index,
                page_number=chunk.page_number,
                is_verified=is_verified
            ))
            
        # 2. KB Emails
        for row in email_rows:
            similarity = 1.0 - row.distance
            if similarity >= similarity_threshold:
                # Use subject as document name, body as text
                # We can construct a pseudo-chunk-id from email id
                unified_results.append(SearchResult(
                    chunk_id=f"email_{str(row.id)}",
                    document_id=str(row.id),
                    document_name=f"Email: {row.subject or 'No Subject'}",
                    section="KB Email",
                    text=row.body_text or "",
                    similarity=round(similarity, 4),
                    position=0,
                    page_number=None,
                    is_verified=False
                ))
        
        # Sort combined results by similarity descending
        unified_results.sort(key=lambda x: x.similarity, reverse=True)
        
        # Take top K
        final_results = unified_results[:k]

        latency_ms = int((time.time() - start_time) * 1000)
        logger.info(
            f"Hybrid search completed: query='{query[:50]}...', "
            f"bot_id={bot_id}, results={len(final_results)} (docs+emails), "
            f"latency={latency_ms}ms"
        )

        return final_results, latency_ms


class VectorSearchError(Exception):
    """Exception raised when vector search fails."""

    pass
