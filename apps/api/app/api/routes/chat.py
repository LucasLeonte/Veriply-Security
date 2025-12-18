"""Chat endpoint for public bot interactions."""

import json
import logging
from typing import AsyncIterator, Optional
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.bot import Bot
from app.schemas.chat import ChatQueryRequest, ChatMessage, PublicBotInfo
from app.services.llm_service import LLMService
from app.services.vector_search_service import VectorSearchService
from app.services.embedding_service import EmbeddingService
from app.services.context_service import ContextService, DEFAULT_CONTEXT_WINDOW

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

    try:
        # Get tenant_id from bot for context retrieval
        tenant_id = bot.tenant_id

        # Retrieve relevant context from vector store
        # Use higher thresholds to reduce false positives in citations
        search_results, _latency_ms = await vector_search_service.search(
            db=db,
            bot_id=bot_id,
            tenant_id=tenant_id,
            query=request.query.strip(),
            k=3,  # Get top 3 chunks (reduced from 5 to minimize noise)
            similarity_threshold=0.65,  # Raised from 0.5 to 0.65 for higher relevance bar
        )

        if not search_results:
            # No relevant context found
            return StreamingResponse(
                _stream_no_context_response(),
                media_type="text/event-stream",
            )

        # Pass SearchResult objects directly to LLM service
        # LLMService expects List[SearchResult], not list of dicts

        # Build conversation history (only if no formatted context available)
        conversation_history = []
        if not conversation_context and context_messages:
            conversation_history = context_messages[-context_window:]

        # Stream LLM response
        return StreamingResponse(
            _stream_llm_response(
                llm_service=llm_service,
                query=request.query.strip(),
                context_chunks=search_results,  # Pass SearchResult objects directly
                conversation_history=conversation_history,
                conversation_context=conversation_context or None,
            ),
            media_type="text/event-stream",
        )

    except Exception as e:
        logger.error(f"Error processing chat query: {e}")
        return StreamingResponse(
            _stream_error_response(str(e)),
            media_type="text/event-stream",
        )


@router.get("/{bot_id}/chat/{message_id}/status")
async def get_message_status(
    bot_id: UUID,
    message_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Check status of a pending verification message.

    Used by frontend to poll for HITL verification completion.
    When a low-confidence response is pending verification, the frontend
    polls this endpoint until the status changes to "resolved".

    Args:
        - bot_id: UUID of the bot
        - message_id: ID of the pending message

    Returns:
        - 200: { status: "pending" | "resolved", response?: {...} }
        - 404: Message not found or not pending
    """
    try:
        # Verify bot exists
        bot = await db.get(Bot, bot_id)
        if not bot:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bot not found",
            )

        # TODO: Implement message status tracking in database
        # For now, return pending status as placeholder
        # In production:
        # 1. Query message_status table to get current status
        # 2. If status == "resolved", fetch and return the verified response
        # 3. If status == "pending", return pending status
        # 4. If message not found, return 404

        logger.debug(f"Checking status for message {message_id} in bot {bot_id}")

        # Placeholder response - implement when HITL queue is ready
        return {
            "status": "pending",
            "error": "Message status tracking not yet implemented",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking message status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check message status",
        )


async def _stream_llm_response(
    llm_service: LLMService,
    query: str,
    context_chunks: list,  # List[SearchResult]
    conversation_history: list[ChatMessage],
    conversation_context: Optional[str] = None,
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
            conversation_context=conversation_context,
        ):
            token_count += 1
            yield f"data: {json.dumps({'token': token})}\n\n"

        # Calculate trust level based on source and confidence
        # For now, we treat all RAG responses as ai_generated
        # TODO: Integrate VerifiedKBService to check if from Verified KB
        trust_level = "ai_generated"
        source_type = "rag"
        
        # Calculate confidence score from average similarity of chunks
        if context_chunks:
            avg_similarity = sum(chunk.similarity for chunk in context_chunks) / len(context_chunks)
            confidence_score = avg_similarity * 100  # Convert to percentage
        else:
            confidence_score = 0.0
        
        # Send metadata at the end
        # Filter citations to only high-confidence matches (≥0.65 similarity)
        CITATION_SIMILARITY_THRESHOLD = 0.65
        citations = [
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
            for result in context_chunks
            if result.similarity >= CITATION_SIMILARITY_THRESHOLD
        ]
        
        # Log low-confidence chunks that were excluded from citations
        low_confidence = [r for r in context_chunks if r.similarity < CITATION_SIMILARITY_THRESHOLD]
        if low_confidence:
            logger.debug(
                f"Excluded {len(low_confidence)} low-confidence chunk(s) from citations: "
                f"{[f'{r.document_name}({r.similarity:.2f})' for r in low_confidence]}"
            )

        # Filter citations to only high-confidence matches
        # CITATION_SIMILARITY_THRESHOLD = 0.65 filters out low-confidence chunks
        # that may have false positive relevance. Matches search_results threshold
        # to ensure consistency between search retrieval and citation display.
        metadata = {
            "citations": citations,
            "chunks_used": len(context_chunks),
            "token_count": token_count,
            "trust_level": trust_level,
            "confidence_score": round(confidence_score, 2),
            "source_type": source_type,
            "response_id": str(uuid4()),
        }

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

    # Send empty metadata
    yield f"data: {json.dumps({'metadata': {'citations': [], 'chunks_used': 0}})}\n\n"
    yield "data: [DONE]\n\n"


async def _stream_error_response(error: str) -> AsyncIterator[str]:
    """Stream an error response."""
    yield f"data: {json.dumps({'error': 'Sorry, I encountered an issue. Please try again.', 'detail': error})}\n\n"
    yield "data: [DONE]\n\n"
