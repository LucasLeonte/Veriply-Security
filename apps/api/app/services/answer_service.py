"""Answer generation service orchestrating vector search, LLM, and confidence routing.

Coordinates VectorSearchService for context retrieval, LLMService for
answer generation, and ConfidenceCalculatorService for routing decisions.
Handles edge cases like empty context and provides streaming token-by-token responses.

Story 3.4: Added confidence scoring and HITL routing.
"""

import logging
import time
from dataclasses import dataclass
from typing import AsyncIterator, List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.llm_service import LLMService, LLMError
from app.services.vector_search_service import VectorSearchService, SearchResult
from app.services.confidence_service import (
    ConfidenceCalculatorService,
    ConfidenceResult,
    RoutingDecision,
)

logger = logging.getLogger(__name__)


# HITL placeholder message shown to end-users when confidence is low
HITL_PENDING_MESSAGE = "I'm checking with the team for the best answer. You'll hear from us shortly."


@dataclass
class AnswerResponse:
    """Response from answer generation with routing information.
    
    Attributes:
        answer_generator: Async iterator of answer tokens (or None if HITL)
        metadata: Query metadata and stats
        confidence: Confidence calculation result
        routing_decision: Whether to auto-send or route to HITL
        hitl_message: Message to show user if routed to HITL
    """
    answer_generator: Optional[AsyncIterator[str]]
    metadata: dict
    confidence: ConfidenceResult
    routing_decision: RoutingDecision
    hitl_message: Optional[str] = None


class AnswerGenerationService:
    """Service for generating answers from context and LLM with confidence routing."""

    def __init__(
        self,
        vector_search_service: VectorSearchService,
        llm_service: LLMService,
        confidence_calculator: Optional[ConfidenceCalculatorService] = None,
    ):
        """Initialize answer generation service.

        Args:
            vector_search_service: Service for semantic search
            llm_service: Service for LLM answer generation
            confidence_calculator: Service for confidence scoring (optional, created if None)
        """
        self.vector_search_service = vector_search_service
        self.llm_service = llm_service
        self.confidence_calculator = confidence_calculator or ConfidenceCalculatorService()

    async def generate(
        self,
        db: AsyncSession,
        bot_id: UUID,
        tenant_id: UUID,
        query: str,
        k: int = 5,
        conversation_history: Optional[List[dict]] = None,
    ) -> tuple[AsyncIterator[str], dict]:
        """Generate answer from context with streaming response (legacy interface).

        Performs semantic search to retrieve context, then streams answer tokens
        from LLM. Handles empty context gracefully by returning appropriate message.
        
        NOTE: This method does NOT perform confidence routing. Use generate_with_routing()
        for full Story 3.4 functionality.

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
                    "verified": chunk.is_verified,
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

    async def generate_with_routing(
        self,
        db: AsyncSession,
        bot_id: UUID,
        tenant_id: UUID,
        group_id: Optional[UUID],
        user_id: Optional[UUID],
        query: str,
        confidence_threshold: int = 80,
        k: int = 5,
        conversation_history: Optional[List[dict]] = None,
        is_verified_kb: bool = False,
    ) -> AnswerResponse:
        """Generate answer with confidence scoring and HITL routing.

        Full Story 3.4 implementation:
        1. Retrieves context via vector search
        2. Calculates confidence score
        3. Routes to auto-send OR HITL based on threshold
        4. Returns answer or HITL pending message

        Args:
            db: Database session
            bot_id: Bot ID for context filtering
            tenant_id: Tenant ID for RLS
            query: User's question
            confidence_threshold: Bot's threshold (0-100, default 80)
            k: Number of context chunks to retrieve
            conversation_history: Previous messages for multi-turn conversations
            is_verified_kb: Whether answer comes from Verified KB

        Returns:
            AnswerResponse with answer generator, confidence, and routing decision

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
            "confidence_threshold": confidence_threshold,
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
                    "verified": getattr(chunk, "is_verified", False),
                }
                for chunk in search_results
            ]

            # Determine Verified KB presence for routing
            if any(getattr(chunk, "is_verified", False) for chunk in search_results):
                is_verified_kb = True

            logger.info(
                f"Vector search returned {len(search_results)} chunks "
                f"(latency: {search_latency_ms}ms)"
            )

        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            raise

        # Step 2: Generate AI draft (always, regardless of routing decision)
        # This ensures HITL queue has the AI draft for human review
        logger.debug(
            f"Generating AI draft with {len(search_results)} context chunks"
        )

        draft_tokens = []
        try:
            async for token in self.llm_service.generate_answer(
                query=query,
                context_chunks=search_results,
                conversation_history=conversation_history,
            ):
                draft_tokens.append(token)
            
            ai_draft = "".join(draft_tokens)
            metadata["ai_draft"] = ai_draft
            metadata["tokens_generated"] = len(draft_tokens)
            
            logger.info(
                f"AI draft generated: {len(draft_tokens)} tokens"
            )

        except LLMError as e:
            logger.error(f"Failed to generate AI draft: {e}")
            # Don't fail the entire operation if draft generation fails
            ai_draft = "Failed to generate draft"
            metadata["ai_draft"] = ai_draft

        # Step 3: Calculate confidence and determine routing
        confidence_result = await self.confidence_calculator.calculate_confidence(
            db=db,
            bot_id=bot_id,
            tenant_id=tenant_id,
            group_id=group_id,
            user_id=user_id,
            query=query,
            search_results=search_results,
            confidence_threshold=confidence_threshold,
            is_verified_kb=is_verified_kb,
            metadata_json={
                "search_results": metadata.get("search_results", []),
                "confidence_threshold": confidence_threshold,
                "ai_draft": ai_draft,
                "citations": [
                    {
                        "source": chunk.document_name,
                        "relevance": chunk.similarity,
                    }
                    for chunk in search_results
                ],
            },
        )

        # Add confidence to metadata
        metadata["confidence"] = {
            "overall_score": int(confidence_result.overall_score * 100),
            "retrieval_confidence": confidence_result.retrieval_confidence,
            "context_coverage": confidence_result.context_coverage,
            "source_consistency": confidence_result.source_consistency,
            "generation_confidence": confidence_result.generation_confidence,
            "reasoning": confidence_result.reasoning,
        }
        metadata["routing_decision"] = confidence_result.routing_decision.value
        metadata["query_id"] = str(confidence_result.query_id)

        logger.info(
            f"Confidence calculated: {confidence_result.overall_score:.0%}, "
            f"routing={confidence_result.routing_decision.value}"
        )

        # Step 4: Route based on confidence
        if confidence_result.routing_decision == RoutingDecision.HITL:
            # Low confidence - route to HITL queue
            logger.info(
                f"Routing to HITL: confidence={confidence_result.overall_score:.0%} "
                f"< threshold={confidence_threshold}%"
            )
            
            # Return HITL response (no answer generator)
            return AnswerResponse(
                answer_generator=None,
                metadata=metadata,
                confidence=confidence_result,
                routing_decision=RoutingDecision.HITL,
                hitl_message=HITL_PENDING_MESSAGE,
            )

        # Step 5: High confidence - return the generated answer as iterator
        logger.debug("Auto-send: returning generated answer")

        # Create an async generator that yields the already-generated draft tokens
        async def answer_generator() -> AsyncIterator[str]:
            """Generator that yields tokens from the already-generated draft."""
            for token in draft_tokens:
                yield token

        return AnswerResponse(
            answer_generator=answer_generator(),
            metadata=metadata,
            confidence=confidence_result,
            routing_decision=RoutingDecision.AUTO_SEND,
            hitl_message=None,
        )

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
