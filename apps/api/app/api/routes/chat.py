"""Chat endpoint for public bot interactions."""

import json
import logging
from typing import AsyncIterator
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.bot import Bot
from app.schemas.chat import ChatQueryRequest, ChatMessage, PublicBotInfo
from app.services.llm_service import LLMService
from app.services.vector_search_service import VectorSearchService
from app.services.embedding_service import EmbeddingService
from app.services.bot_service import BotService
from app.services.confidence_service import ConfidenceCalculatorService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/bots", tags=["chat"])


@router.get("/{bot_id}/public", response_model=PublicBotInfo)
async def get_public_bot_info(
    bot_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Get public information about a bot (no authentication required).

    Returns bot name, avatar, welcome message, and public status.
    Used by the public chat interface to render bot details.

    Returns:
        - 200: Bot public information
        - 404: Bot not found
        - 403: Bot is not public
    """
    try:
        # Get bot without tenant/user context (public endpoint)
        bot = await db.get(Bot, bot_id)

        if not bot:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bot not found",
            )

        # Check public visibility
        if hasattr(bot, "is_public") and not bot.is_public:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Bot is not public",
            )

        return PublicBotInfo(
            id=str(bot.id),
            name=bot.name,
            avatar_url=getattr(bot, "avatar_url", None),
            welcome_message=(
                getattr(bot, "welcome_message", None)
                or bot.description
                or f"Hi! I'm {bot.name}. Ask me anything!"
            ),
            is_public=getattr(bot, "is_public", True),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching public bot info: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch bot information",
        )


@router.post("/{bot_id}/chat/query")
async def chat_query(
    bot_id: UUID,
    request: ChatQueryRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Query a bot via public chat interface (no authentication required).

    Streams response tokens via Server-Sent Events (SSE) for real-time feedback.
    Uses the bot's knowledge base to generate context-only answers.

    Args:
        - bot_id: UUID of the bot to query
        - query: User's question (1-5000 chars)
        - conversation_history: Optional previous messages for context

    Returns:
        - 200: SSE stream with tokens and final metadata
        - 400: Invalid query
        - 404: Bot not found
        - 403: Bot is not public
    """
    # Validate query
    if not request.query or not request.query.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Query cannot be empty",
        )

    if len(request.query) > 5000:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Query too long (max 5000 characters)",
        )

    # Verify bot exists and is public
    try:
        bot = await db.get(Bot, bot_id)

        if not bot:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bot not found",
            )

        # TODO: Check is_public field once added to model
        # if not bot.is_public:
        #     raise HTTPException(
        #         status_code=status.HTTP_403_FORBIDDEN,
        #         detail="Bot is not public",
        #     )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error verifying bot: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to verify bot access",
        )

    # Initialize services
    embedding_service = EmbeddingService()
    vector_search_service = VectorSearchService(embedding_service)
    llm_service = LLMService()
    confidence_service = ConfidenceCalculatorService()

    try:
        # Get tenant_id from bot for context retrieval
        tenant_id = bot.tenant_id

        # Retrieve relevant context from vector store
        search_results, _latency_ms = await vector_search_service.search(
            db=db,
            bot_id=bot_id,
            tenant_id=tenant_id,
            query=request.query.strip(),
            k=5,  # Get top 5 chunks
            similarity_threshold=0.5,
        )

        if not search_results:
            # No relevant context found
            return StreamingResponse(
                _stream_no_context_response(),
                media_type="text/event-stream",
            )

        # Build conversation history
        conversation_history = []
        if request.conversation_history:
            conversation_history = [
                ChatMessage(role=msg["role"], content=msg["content"])
                for msg in request.conversation_history[-4:]  # Last 4 messages
            ]

        # Generate AI draft tokens (not streamed yet)
        draft_tokens: list[str] = []
        async for token in llm_service.generate_answer(
            query=request.query.strip(),
            context_chunks=search_results,
            conversation_history=[{"role": m.role, "content": m.content} for m in conversation_history],
        ):
            draft_tokens.append(token)
        ai_draft = "".join(draft_tokens)

        # Prepare citations metadata
        citations = [
            {"source": result.document_name or "Unknown", "similarity": result.similarity}
            for result in search_results
        ]

        # Calculate confidence score using draft + citations
        threshold = getattr(bot, "confidence_threshold", 80)
        is_verified_kb = any(getattr(r, "is_verified", False) for r in search_results)
        confidence_result = await confidence_service.calculate_confidence(
            db=db,
            bot_id=bot_id,
            tenant_id=tenant_id,
            query=request.query.strip(),
            search_results=search_results,
            confidence_threshold=threshold,
            is_verified_kb=is_verified_kb,
            metadata_json={
                "confidence_threshold": threshold,
                "ai_draft": ai_draft,
                "citations": citations,
            },
        )
        confidence_pct = int(confidence_result.overall_score * 100)

        # Routing decision: HITL → wait message; AUTO_SEND → stream draft tokens
        if confidence_result.routing_decision.value == "hitl":
            return StreamingResponse(
                _stream_hitl_wait_response(confidence_pct),
                media_type="text/event-stream",
            )

        # Auto-send: stream the precomputed draft tokens with metadata
        return StreamingResponse(
            _stream_precomputed_response(
                tokens=draft_tokens,
                citations=citations,
                extra_metadata={"confidence": confidence_pct},
            ),
            media_type="text/event-stream",
        )

    except Exception as e:
        logger.error(f"Error processing chat query: {e}")
        return StreamingResponse(
            _stream_error_response(str(e)),
            media_type="text/event-stream",
        )


async def _stream_llm_response(
    llm_service: LLMService,
    query: str,
    context_chunks: list,  # List[SearchResult]
    conversation_history: list[ChatMessage],
    extra_metadata: dict | None = None,
) -> AsyncIterator[str]:
    """Stream LLM response tokens as SSE events using LLMService.generate_answer."""
    try:
        # Map conversation history to LLM-compatible message dicts
        history_payload = [
            {"role": msg.role, "content": msg.content}
            for msg in conversation_history
        ]

        # Stream tokens from LLM service
        token_count = 0
        async for token in llm_service.generate_answer(
            query=query,
            context_chunks=context_chunks,
            conversation_history=history_payload,
        ):
            token_count += 1
            yield f"data: {json.dumps({'token': token})}\n\n"

        # Send metadata at the end
        citations = [
            {"source": result.document_name or "Unknown", "similarity": result.similarity}
            for result in context_chunks
        ]

        metadata = {
            "citations": citations,
            "chunks_used": len(context_chunks),
            "token_count": token_count,
        }
        if extra_metadata:
            try:
                metadata.update(extra_metadata)
            except Exception:
                # Ignore metadata merge issues
                pass

        yield f"data: {json.dumps({'metadata': metadata})}\n\n"
        yield "data: [DONE]\n\n"

    except Exception as e:
        logger.error(f"Error streaming LLM response: {e}")
        error_msg = {
            "error": "Failed to generate response",
            "detail": str(e),
        }
        yield f"data: {json.dumps(error_msg)}\n\n"


async def _stream_no_context_response() -> AsyncIterator[str]:
    """Stream a no-context response."""
    message = "I couldn't find relevant information in my knowledge base to answer your question. Could you rephrase or ask something else?"

    # Stream token by token
    for char in message:
        yield f"data: {json.dumps({'token': char})}\n\n"

    # Send empty metadata with zero confidence
    yield f"data: {json.dumps({'metadata': {'citations': [], 'chunks_used': 0, 'confidence': 0}})}\n\n"
    yield "data: [DONE]\n\n"


async def _stream_precomputed_response(
    tokens: list[str],
    citations: list[dict],
    extra_metadata: dict | None = None,
) -> AsyncIterator[str]:
    """Stream precomputed tokens and final metadata."""
    token_count = 0
    for token in tokens:
        token_count += 1
        yield f"data: {json.dumps({'token': token})}\n\n"

    metadata = {
        "citations": citations,
        "chunks_used": len(citations),
        "token_count": token_count,
    }
    if extra_metadata:
        try:
            metadata.update(extra_metadata)
        except Exception:
            pass

    yield f"data: {json.dumps({'metadata': metadata})}\n\n"
    yield "data: [DONE]\n\n"


async def _stream_hitl_wait_response(confidence: int) -> AsyncIterator[str]:
    """Stream HITL wait message to end-user with confidence metadata."""
    message = "I'm checking with the team for the best answer. You'll hear from us shortly."
    for ch in message:
        yield f"data: {json.dumps({'token': ch})}\n\n"
    yield f"data: {json.dumps({'metadata': {'citations': [], 'chunks_used': 0, 'confidence': confidence}})}\n\n"
    yield "data: [DONE]\n\n"


async def _stream_error_response(error: str) -> AsyncIterator[str]:
    """Stream an error response."""
    yield f"data: {json.dumps({'error': 'Sorry, I encountered an issue. Please try again.', 'detail': error})}\n\n"
    yield "data: [DONE]\n\n"
