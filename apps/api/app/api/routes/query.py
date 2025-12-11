"""Query endpoint for context-only answer generation with streaming support."""

import json
import logging
from typing import AsyncIterator

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.core.database import get_db
from app.api.v1.auth import get_current_user, get_current_tenant
from app.models.user import User
from app.schemas.query import QueryRequest, QueryResponse, QueryMetadata
from app.services.llm_service import LLMService, LLMError
from app.services.vector_search_service import VectorSearchService
from app.services.answer_service import AnswerGenerationService
from app.services.embedding_service import EmbeddingService, EmbeddingError
from app.services.bot_service import BotService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/bots", tags=["query"])


@router.post("/{bot_id}/query")
async def query_bot(
    bot_id: UUID,
    query_request: QueryRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: UUID = Depends(get_current_tenant),
):
    """
    Query a bot for context-only answers with optional streaming.

    - **bot_id**: ID of the bot to query
    - **query**: User's question (required, 1-2000 chars)
    - **stream**: Stream response tokens (SSE) or return complete JSON (default: true)
    - **conversation_history**: Previous messages for multi-turn context (optional)
    - **k**: Number of context chunks to retrieve (default: 5, 1-20)

    Returns:
        - If stream=true: Server-Sent Events stream with tokens and final metadata
        - If stream=false: Complete JSON response with full answer and metadata

    Note:
        - User must have access to this bot (RLS enforced)
        - Streaming response provides real-time feedback with tokens as they're generated
        - All answers are constrained to provided context (no hallucination)
    """
    # Validate query
    if not query_request.query or not query_request.query.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Query cannot be empty",
        )

    # Verify bot exists and belongs to tenant
    try:
        bot = await BotService.get_bot(db=db, bot_id=bot_id, tenant_id=tenant_id)
        if not bot:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bot not found",
            )
    except Exception as e:
        logger.error(f"Error verifying bot access: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to verify bot access",
        )

    # Initialize services
    embedding_service = EmbeddingService()
    vector_search_service = VectorSearchService(embedding_service)
    llm_service = LLMService()
    answer_service = AnswerGenerationService(vector_search_service, llm_service)

    try:
        # Generate answer with streaming
        answer_generator, metadata = await answer_service.generate(
            db=db,
            bot_id=bot_id,
            tenant_id=tenant_id,
            query=query_request.query.strip(),
            k=query_request.k,
            conversation_history=query_request.conversation_history,
        )

        # Return streaming or non-streaming response
        if query_request.stream:
            return StreamingResponse(
                _stream_answer(answer_generator, metadata),
                media_type="text/event-stream",
            )
        else:
            # Collect full answer
            full_answer = ""
            async for token in answer_generator:
                full_answer += token

            return QueryResponse(
                answer=full_answer,
                metadata=QueryMetadata(**metadata),
            )

    except EmbeddingError as e:
        logger.error(f"Embedding error for bot {bot_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to search knowledge base",
        )
    except LLMError as e:
        logger.error(f"LLM error for bot {bot_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate answer",
        )
    except Exception as e:
        logger.exception(f"Unexpected error querying bot {bot_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred",
        )
    finally:
        # Clean up services
        await embedding_service.close()
        await llm_service.close()


async def _stream_answer(
    answer_generator: AsyncIterator[str], metadata: dict
) -> AsyncIterator[str]:
    """Stream answer tokens as Server-Sent Events.

    Args:
        answer_generator: Async iterator of tokens
        metadata: Metadata about the query execution

    Yields:
        SSE formatted events with tokens and completion metadata
    """
    try:
        # Stream tokens
        position = 0
        async for token in answer_generator:
            event = {"token": token, "position": position}
            yield f"data: {json.dumps(event)}\n\n"
            position += 1

        # Send completion event with metadata
        completion_event = {"type": "complete", "metadata": metadata}
        yield f"data: {json.dumps(completion_event)}\n\n"

    except Exception as e:
        logger.error(f"Error streaming answer: {e}")
        error_event = {"type": "error", "message": str(e)}
        yield f"data: {json.dumps(error_event)}\n\n"
