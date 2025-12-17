"""Query API routes for RAG Q&A with confidence scoring and routing.

Story 3.4: Confidence Scoring & Routing
Provides endpoints for querying bots with confidence-based HITL routing.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from uuid import UUID
from typing import Optional
import json
import logging

from app.models import Bot, GroupMember, GroupRole
from app.core.auth import get_current_user
from app.core.database import get_db
from app.schemas.confidence import (
    QueryWithConfidenceRequest,
    QueryWithConfidenceResponse,
    HITLPendingResponse,
    ConfidenceScore,
    ConfidenceComponents,
    RoutingInfo,
    RoutingDecisionEnum,
)
from app.services.answer_service import AnswerGenerationService, AnswerResponse
from app.services.confidence_service import RoutingDecision
from app.services.vector_search_service import VectorSearchService
from app.services.llm_service import LLMService
from app.services.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/bots/{bot_id}/query", tags=["query"])


def get_answer_service() -> AnswerGenerationService:
    """Create and return AnswerGenerationService with dependencies."""
    embedding_service = EmbeddingService()
    vector_search_service = VectorSearchService(embedding_service)
    llm_service = LLMService()
    return AnswerGenerationService(vector_search_service, llm_service)


async def verify_bot_access(
    bot_id: UUID,
    current_user: dict,
    session: AsyncSession,
) -> Bot:
    """Verify user has access to the bot and return bot object."""
    # Get the bot
    bot = await session.scalar(select(Bot).where(Bot.id == bot_id))
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
    
    # Verify tenant isolation
    if str(bot.tenant_id) != current_user["tenant_id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Verify group membership if bot has group_id
    if bot.group_id:
        member = await session.scalar(
            select(GroupMember).where(
                (GroupMember.group_id == bot.group_id)
                & (GroupMember.user_id == UUID(current_user["sub"]))
            )
        )
        if not member:
            raise HTTPException(status_code=403, detail="Not a member of this bot's group")
    
    return bot


@router.post("", response_model=QueryWithConfidenceResponse | HITLPendingResponse)
async def query_bot_with_confidence(
    bot_id: UUID,
    request: QueryWithConfidenceRequest,
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    """
    Query a bot with confidence scoring and HITL routing.
    
    This endpoint:
    1. Retrieves relevant context via vector search
    2. Calculates confidence score (retrieval + consistency + generation)
    3. Routes to auto-send OR HITL based on bot's confidence threshold
    
    **Routing Logic:**
    - If confidence >= threshold: Returns generated answer
    - If confidence < threshold: Returns HITL pending message
    
    **Confidence Components:**
    - Retrieval confidence (40%): Max similarity from vector search
    - Source consistency (30%): Agreement between retrieved chunks
    - Generation confidence (30%): LLM logprobs (future)
    
    **Verified KB:**
    - Answers from Verified KB get 95% confidence and always auto-send
    """
    # Verify access and get bot
    bot = await verify_bot_access(bot_id, current_user, session)
    
    # Use request threshold override or bot's default
    threshold = request.auto_send_threshold or bot.confidence_threshold
    
    # Get answer service
    answer_service = get_answer_service()
    
    try:
        # Generate answer with confidence routing
        response: AnswerResponse = await answer_service.generate_with_routing(
            db=session,
            bot_id=bot_id,
            tenant_id=UUID(current_user["tenant_id"]),
            group_id=bot.group_id,
            user_id=UUID(current_user["sub"]),
            query=request.query,
            confidence_threshold=threshold,
            k=5,
            is_verified_kb=False,
        )
        
        # Build confidence score response
        confidence_score = ConfidenceScore(
            overall_score=int(response.confidence.overall_score * 100),
            components=ConfidenceComponents(
                retrieval_confidence=response.confidence.retrieval_confidence,
                context_coverage=response.confidence.context_coverage,
                source_consistency=response.confidence.source_consistency,
                generation_confidence=response.confidence.generation_confidence,
            ),
            reasoning=response.confidence.reasoning,
        )
        
        # Handle HITL routing
        if response.routing_decision == RoutingDecision.HITL:
            routing_info = RoutingInfo(
                decision=RoutingDecisionEnum.HITL,
                reason=f"Low confidence ({int(response.confidence.overall_score * 100)}%) below threshold ({threshold}%)",
                end_user_message=response.hitl_message,
            )
            
            return HITLPendingResponse(
                message=response.hitl_message,
                confidence=confidence_score,
                routing=routing_info,
                query_id=response.confidence.query_id,
            )
        
        # Auto-send: Collect the full answer
        answer_text = ""
        if response.answer_generator:
            async for token in response.answer_generator:
                answer_text += token
        
        routing_info = RoutingInfo(
            decision=RoutingDecisionEnum.AUTO_SEND,
            reason=f"Overall confidence ({int(response.confidence.overall_score * 100)}%) exceeds threshold ({threshold}%)",
            end_user_message=None,
        )
        
        return QueryWithConfidenceResponse(
            answer=answer_text,
            confidence=confidence_score,
            routing=routing_info,
            source="verified_kb" if response.confidence.is_verified_kb else "rag",
            query_id=response.confidence.query_id,
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Query failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to process query")


@router.post("/stream")
async def query_bot_stream(
    bot_id: UUID,
    request: QueryWithConfidenceRequest,
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    """
    Query a bot with streaming response.
    
    Returns Server-Sent Events (SSE) stream with:
    - Confidence metadata first
    - Then answer tokens (if auto-send)
    - Or HITL pending message (if routed to HITL)
    
    **Event Types:**
    - `confidence`: Confidence score and routing decision
    - `token`: Answer token (streaming)
    - `hitl`: HITL pending message
    - `done`: Stream complete
    - `error`: Error occurred
    """
    # Verify access and get bot
    bot = await verify_bot_access(bot_id, current_user, session)
    
    threshold = request.auto_send_threshold or bot.confidence_threshold
    answer_service = get_answer_service()
    
    async def event_generator():
        try:
            # Generate with routing
            response: AnswerResponse = await answer_service.generate_with_routing(
                db=session,
                bot_id=bot_id,
                tenant_id=UUID(current_user["tenant_id"]),
                group_id=bot.group_id,
                user_id=UUID(current_user["sub"]),
                query=request.query,
                confidence_threshold=threshold,
                k=5,
            )
            
            # Send confidence metadata first
            confidence_data = {
                "overall_score": int(response.confidence.overall_score * 100),
                "retrieval_confidence": response.confidence.retrieval_confidence,
                "context_coverage": response.confidence.context_coverage,
                "source_consistency": response.confidence.source_consistency,
                "generation_confidence": response.confidence.generation_confidence,
                "reasoning": response.confidence.reasoning,
                "routing_decision": response.routing_decision.value,
                "query_id": str(response.confidence.query_id),
            }
            yield f"event: confidence\ndata: {json.dumps(confidence_data)}\n\n"
            
            # Handle HITL routing
            if response.routing_decision == RoutingDecision.HITL:
                hitl_data = {
                    "message": response.hitl_message,
                    "query_id": str(response.confidence.query_id),
                }
                yield f"event: hitl\ndata: {json.dumps(hitl_data)}\n\n"
                yield "event: done\ndata: {}\n\n"
                return
            
            # Stream answer tokens
            if response.answer_generator:
                async for token in response.answer_generator:
                    yield f"event: token\ndata: {json.dumps({'token': token})}\n\n"
            
            yield "event: done\ndata: {}\n\n"
            
        except Exception as e:
            logger.error(f"Stream query failed: {e}")
            yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )
