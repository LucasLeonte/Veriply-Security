"""Confidence calculation service for answer routing decisions.

Calculates confidence scores based on retrieval quality, source consistency,
and LLM generation confidence. Routes answers to auto-send or HITL queue
based on bot's configured threshold.

Story 3.4: Confidence Scoring & Routing
"""

import logging
from dataclasses import dataclass
from decimal import Decimal
from typing import List, Optional
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.confidence_log import ConfidenceLog, RoutingDecision
from app.services.vector_search_service import SearchResult

logger = logging.getLogger(__name__)


# Confidence component weights (must sum to 1.0)
# Note: Since generation_confidence is not yet implemented (returns None),
# weights effectively become: retrieval 60% + context_coverage 40%
# This balances single-best-match quality with overall evidence breadth
RETRIEVAL_WEIGHT = 0.6
CONTEXT_COVERAGE_WEIGHT = 0.4
GENERATION_WEIGHT = 0.0  # Placeholder - not yet implemented

# Verified KB confidence boost
VERIFIED_KB_CONFIDENCE = 0.95

# Minimum confidence for "no context" case
NO_CONTEXT_CONFIDENCE = 0.0

# Patterns that indicate the bot doesn't know the answer
NO_ANSWER_PATTERNS = [
    "i don't have information",
    "i don't know",
    "i do not have information",
    "i do not know",
    "i'm not sure",
    "i am not sure",
    "i cannot find",
    "i can't find",
    "no information available",
    "not in the knowledge base",
    "checking with the team",
    "i'm checking with",
    "i am checking with",
    "you'll hear from us",
    "unable to answer",
    "cannot answer",
    "can't answer",
    "don't have enough information",
    "do not have enough information",
    "outside my knowledge",
    "beyond my knowledge",
    "not able to find",
]


@dataclass
class ConfidenceResult:
    """Result of confidence calculation.
    
    Attributes:
        overall_score: Combined confidence score (0-1)
        retrieval_confidence: Max similarity from vector search (60% weight)
        context_coverage: Average similarity across chunks (40% weight)
        source_consistency: Agreement between retrieved chunks (used in reasoning only)
        generation_confidence: Not implemented - placeholder for future LLM logprobs
        routing_decision: Whether to auto_send or route to HITL
        is_verified_kb: Whether answer came from verified KB
        reasoning: Human-readable explanation of the score
    """
    overall_score: float
    retrieval_confidence: float
    context_coverage: float
    source_consistency: Optional[float]
    generation_confidence: Optional[float]  # Always None - not implemented
    routing_decision: RoutingDecision
    is_verified_kb: bool
    reasoning: str
    query_id: UUID


class ConfidenceCalculatorService:
    """Service for calculating confidence scores and routing decisions.
    
    Implements the confidence formula:
        confidence = (retrieval × 0.6) + (context coverage × 0.4)
    
    Note: Generation confidence (LLM logprobs) is not yet implemented.
    When available, the intended formula will be:
        confidence = (retrieval × 0.4) + (context coverage × 0.3) + (generation × 0.3)
    """

    async def calculate_confidence(
        self,
        db: AsyncSession,
        bot_id: UUID,
        tenant_id: UUID,
        query: str,
        search_results: List[SearchResult],
        confidence_threshold: int,
        group_id: Optional[UUID] = None,
        user_id: Optional[UUID] = None,
        is_verified_kb: bool = False,
        token_logprobs: Optional[List[float]] = None,
        metadata_json: Optional[dict] = None,
    ) -> ConfidenceResult:
        """Calculate confidence score and determine routing decision.
        
        Args:
            db: Database session for logging
            bot_id: Bot processing the query
            tenant_id: Tenant ID for RLS
            query: Original query text
            search_results: Retrieved chunks from vector search
            confidence_threshold: Bot's configured threshold (0-100)
            is_verified_kb: Whether answer comes from Verified KB
            token_logprobs: LLM token log probabilities (future)
        
        Returns:
            ConfidenceResult with score components and routing decision
        """
        query_id = uuid4()
        
        # Convert threshold from 0-100 to 0-1
        threshold = confidence_threshold / 100.0
        
        # Extract AI draft from metadata to check for "I don't know" responses
        ai_draft = metadata_json.get("ai_draft", "") if metadata_json else ""
        answer_confidence = self._calculate_answer_confidence(ai_draft)
        
        # If bot says it doesn't know, confidence should be 0
        if answer_confidence == 0.0:
            logger.info("Bot indicates it doesn't know the answer - confidence set to 0")
            result = ConfidenceResult(
                overall_score=0.0,
                retrieval_confidence=0.0,
                context_coverage=0.0,
                source_consistency=None,
                generation_confidence=0.0,
                routing_decision=RoutingDecision.hitl,
                is_verified_kb=False,
                reasoning="Bot indicated it doesn't have the answer - routing to human review",
                query_id=query_id,
            )
            await self._log_confidence(
                db=db,
                bot_id=bot_id,
                tenant_id=tenant_id,
                query_id=query_id,
                query=query,
                result=result,
                threshold=threshold,
                group_id=group_id,
                user_id=user_id,
                metadata_json=metadata_json,
            )
            return result
        
        # Verified KB answers get automatic high confidence
        if is_verified_kb:
            result = self._create_verified_kb_result(query_id, threshold)
            await self._log_confidence(
                db=db,
                bot_id=bot_id,
                tenant_id=tenant_id,
                query_id=query_id,
                query=query,
                result=result,
                threshold=threshold,
                group_id=group_id,
                user_id=user_id,
                metadata_json=metadata_json,
            )
            return result
        
        # Calculate confidence components
        retrieval_confidence = self._calculate_retrieval_confidence(search_results)
        context_coverage = self._calculate_context_coverage(search_results)
        source_consistency = self._calculate_source_consistency(search_results)
        
        # Combine components with weighting (60% retrieval + 40% coverage)
        overall_score = self._combine_confidence_scores(
            retrieval_confidence,
            context_coverage,
        )
        
        # Determine routing decision
        routing_decision = (
            RoutingDecision.auto_send 
            if overall_score >= threshold 
            else RoutingDecision.hitl
        )
        
        # Generate human-readable reasoning
        reasoning = self._generate_reasoning(
            retrieval_confidence,
            context_coverage,
            source_consistency,
            overall_score,
            threshold,
            routing_decision,
            search_results,
        )
        
        result = ConfidenceResult(
            overall_score=round(overall_score, 3),
            retrieval_confidence=round(retrieval_confidence, 3),
            context_coverage=round(context_coverage, 3),
            source_consistency=round(source_consistency, 3) if source_consistency else None,
            generation_confidence=None,  # Not implemented
            routing_decision=routing_decision,
            is_verified_kb=False,
            reasoning=reasoning,
            query_id=query_id,
        )
        
        # Log confidence calculation
        await self._log_confidence(
            db=db,
            bot_id=bot_id,
            tenant_id=tenant_id,
            query_id=query_id,
            query=query,
            result=result,
            threshold=threshold,
            group_id=group_id,
            user_id=user_id,
            metadata_json=metadata_json,
        )
        
        logger.info(
            f"Confidence calculated: score={overall_score:.2%}, "
            f"threshold={threshold:.2%}, routing={routing_decision.value}, "
            f"bot_id={bot_id}"
        )
        
        return result

    def _calculate_answer_confidence(self, ai_draft: str) -> float:
        """Calculate confidence based on the AI's answer content.
        
        Detects "I don't know" type responses and returns 0 confidence.
        Otherwise returns 1.0 to indicate the bot gave a substantive answer.
        
        Args:
            ai_draft: The AI-generated draft answer
            
        Returns:
            0.0 if bot indicates it doesn't know, 1.0 otherwise
            None is returned (as 1.0) if no ai_draft is provided to skip this check
        """
        # If no ai_draft provided, skip the answer content check
        # This allows confidence to be calculated from retrieval metrics alone
        if ai_draft is None or ai_draft == "":
            return 1.0
        
        draft_lower = ai_draft.lower()
        
        for pattern in NO_ANSWER_PATTERNS:
            if pattern in draft_lower:
                logger.debug(f"Detected 'no answer' pattern: '{pattern}'")
                return 0.0
        
        return 1.0

    def _calculate_retrieval_confidence(
        self, 
        search_results: List[SearchResult]
    ) -> float:
        """Calculate retrieval confidence from vector search results.
        
        Uses the maximum similarity score from retrieved chunks.
        
        Args:
            search_results: Retrieved chunks with similarity scores
            
        Returns:
            Retrieval confidence (0-1)
        """
        if not search_results:
            logger.debug("No search results - retrieval confidence is 0")
            return NO_CONTEXT_CONFIDENCE
        
        # Use max similarity as retrieval confidence
        max_similarity = max(chunk.similarity for chunk in search_results)
        
        logger.debug(
            f"Retrieval confidence: {max_similarity:.3f} "
            f"(from {len(search_results)} chunks)"
        )
        
        return max_similarity

    def _calculate_context_coverage(
        self,
        search_results: List[SearchResult],
    ) -> float:
        """Estimate context coverage as average similarity of returned chunks.

        This acts as a proxy for how well retrieved context can support the answer.
        """
        if not search_results:
            return 0.0

        avg_similarity = sum(chunk.similarity for chunk in search_results) / len(search_results)
        return max(0.0, min(1.0, avg_similarity))

    def _calculate_source_consistency(
        self,
        search_results: List[SearchResult],
    ) -> Optional[float]:
        """Calculate source consistency from retrieved chunks.
        
        Measures agreement between multiple retrieved sources.
        High consistency = chunks say similar things (low hallucination risk).
        Low consistency = chunks contradict (high hallucination risk).
        
        MVP: Returns average similarity as proxy for consistency.
        Future: Use pairwise embedding comparison.
        
        Args:
            search_results: Retrieved chunks with similarity scores
            
        Returns:
            Source consistency score (0-1) or None if insufficient data
        """
        if len(search_results) < 2:
            # Need at least 2 chunks to measure consistency
            return None
        
        # MVP: Use average similarity as consistency proxy
        # Future: Calculate pairwise chunk embedding similarity
        avg_similarity = sum(chunk.similarity for chunk in search_results) / len(search_results)
        
        logger.debug(
            f"Source consistency (proxy): {avg_similarity:.3f} "
            f"(avg of {len(search_results)} chunks)"
        )
        
        return avg_similarity

    # FUTURE IMPLEMENTATION: Generation Confidence from LLM Token Logprobs
    # Currently not implemented because Ollama doesn't expose per-token probabilities.
    # Uncomment and integrate when LLM provides logprobs in responses.
    #
    # def _calculate_generation_confidence(
    #     self,
    #     token_logprobs: Optional[List[float]],
    # ) -> Optional[float]:
    #     """Calculate generation confidence from LLM token logprobs.
    #     
    #     Extracts confidence from token probability distributions.
    #     Higher average logprob = more confident generation.
    #     
    #     Args:
    #         token_logprobs: Token-level log probabilities from LLM
    #         
    #     Returns:
    #         Generation confidence (0-1) or None if not available
    #     """
    #     if not token_logprobs:
    #         return None
    #     
    #     # Convert average logprob to confidence score
    #     # logprob=-0.1 → ~0.9, logprob=-1.0 → ~0.5, logprob=-5+ → ~0.0
    #     avg_logprob = sum(token_logprobs) / len(token_logprobs)
    #     confidence = 1.0 / (1.0 + abs(avg_logprob) * 0.5)
    #     
    #     logger.debug(f"Generation confidence: {confidence:.3f} (from logprobs)")
    #     
    #     return max(0.0, min(1.0, confidence))

    def _combine_confidence_scores(
        self,
        retrieval_confidence: float,
        context_coverage: float,
    ) -> float:
        """Combine confidence components with weighting.
        
        Current formula: (retrieval × 0.6) + (context_coverage × 0.4)
        
        Args:
            retrieval_confidence: Max similarity from vector search (60% weight)
            context_coverage: Average similarity across all chunks (40% weight)
            
        Returns:
            Overall confidence score (0-1)
        """
        score = (retrieval_confidence * RETRIEVAL_WEIGHT) + (context_coverage * CONTEXT_COVERAGE_WEIGHT)
        return max(0.0, min(1.0, score))

    def _create_verified_kb_result(
        self,
        query_id: UUID,
        threshold: float,
    ) -> ConfidenceResult:
        """Create confidence result for Verified KB answer.
        
        Verified KB answers automatically get 95% confidence and auto-send.
        """
        return ConfidenceResult(
            overall_score=VERIFIED_KB_CONFIDENCE,
            retrieval_confidence=VERIFIED_KB_CONFIDENCE,
            context_coverage=VERIFIED_KB_CONFIDENCE,
            source_consistency=None,
            generation_confidence=None,
            routing_decision=RoutingDecision.auto_send,
            is_verified_kb=True,
            reasoning="Answer from Verified Knowledge Base - human-verified content (95% confidence)",
            query_id=query_id,
        )

    def _generate_reasoning(
        self,
        retrieval_confidence: float,
        context_coverage: float,
        source_consistency: Optional[float],
        overall_score: float,
        threshold: float,
        routing_decision: RoutingDecision,
        search_results: List[SearchResult],
    ) -> str:
        """Generate human-readable reasoning for confidence score.
        
        Explains why the score is what it is, for agent transparency.
        """
        reasons = []
        
        # Retrieval quality (60% weight)
        if retrieval_confidence >= 0.85:
            reasons.append("Excellent retrieval match")
        elif retrieval_confidence >= 0.7:
            reasons.append("Good retrieval match")
        elif retrieval_confidence >= 0.5:
            reasons.append("Moderate retrieval match")
        elif retrieval_confidence > 0:
            reasons.append("Poor retrieval match")
        else:
            reasons.append("No relevant context found")

        # Context coverage (40% weight)
        if context_coverage >= 0.8:
            reasons.append("strong context coverage")
        elif context_coverage >= 0.6:
            reasons.append("moderate context coverage")
        elif context_coverage > 0:
            reasons.append("limited context coverage")
        else:
            reasons.append("no supporting context")
        
        # Source consistency (informational only, not used in score)
        if source_consistency is not None:
            if source_consistency >= 0.8:
                reasons.append("high agreement between sources")
            elif source_consistency >= 0.6:
                reasons.append("moderate source agreement")
            else:
                reasons.append("sources may be contradictory")
        
        # Combine reasoning
        reasoning = ", ".join(reasons)
        
        # Add routing explanation
        if routing_decision == RoutingDecision.auto_send:
            reasoning += f". Score ({overall_score:.0%}) exceeds threshold ({threshold:.0%})."
        else:
            reasoning += f". Score ({overall_score:.0%}) below threshold ({threshold:.0%}) - routing to human review."
        
        return reasoning

    async def _log_confidence(
        self,
        db: AsyncSession,
        bot_id: UUID,
        tenant_id: UUID,
        query_id: UUID,
        query: str,
        result: ConfidenceResult,
        threshold: float,
        group_id: Optional[UUID] = None,
        user_id: Optional[UUID] = None,
        metadata_json: Optional[dict] = None,
    ) -> None:
        """Log confidence calculation to database for analytics.
        
        Args:
            db: Database session
            bot_id: Bot ID
            query_id: Unique query identifier
            query: Original query text
            result: Confidence calculation result
            threshold: Bot's confidence threshold
            group_id: Optional group identifier
            user_id: Optional user identifier
            metadata_json: Additional metadata to persist
        """
        from datetime import datetime, timedelta
        from sqlalchemy import and_
        from sqlalchemy.future import select
        
        try:
            # Dedup check: prevent duplicate entries for the same query within 5 seconds
            # This handles React StrictMode double-invocations
            dedup_window = datetime.utcnow() - timedelta(seconds=5)
            query_text_truncated = query[:500] if query else None
            
            existing = await db.execute(
                select(ConfidenceLog.id).where(
                    and_(
                        ConfidenceLog.bot_id == bot_id,
                        ConfidenceLog.tenant_id == tenant_id,
                        ConfidenceLog.query_text == query_text_truncated,
                        ConfidenceLog.created_at >= dedup_window,
                    )
                ).limit(1)
            )
            if existing.scalar_one_or_none() is not None:
                logger.debug(f"Skipping duplicate confidence log for query: {query_text_truncated[:50]}...")
                return

            # Guard: Do not re-queue questions that were previously resolved (approved or rejected)
            try:
                existing_resolved = await db.scalar(
                    select(ConfidenceLog)
                    .where(ConfidenceLog.bot_id == bot_id)
                    .where(ConfidenceLog.query_text == query_text_truncated)
                    .where(ConfidenceLog.hitl_resolved == True)
                    .order_by(ConfidenceLog.created_at.desc())
                )
                if existing_resolved is not None:
                    logger.info(
                        "Skipping HITL log: previously resolved question detected (id=%s)",
                        existing_resolved.id,
                    )
                    return
            except Exception as e:
                logger.warning("Resolved-check failed; continuing without re-queue guard: %s", e)
            
            metadata_to_store = dict(metadata_json or {})
            metadata_to_store.setdefault("context_coverage", result.context_coverage)
            metadata_to_store.setdefault("source_consistency", result.source_consistency)
            metadata_to_store.setdefault("generation_confidence", result.generation_confidence)

            log_entry = ConfidenceLog(
                bot_id=bot_id,
                tenant_id=tenant_id,
                group_id=group_id,
                user_id=user_id,
                query_id=query_id,
                query_text=query[:500] if query else None,  # Truncate for storage
                retrieval_confidence=Decimal(str(result.retrieval_confidence)),
                source_consistency=(
                    Decimal(str(result.source_consistency)) 
                    if result.source_consistency is not None 
                    else None
                ),
                generation_confidence=(
                    Decimal(str(result.generation_confidence))
                    if result.generation_confidence is not None
                    else None
                ),
                overall_confidence=Decimal(str(result.overall_score)),
                threshold_used=Decimal(str(threshold)),
                routing_decision=result.routing_decision,
                is_verified_kb=result.is_verified_kb,
                hitl_resolved=False,
                metadata_json=metadata_to_store,
            )
            
            db.add(log_entry)
            await db.flush()
            await db.commit()
            
            logger.debug(f"Confidence log created: query_id={query_id}")
            
        except Exception as e:
            logger.error(f"Failed to log confidence: {e}")
            try:
                await db.rollback()
            except Exception:
                logger.error("Rollback failed after logging error")
            # Don't raise - logging failure shouldn't break the flow


class ConfidenceCalculatorError(Exception):
    """Exception raised when confidence calculation fails."""
    pass
