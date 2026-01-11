"""Chat endpoint for public bot interactions."""

import json
import logging
import string
from typing import AsyncIterator, Optional
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, status, Response, Request, Header
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db, set_tenant_context
from app.core.auth import decode_jwt
from app.core.settings import settings
from fastapi import APIRouter, Depends, HTTPException, status, Response, Request, Header, WebSocket, WebSocketDisconnect
import redis.asyncio as aioredis
import asyncio
from typing import Dict, Set
from app.models.bot import Bot
from app.models.confidence_log import RoutingDecision
from app.schemas.chat import ChatQueryRequest, ChatMessage, PublicBotInfo
from app.schemas.widget import WidgetConfigResponse
from app.models import WidgetConfig
from app.services.llm_service import LLMService
from app.services.vector_search_service import VectorSearchService
from app.services.embedding_service import EmbeddingService
from app.services.context_service import ContextService, DEFAULT_CONTEXT_WINDOW
from app.services.confidence_service import ConfidenceCalculatorService
from app.services.domain_whitelist_service import extract_request_origin, matches_whitelist
from app.services.chat_message_service import ChatMessageService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/bots", tags=["chat"])
context_service = ContextService()
chat_message_service = ChatMessageService()


@router.get("/{bot_id}/public", response_model=PublicBotInfo)
async def get_public_bot_info(
    bot_id: UUID,
    response: Response,
    db: AsyncSession = Depends(get_db),
    authorization: Optional[str] = Header(None),
):
    """
    Get public information about a bot.
    
    - No authentication: Only returns info if bot is public
    - With authentication: Returns info regardless of public status (for bot owners/members)

    Returns bot name, avatar, welcome message, and public status.
    Used by the public chat interface to render bot details.

    Returns:
        - 200: Bot public information
        - 404: Bot not found
        - 403: Bot is not public (only for unauthenticated requests)
    """
    # Add CORS headers for widget embedding
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "*"
    
    # Check if user is authenticated
    is_authenticated = False
    if authorization:
        token = None
        if authorization.startswith("Bearer "):
            token = authorization.replace("Bearer ", "")
        else:
            token = authorization
            
        if token:
            try:
                payload = decode_jwt(token)
                if payload:
                    is_authenticated = True
                    logger.debug(f"User authenticated for bot {bot_id}")
            except Exception as e:
                logger.debug(f"Token validation failed: {e}")
                pass  # Invalid token, treat as unauthenticated
    
    try:
        # Get bot without tenant/user context (public endpoint)
        bot = await db.get(Bot, bot_id)

        if not bot:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bot not found",
            )

        # Check public visibility (skip check if authenticated)
        if not is_authenticated and hasattr(bot, "is_public") and not bot.is_public:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Bot is not public. Enable 'Allow link sharing' in bot settings.",
            )
        
        # Check if bot is active
        if hasattr(bot, "is_active") and not bot.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Bot is currently disabled",
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


from app.core.auth import get_current_user, security, get_jwt_secret, JWT_ALGORITHM
import jwt
from typing import Optional

async def get_current_user_optional(
    request: Request,
    credentials = Depends(security)
) -> Optional[dict]:
    """
    Optional authentication. Returns user dict if authenticated, None otherwise.
    Does NOT raise HTTPException.
    """
    token = request.cookies.get("access_token")
    if not token and credentials:
        token = credentials.credentials
    
    if not token:
        return None
    
    try:
        payload = jwt.decode(token, get_jwt_secret(), algorithms=[JWT_ALGORITHM])
        user_id: str = payload.get("sub")
        tenant_id: str = payload.get("tenant_id")
        
        if not user_id or not tenant_id:
            return None
            
        return {
            "sub": user_id, 
            "tenant_id": tenant_id,
            "role": payload.get("role")
        }
    except Exception:
        return None

@router.post("/{bot_id}/chat/query")
async def chat_query(
    bot_id: UUID,
    request: ChatQueryRequest,
    http_request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[dict] = Depends(get_current_user_optional),
):
    """
    Query a bot via public chat interface (no authentication required).
    If user is authenticated (e.g. via dashboard), logs the user_id.

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
    # Use provided session_id or generate a new one
    session_id = request.session_id or str(uuid4())
    
    # Get user_id if authenticated
    user_id = UUID(current_user["sub"]) if current_user else None

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

        # Basic public check
        if not bot.is_public:
             # Check if user is the owner/admin of this tenant. 
             # If so, allow access even if private (Preview Mode)
             if not (current_user and str(bot.tenant_id) == str(current_user.get("tenant_id"))):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Bot is not public",
                )
        
        if not bot.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Bot is currently disabled",
            )

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

        # Log User Message
        await chat_message_service.log_message(
            db=db,
            bot_id=bot_id,
            tenant_id=tenant_id,
            session_id=session_id,
            role="user",
            content=request.query.strip(),
            user_id=user_id,
            client_message_id=request.message_id,
            origin=extract_request_origin(http_request) or "unknown",
        )
        
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

        # Check for greeting/chitchat (bypass vector search)
        normalized_query = request.query.strip().lower()
        normalized_query = normalized_query.translate(str.maketrans('', '', string.punctuation))
        
        if normalized_query in GREETINGS:
            logger.info(f"Greeting detected: '{request.query}', sending welcome message")
            response = StreamingResponse(
                _stream_greeting_response(getattr(bot, "welcome_message", None)),
                media_type="text/event-stream",
            )
            response.headers["Access-Control-Allow-Origin"] = "*"
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
            response.headers["Access-Control-Allow-Headers"] = "*"
            return response

        # Retrieve relevant context from vector store
        search_results, _latency_ms = await vector_search_service.search(
            db=db,
            bot_id=bot_id,
            tenant_id=tenant_id,
            query=request.query.strip(),
            k=8,
            similarity_threshold=0.40, # Lowered from 0.60 to allow broader matching (especially for multilingual/semantic)
        )

        # Debug logging for KB search results
        if search_results:
            verified_count = sum(1 for r in search_results if r.is_verified)
            doc_count = sum(1 for r in search_results if not r.is_verified and not r.chunk_id.startswith('email_'))
            email_count = sum(1 for r in search_results if r.chunk_id.startswith('email_'))
            logger.info(
                f"[Chat KB Debug] Query: '{request.query.strip()[:50]}...' → "
                f"Found {len(search_results)} results: {verified_count} verified, {doc_count} docs, {email_count} emails"
            )
            for i, r in enumerate(search_results[:3]):  # Log top 3 results
                logger.debug(
                    f"[Chat KB Debug] Result #{i+1}: sim={r.similarity:.3f}, "
                    f"verified={r.is_verified}, doc='{r.document_name[:40]}...'"
                )
        else:
            logger.warning(
                f"[Chat KB Debug] Query: '{request.query.strip()[:50]}...' → "
                f"No results found! Check if bot has KB entries."
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

        # Log Assistant Message (RAG or Verified)
        await chat_message_service.log_message(
            db=db,
            bot_id=bot_id,
            tenant_id=tenant_id,
            session_id=session_id,
            role="assistant",
            content=ai_draft,
            citations=[
                {
                    "source": result.document_name or "Unknown",
                    "document_id": str(result.document_id),
                    "chunk_id": str(result.chunk_id),
                    "url": f"/api/v1/documents/{result.document_id}/chunks",
                    "similarity": result.similarity
                }
                for result in search_results
            ] if search_results else None,
            answer_id=verified_match.verified_id if verified_match else None,
            origin=extract_request_origin(http_request) or "unknown",
        )

        # Prepare lightweight citations metadata for confidence logging
        confidence_citations = [
            {
                "source": result.document_name or "Unknown",
                "similarity": result.similarity,
            }
            for result in search_results
        ]

        # Build detailed citations for streaming metadata.
        # Use the same threshold as vector search so that
        # every retrieved chunk is surfaced as a source.
        CITATION_SIMILARITY_THRESHOLD = 0.70
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
            # Story 7.2: Verified answers skip LLM and return immediately with provenance
            logger.info(
                f"[Story 7.2] Returning verified answer (ID: {verified_match.verified_id}, "
                f"similarity: {verified_match.similarity:.4f})"
            )
            confidence_value = 1.0  # Maximum confidence for verified answers
            return StreamingResponse(
                _stream_precomputed_response(
                    tokens=draft_tokens,
                    citations=streaming_citations,
                    extra_metadata={
                        "confidence": confidence_value,
                        # Story 7.2: AC #2 - Add verified metadata
                        "verified": True,
                        "verified_id": str(verified_match.verified_id),
                        "verified_confidence": verified_match.similarity,
                        "trust_level": "verified",
                        "source_type": "verified_kb",
                        # Include citations from verified entry if available
                        **({"verified_citations": verified_match.verified_citations}
                           if verified_match.verified_citations else {}),
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
                "session_id": request.session_id,  # For sending approved answers back to chat
                "message_id": request.message_id,
            },
        )

        # Keep confidence as 0–1 for the streaming API; UI expects a float in [0,1].
        confidence_value = float(confidence_result.overall_score)

        # Stream the AI draft regardless of confidence - frontend will handle review queue submission
        # The ConfidenceLog is already created with routing_decision=hitl, so the review queue
        # will pick it up when the frontend submits it
        response = StreamingResponse(
            _stream_precomputed_response(
                tokens=draft_tokens,
                citations=streaming_citations,
                extra_metadata={
                    "confidence": confidence_value,
                    # Story 7.2: Mark as AI-generated from RAG
                    "verified": False,
                    "trust_level": "ai_generated",
                    "source_type": "rag",
                    # Include routing decision for frontend to handle appropriately
                    "routing_decision": confidence_result.routing_decision.value,
                },
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


GREETINGS = {
    "hey", "hi", "hello", "hallo", "hoi", "good morning", "good afternoon", "good evening",
    "bonjour", "salut", "yo", "greetings", "start", "begin"
}

async def _stream_greeting_response(welcome_message: Optional[str] = None) -> AsyncIterator[str]:
    """Stream a greeting response."""
    message = welcome_message or "Hello! How can I help you today?"
    
    for char in message:
        yield f"data: {json.dumps({'token': char})}\n\n"
        
    yield f"data: {json.dumps({'metadata': {'citations': [], 'chunks_used': 0, 'confidence': 1.0}})}\n\n"
    yield "data: [DONE]\n\n"


# ============================================================================
# WebSocket for Real-Time Chat Updates
# ============================================================================

class ChatConnectionManager:
    """
    Manages WebSocket connections for chat sessions.
    """
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, session_id: str):
        await websocket.accept()
        if session_id not in self.active_connections:
            self.active_connections[session_id] = set()
        self.active_connections[session_id].add(websocket)
        logger.debug(f"WebSocket connected for session {session_id}")

    def disconnect(self, websocket: WebSocket, session_id: str):
        if session_id in self.active_connections:
            self.active_connections[session_id].discard(websocket)
            if not self.active_connections[session_id]:
                del self.active_connections[session_id]
        logger.debug(f"WebSocket disconnected for session {session_id}")

    async def send_message(self, session_id: str, message: dict):
        if session_id in self.active_connections:
            for connection in self.active_connections[session_id]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"Error sending to chat connection: {e}")

chat_connection_manager = ChatConnectionManager()

@router.websocket("/{bot_id}/chat/ws/{session_id}")
async def websocket_chat_endpoint(
    websocket: WebSocket,
    bot_id: UUID, 
    session_id: str,
):
    """
    WebSocket endpoint for real-time chat updates (e.g. approved answers).
    Subscribes to Redis channel chat_session:{session_id}.
    """
    await chat_connection_manager.connect(websocket, session_id)
    
    redis_client = None
    pubsub = None
    
    try:
        # Connect to Redis with robust fallback
        try:
            # Try configured URL first
            redis_client = await aioredis.from_url(settings.REDIS_URL, decode_responses=True)
            await redis_client.ping()
        except Exception as first_error:
            logger.warning(f"Initial Redis connection failed: {first_error}. Attempting localhost fallback...")
            try:
                # Fallback to localhost default
                fallback_url = "redis://localhost:6379/0"
                if settings.REDIS_PASSWORD:
                    # If password is set, try to use it with localhost
                    fallback_url = f"redis://:{settings.REDIS_PASSWORD}@localhost:6379/0"
                
                redis_client = await aioredis.from_url(fallback_url, decode_responses=True)
                await redis_client.ping()
                logger.info(f"Connected to Redis via fallback: {fallback_url}")
            except Exception as second_error:
                logger.error(f"Redis fallback also failed: {second_error}")
                # Re-raise the original error if fallback fails
                raise first_error

        pubsub = redis_client.pubsub()
        channel = f"chat_session:{session_id}"
        await pubsub.subscribe(channel)
        logger.info(f"Chat WebSocket subscribed to {channel}")
        
        # Send initial connected message
        await websocket.send_json({
            "type": "connected",
            "session_id": session_id,
            "timestamp": asyncio.get_event_loop().time()
        })

        # Main loop: listen for Redis messages or client disconnect
        while True:
            try:
                # We need to poll both websocket (for close) and redis
                # Usually we just loop on redis, but if client disconnects we need to know.
                # However, Starlette/FastAPI handles disconnect by raising WebSocketDisconnect
                # when we try to send/receive.
                
                # Use a task to listen to Redis
                message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                
                if message and message["type"] == "message":
                    data = json.loads(message["data"])
                    await websocket.send_json(data)
                
                # Check for client messages (pings) to keep alive
                # Use wait_for to yield control
                try:
                    client_msg = await asyncio.wait_for(websocket.receive_text(), timeout=0.1)
                    # If we receive something, pass
                except asyncio.TimeoutError:
                    pass
                    
            except WebSocketDisconnect:
                break
            except Exception as e:
                # Only log non-disconnect errors
                if "disconnect" not in str(e).lower():
                    logger.error(f"Error in chat websocket loop: {e}")
                break

            # Small sleep to prevent tight loop
            await asyncio.sleep(0.1)
            
    except Exception as e:
        logger.error(f"Chat WebSocket error: {e}")
        try:
            await websocket.close(code=status.WS_1011_SERVER_ERROR)
        except:
            pass
            
    finally:
        chat_connection_manager.disconnect(websocket, session_id)
        if pubsub:
            try:
                await pubsub.unsubscribe()
                await pubsub.close()
            except:
                pass
        if redis_client:
            try:
                await redis_client.close()
            except:
                pass
