"""Chat endpoint for public bot interactions."""

import json
import logging
from typing import AsyncIterator
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.bot import Bot
from app.schemas.chat import ChatQueryRequest, ChatMessage, PublicBotInfo
from app.schemas.widget import WidgetConfigResponse
from app.models import WidgetConfig
from app.services.llm_service import LLMService
from app.services.vector_search_service import VectorSearchService
from app.services.embedding_service import EmbeddingService
from app.services.context_service import ContextService, DEFAULT_CONTEXT_WINDOW
from app.services.confidence_service import ConfidenceCalculatorService
from app.services.domain_whitelist_service import extract_request_origin, matches_whitelist

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/bots", tags=["chat"])
context_service = ContextService()


@router.get("/{bot_id}/public", response_model=PublicBotInfo)
async def get_public_bot_info(
    bot_id: UUID,
    response: Response,
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
    # Add CORS headers for widget embedding
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "*"
    
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
            description=bot.description,
            avatar_url=getattr(bot, "avatar_url", None),
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
    http_request: Request,
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

        # Enforce domain whitelist before processing request
        widget_cfg_result = await db.execute(
            select(WidgetConfig).where(WidgetConfig.bot_id == bot_id)
        )
        widget_cfg = widget_cfg_result.scalar_one_or_none()
        allowed_domains = (widget_cfg.allowed_domains or []) if widget_cfg else []

        if allowed_domains:
            origin = extract_request_origin(http_request)
            if not matches_whitelist(origin, allowed_domains):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="This widget is not authorized for this domain",
                )

        # Retrieve relevant context from vector store
        search_results, _latency_ms = await vector_search_service.search(
            db=db,
            bot_id=bot_id,
            tenant_id=tenant_id,
            query=request.query.strip(),
            k=3,
            similarity_threshold=0.5,
        )

        if not search_results:
            # No relevant context found
            response = StreamingResponse(
                _stream_no_context_response(),
                media_type="text/event-stream",
            )
            response.headers["Access-Control-Allow-Origin"] = "*"
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
            response.headers["Access-Control-Allow-Headers"] = "*"
            return response

        # Check if we have a verified Q&A match - if so, use it directly
        # Verified answers have is_verified=True and verified_answer set
        verified_match = None
        for result in search_results:
            if result.is_verified and result.verified_answer:
                verified_match = result
                break

        # Build conversation history that will be sent to the LLM
        conversation_history: list[ChatMessage] = []
        if not conversation_context and context_messages:
            conversation_history = context_messages[-context_window:]

        # If we have a verified answer, use it directly (no LLM needed)
        if verified_match:
            logger.info(
                f"Using verified Q&A answer for query '{request.query.strip()[:50]}...' "
                f"(similarity={verified_match.similarity})"
            )
            ai_draft = verified_match.verified_answer
            draft_tokens = [ai_draft]  # Single token for verified answer
        else:
            # Generate AI draft tokens via LLM
            draft_tokens: list[str] = []
            async for token in llm_service.generate_answer(
                query=request.query.strip(),
                context_chunks=search_results,
                conversation_history=[
                    {"role": m.role, "content": m.content} for m in conversation_history
                ],
                conversation_context=conversation_context or None,
            ):
                draft_tokens.append(token)
            ai_draft = "".join(draft_tokens)

        # Prepare lightweight citations metadata for confidence logging
        confidence_citations = [
            {
                "source": result.document_name or "Unknown",
                "similarity": result.similarity,
            }
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
        low_confidence = [
            r for r in search_results if r.similarity < CITATION_SIMILARITY_THRESHOLD
        ]
        if low_confidence:
            logger.debug(
                "Excluded %d low-confidence chunk(s) from citations: %s",
                len(low_confidence),
                [f"{r.document_name}({r.similarity:.2f})" for r in low_confidence],
            )

        # Calculate confidence score using draft + citations
        threshold = getattr(bot, "confidence_threshold", 80)
        is_verified_kb = any(
            getattr(r, "is_verified", False) for r in search_results
        )
        
        # If we used a verified Q&A answer, bypass confidence check - it's already human-approved
        if verified_match:
            # Verified answers should NEVER go to HITL - they're already human-approved
            confidence_value = 1.0  # Maximum confidence for verified answers
            return StreamingResponse(
                _stream_precomputed_response(
                    tokens=draft_tokens,
                    citations=streaming_citations,
                    extra_metadata={
                        "confidence": confidence_value,
                        "is_verified_answer": True,
                        "verified_qa_id": verified_match.document_id,
                    },
                ),
                media_type="text/event-stream",
            )
        
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

        # Keep confidence as 0–1 for the streaming API; UI expects a float in [0,1].
        confidence_value = float(confidence_result.overall_score)

        # Routing decision: send a wait message for HITL, otherwise stream draft
        if confidence_result.routing_decision.value == "hitl":
            response = StreamingResponse(
                _stream_hitl_wait_response(confidence_value),
                media_type="text/event-stream",
            )
            response.headers["Access-Control-Allow-Origin"] = "*"
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
            response.headers["Access-Control-Allow-Headers"] = "*"
            return response

        response = StreamingResponse(
            _stream_precomputed_response(
                tokens=draft_tokens,
                citations=streaming_citations,
                extra_metadata={"confidence": confidence_value},
                response_id=confidence_result.query_id,
            ),
            media_type="text/event-stream",
        )
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "*"
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing chat query: {e}")
        response = StreamingResponse(
            _stream_error_response(str(e)),
            media_type="text/event-stream",
        )
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "*"
        return response


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
    response_id: UUID | None = None,
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
    if response_id:
        metadata["response_id"] = str(response_id)
        
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


@router.get("/{bot_id}/widget/config", response_model=WidgetConfigResponse)
async def get_public_widget_config(
    bot_id: UUID,
    http_request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Public widget configuration for a bot (no auth).

    Returns defaults if no explicit config exists. Only allowed if bot is public.
    """
    # Validate bot exists and public
    bot = await db.get(Bot, bot_id)
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
    if hasattr(bot, "is_public") and not bot.is_public:
        raise HTTPException(status_code=403, detail="Bot is not public")

    result = await db.execute(select(WidgetConfig).where(WidgetConfig.bot_id == bot_id))
    cfg = result.scalar_one_or_none()
    allowed_domains = (cfg.allowed_domains or []) if cfg else []

    if allowed_domains:
        origin = extract_request_origin(http_request)
        if not matches_whitelist(origin, allowed_domains):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This widget is not authorized for this domain",
            )

    if cfg is None:
        # Compose defaults with bot welcome message if present
        return WidgetConfigResponse(
            bot_id=str(bot_id),
            position="bottom-right",
            primary_color="#3B82F6",
            welcome_message=getattr(bot, "welcome_message", None),
            auto_open=False,
            allowed_domains=[],
        )

    return WidgetConfigResponse(**cfg.to_dict())
