"""Chat endpoint for public bot interactions."""

import json
import logging
from typing import AsyncIterator, Optional
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
from app.services.context_service import ContextService, DEFAULT_CONTEXT_WINDOW
from app.services.confidence_service import ConfidenceCalculatorService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/bots", tags=["chat"])
context_service = ContextService()


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
            confidence_threshold=getattr(bot, "confidence_threshold", 80),
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

    # Prepare conversation context (last N + summary of older)
    context_window = request.context_window or DEFAULT_CONTEXT_WINDOW
    
    # Validate context window size
    if context_window < 1 or context_window > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Context window must be between 1 and 100",
        )
    
    context_messages: list[ChatMessage] = []

    if request.context:
        context_messages = request.context
    elif request.conversation_history:
        context_messages = [
            ChatMessage(role=msg.get("role"), content=msg.get("content", ""))
            for msg in request.conversation_history
            if isinstance(msg, dict)
            and msg.get("role") in {"user", "assistant"}
            and msg.get("content")
        ]

    conversation_context = ""
    try:
        conversation_context = await context_service.prepare_context(
            context_messages, context_window
        )
    except Exception as context_error:
        logger.warning(
            f"Context preparation failed, continuing without context: {context_error}"
        )
        conversation_context = ""

    # Initialize services
    embedding_service = EmbeddingService()
    vector_search_service = VectorSearchService(embedding_service)
    llm_service = LLMService()
    confidence_service = ConfidenceCalculatorService()

    try:
        # Get tenant_id from bot for context retrieval
        tenant_id = bot.tenant_id

        # Retrieve relevant context from vector store
        # Use a balanced similarity threshold: high enough to avoid noise,
        # but not so strict that we almost never find context in dev
        search_results, _latency_ms = await vector_search_service.search(
            db=db,
            bot_id=bot_id,
            tenant_id=tenant_id,
            query=request.query.strip(),
            k=3,  # Get top 3 chunks (reduced from 5 to minimize noise)
            similarity_threshold=0.5,
        )

        if not search_results:
            # No relevant context found
            return StreamingResponse(
                _stream_no_context_response(),
                media_type="text/event-stream",
            )

        # Pass SearchResult objects directly to LLM service
        # LLMService expects List[SearchResult], not list of dicts

        # Build conversation history
        conversation_history = []
        if not conversation_context and context_messages:
            conversation_history = context_messages[-context_window:]

        # Generate AI draft tokens (not streamed yet);
        # we hold them until confidence is calculated and routing decided.
        draft_tokens: list[str] = []
        async for token in llm_service.generate_answer(
            query=request.query.strip(),
            context_chunks=search_results,
            conversation_history=[{"role": m.role, "content": m.content} for m in conversation_history],
            conversation_context=conversation_context,
        ):
            draft_tokens.append(token)
        ai_draft = "".join(draft_tokens)

        # Prepare lightweight citations metadata for confidence logging
        confidence_citations = [
            {"source": result.document_name or "Unknown", "similarity": result.similarity}
            for result in search_results
        ]

        # Build detailed citations for streaming metadata.
        # Use the same threshold as vector search (0.5) so that
        # every retrieved chunk is surfaced as a source.
        CITATION_SIMILARITY_THRESHOLD = 0.5
        streaming_citations = [
            {
                "source": result.document_name or "Unknown",
                "document_name": result.document_name or "Unknown",
                "document_id": result.document_id,
                "chunk_id": result.chunk_id,
                "page_number": result.page_number,
                "section": result.section,
                "position": result.position,
                "text": result.text,
                "similarity": result.similarity,
                "url": f"/api/v1/documents/{result.document_id}/chunks",
            }
            for result in search_results
            if result.similarity >= CITATION_SIMILARITY_THRESHOLD
        ]

        # Log low-confidence chunks that were excluded from citations
        low_confidence = [r for r in search_results if r.similarity < CITATION_SIMILARITY_THRESHOLD]
        if low_confidence:
            logger.debug(
                f"Excluded {len(low_confidence)} low-confidence chunk(s) from citations: "
                f"{[f'{r.document_name}({r.similarity:.2f})' for r in low_confidence]}"
            )

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
                "citations": confidence_citations,
            },
        )
        # Keep confidence as 0-1 for the streaming API; UI already expects a 0-1 float.
        confidence_value = float(confidence_result.overall_score)

        # Routing decision: HITL  wait message; AUTO_SEND  stream draft tokens
        if confidence_result.routing_decision.value == "hitl":
            return StreamingResponse(
                _stream_hitl_wait_response(confidence_value),
                media_type="text/event-stream",
            )

        # Auto-send: stream the precomputed draft tokens with metadata
        return StreamingResponse(
            _stream_precomputed_response(
                tokens=draft_tokens,
                citations=streaming_citations,
                extra_metadata={"confidence": confidence_value},
            ),
            media_type="text/event-stream",
        )

    except Exception as e:
        logger.error(f"Error processing chat query: {e}")
        return StreamingResponse(
            _stream_error_response(str(e)),
            media_type="text/event-stream",
        )


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


async def _stream_hitl_wait_response(confidence: float) -> AsyncIterator[str]:
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
