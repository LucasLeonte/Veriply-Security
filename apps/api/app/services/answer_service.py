"""Answer generation service orchestrating vector search and LLM.

Coordinates VectorSearchService for context retrieval and LLMService for
answer generation. Handles edge cases like empty context and provides
streaming token-by-token responses.
"""

import logging
import time
from typing import AsyncIterator, List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.llm_service import LLMService, LLMError
from app.services.vector_search_service import VectorSearchService, SearchResult

logger = logging.getLogger(__name__)


class AnswerGenerationService:
    """Service for generating answers from context and LLM."""

    def __init__(
        self,
        vector_search_service: VectorSearchService,
        llm_service: LLMService,
    ):
        """Initialize answer generation service.

        Args:
            vector_search_service: Service for semantic search
            llm_service: Service for LLM answer generation
        """
        self.vector_search_service = vector_search_service
        self.llm_service = llm_service

    async def generate(
        self,
        db: AsyncSession,
        bot_id: UUID,
        tenant_id: UUID,
        query: str,
        k: int = 5,
        conversation_history: Optional[List[dict]] = None,
    ) -> tuple[AsyncIterator[str], dict]:
        """Generate answer from context with streaming response.

        Performs semantic search to retrieve context, then streams answer tokens
        from LLM. Handles empty context gracefully by returning appropriate message.

        Args:
            db: Database session
            bot_id: Bot ID for context filtering
            tenant_id: Tenant ID for RLS
            query: User's question
            k: Number of context chunks to retrieve
            conversation_history: Previous messages for multi-turn conversations

        Returns:
            Tuple of (async iterator of tokens, metadata dict)
            Metadata includes: search_latency_ms, context_chunks_count, model, etc.

        Raises:
            ValueError: If query is empty or parameters invalid
            LLMError: If answer generation fails
        """
        # Validate inputs
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")

        metadata = {
            "query": query,
            "bot_id": str(bot_id),
            "tenant_id": str(tenant_id),
            "k": k,
            "context_chunks": 0,
            "search_latency_ms": 0,
            "tokens_generated": 0,
            "generation_latency_s": 0,
            "model": self.llm_service.model,
        }

        # Step 1: Retrieve context chunks via vector search
        logger.debug(f"Searching for context: query='{query[:100]}...'")

        try:
            search_results, search_latency_ms = (
                await self.vector_search_service.search(
                    db=db,
                    bot_id=bot_id,
                    tenant_id=tenant_id,
                    query=query,
                    k=k,
                    similarity_threshold=0.5,
                )
            )

            metadata["context_chunks"] = len(search_results)
            metadata["search_latency_ms"] = search_latency_ms
            metadata["search_results"] = [
                {
                    "document": chunk.document_name,
                    "section": chunk.section,
                    "similarity": chunk.similarity,
                }
                for chunk in search_results
            ]

            logger.info(
                f"Vector search returned {len(search_results)} chunks "
                f"(latency: {search_latency_ms}ms)"
            )

        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            raise

        # Step 2: Generate answer using retrieved context
        logger.debug(
            f"Generating answer with {len(search_results)} context chunks"
        )

        try:
            gen_start_time = time.time()
            tokens_count = 0

            async def answer_generator() -> AsyncIterator[str]:
                """Inner generator to count tokens and update metadata."""
                nonlocal tokens_count
                async for token in self.llm_service.generate_answer(
                    query=query,
                    context_chunks=search_results,
                    conversation_history=conversation_history,
                ):
                    tokens_count += 1
                    yield token

                generation_elapsed = time.time() - gen_start_time
                metadata["tokens_generated"] = tokens_count
                metadata["generation_latency_s"] = round(generation_elapsed, 2)

                logger.info(
                    f"Answer generation complete: "
                    f"tokens={tokens_count}, latency={generation_elapsed:.2f}s"
                )

            return answer_generator(), metadata

        except LLMError as e:
            logger.error(f"Failed to generate answer: {e}")
            raise

    async def generate_from_context(
        self,
        query: str,
        context_chunks: List[SearchResult],
        conversation_history: Optional[List[dict]] = None,
    ) -> AsyncIterator[str]:
        """Generate answer directly from provided context chunks.

        Useful for testing or when context is already retrieved.

        Args:
            query: User's question
            context_chunks: Pre-retrieved context chunks
            conversation_history: Previous messages for multi-turn conversations

        Yields:
            Generated tokens from LLM
        """
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")

        logger.debug(f"Generating answer with {len(context_chunks)} context chunks")

        async for token in self.llm_service.generate_answer(
            query=query,
            context_chunks=context_chunks,
            conversation_history=conversation_history,
        ):
            yield token
