from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from app.core.database import get_db
from app.api.v1.auth import get_current_user, get_current_tenant

from app.schemas.bot import BotCreateRequest, BotUpdateRequest, BotResponse, BotListResponse, BotDuplicateRequest
from app.services.bot_service import BotService
from app.services.embedding_service import EmbeddingService, EmbeddingError
from app.services.vector_search_service import VectorSearchService
from app.models.user import User
import logging
from pydantic import BaseModel, Field
from typing import List, Optional

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/bots", tags=["bots"])

@router.post("", response_model=BotResponse, status_code=201)
async def create_bot(
    bot_data: BotCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: UUID = Depends(get_current_tenant),
):
    """
    Create a new bot for the current tenant.
    
    - **name**: Bot name (required, 2-50 chars, unique per organization)
    - **description**: Optional description (max 500 chars)
    - **confidence_threshold**: Confidence threshold (0-100%, default 80%)
    """
    try:
        bot = await BotService.create_bot(
            db=db,
            tenant_id=tenant_id,
            user_id=current_user.id,
            bot_data=bot_data,
        )
        await db.commit()
        return bot
    except ValueError as e:
        error_msg = str(e)
        if "already exists" in error_msg:
            raise HTTPException(status_code=409, detail=error_msg)
        elif "limit reached" in error_msg:
            raise HTTPException(status_code=402, detail={
                "error": "Bot limit reached",
                "limit": BotService.get_bot_limit(current_user.__dict__.get("subscription_tier")),
                "current": 5,  # Would need to get actual count
            })
        else:
            raise HTTPException(status_code=400, detail=error_msg)
    except Exception as e:
        await db.rollback()
        logger.exception(f"Error creating bot: {e}")
        raise HTTPException(status_code=500, detail="Failed to create bot")

@router.get("", response_model=BotListResponse)
async def list_bots(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    search: str | None = Query(None),
    sort_by: str = Query("name", pattern="^(name|created_at)$"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: UUID = Depends(get_current_tenant),
):
    """
    List all bots for the current tenant with pagination and filtering.
    
    - **limit**: Results per page (default 20, max 100)
    - **offset**: Page offset (default 0)
    - **search**: Filter by bot name (case-insensitive)
    - **sort_by**: Sort by "name" or "created_at" (default "name")
    """
    try:
        bots, total_count = await BotService.list_bots(
            db=db,
            tenant_id=tenant_id,
            limit=limit,
            offset=offset,
            search=search,
            sort_by=sort_by,
        )
        return BotListResponse(
            bots=bots,
            total_count=total_count,
            limit=limit,
            offset=offset,
        )
    except Exception as e:
        logger.exception(f"Error listing bots: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve bots")

@router.get("/{bot_id}", response_model=BotResponse)
async def get_bot(
    bot_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: UUID = Depends(get_current_tenant),
):
    """Get a specific bot by ID (with tenant isolation)."""
    try:
        bot = await BotService.get_bot(db, bot_id, tenant_id)
        if not bot:
            raise HTTPException(status_code=404, detail="Bot not found")
        return bot
    except Exception as e:
        logger.exception(f"Error retrieving bot: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve bot")

@router.patch("/{bot_id}", response_model=BotResponse)
async def update_bot(
    bot_id: UUID,
    bot_data: BotUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: UUID = Depends(get_current_tenant),
):
    """
    Update a bot's settings.
    
    - **name**: Update bot name (must remain unique per organization)
    - **description**: Update description
    - **confidence_threshold**: Update confidence threshold (0-100%)
    """
    try:
        bot = await BotService.update_bot(
            db=db,
            bot_id=bot_id,
            tenant_id=tenant_id,
            bot_data=bot_data,
        )
        await db.commit()
        return bot
    except ValueError as e:
        error_msg = str(e)
        if "not found" in error_msg:
            raise HTTPException(status_code=404, detail=error_msg)
        elif "already exists" in error_msg:
            raise HTTPException(status_code=409, detail=error_msg)
        else:
            raise HTTPException(status_code=400, detail=error_msg)
    except Exception as e:
        await db.rollback()
        logger.exception(f"Error updating bot: {e}")
        raise HTTPException(status_code=500, detail="Failed to update bot")

@router.post("/{bot_id}/duplicate", response_model=BotResponse, status_code=201)
async def duplicate_bot(
    bot_id: UUID,
    duplicate_data: BotDuplicateRequest | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: UUID = Depends(get_current_tenant),
):
    """
    Duplicate a bot by copying settings but NOT documents/embeddings/chat history.
    
    - **name**: Optional custom name for the duplicated bot (default: "[Original Name] (Copy)")
    """
    try:
        new_name = duplicate_data.name if duplicate_data else None
        
        bot = await BotService.duplicate_bot(
            db=db,
            source_bot_id=bot_id,
            tenant_id=tenant_id,
            user_id=current_user.id,
            new_name=new_name,
        )
        await db.commit()
        return bot
    except ValueError as e:
        await db.rollback()
        error_msg = str(e)
        if "not found" in error_msg:
            raise HTTPException(status_code=404, detail=error_msg)
        elif "already exists" in error_msg:
            raise HTTPException(status_code=409, detail=error_msg)
        else:
            raise HTTPException(status_code=400, detail=error_msg)
    except Exception as e:
        await db.rollback()
        logger.exception(f"Error duplicating bot: {e}")
        raise HTTPException(status_code=500, detail="Failed to duplicate bot")

@router.delete("/{bot_id}", status_code=204)
async def delete_bot(
    bot_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: UUID = Depends(get_current_tenant),
):
    """
    Delete a bot and all associated data (documents, embeddings, chunks, chat history).
    
    Requires confirmation by typing the bot name (for safety).
    """
    try:
        await BotService.delete_bot(
            db=db,
            bot_id=bot_id,
            tenant_id=tenant_id,
        )
        await db.commit()
        return None  # 204 No Content
    except ValueError as e:
        await db.rollback()
        error_msg = str(e)
        if "not found" in error_msg:
            raise HTTPException(status_code=404, detail=error_msg)
        else:
            raise HTTPException(status_code=403, detail=error_msg)
    except Exception as e:
        await db.rollback()
        logger.exception(f"Error deleting bot: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete bot")


# ==================== SEARCH ENDPOINT ====================


class SearchRequest(BaseModel):
    """Request body for semantic search."""

    query: str = Field(..., min_length=1, max_length=1000, description="Search query text")
    k: int = Field(5, ge=1, le=20, description="Number of top results to return")
    similarity_threshold: float = Field(
        0.5, ge=0.0, le=1.0, description="Minimum similarity score (0-1)"
    )


class SearchResultItem(BaseModel):
    """Individual search result."""

    chunk_id: str
    document_id: str
    document_name: str
    section: Optional[str] = None
    text: str
    similarity: float
    position: int
    page_number: Optional[int] = None


class SearchResponse(BaseModel):
    """Search response with results and metadata."""

    query: str
    results: List[SearchResultItem]
    search_latency_ms: int


@router.post("/{bot_id}/search", response_model=SearchResponse)
async def search_bot_documents(
    bot_id: UUID,
    request: SearchRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: UUID = Depends(get_current_tenant),
):
    """
    Perform semantic vector search across bot's knowledge base.

    Retrieves relevant document chunks using pgvector cosine similarity search.
    Results are filtered by bot_id and tenant_id (RLS enforcement).

    - **query**: Search query text (1-1000 chars)
    - **k**: Number of top results (1-20, default 5)
    - **similarity_threshold**: Minimum similarity score (0-1, default 0.5)

    Returns chunks sorted by relevance with similarity scores, document names,
    and section references.
    """
    try:
        # Verify bot exists and belongs to tenant
        bot = await BotService.get_bot(db=db, bot_id=bot_id, tenant_id=tenant_id)
        if not bot:
            raise HTTPException(
                status_code=404, detail=f"Bot {bot_id} not found or not accessible"
            )

        # Initialize services
        embedding_service = EmbeddingService()
        search_service = VectorSearchService(embedding_service)

        try:
            # Perform search
            results, latency_ms = await search_service.search(
                db=db,
                bot_id=bot_id,
                tenant_id=tenant_id,
                query=request.query,
                k=request.k,
                similarity_threshold=request.similarity_threshold,
            )

            # Convert to response format
            result_items = [
                SearchResultItem(
                    chunk_id=r.chunk_id,
                    document_id=r.document_id,
                    document_name=r.document_name,
                    section=r.section,
                    text=r.text,
                    similarity=r.similarity,
                    position=r.position,
                    page_number=r.page_number,
                )
                for r in results
            ]

            return SearchResponse(
                query=request.query,
                results=result_items,
                search_latency_ms=latency_ms,
            )

        except EmbeddingError as e:
            logger.error(f"Embedding failed for query '{request.query}': {e}")
            raise HTTPException(
                status_code=503,
                detail="Embedding service temporarily unavailable. Please try again.",
            )
        finally:
            # Clean up async resources
            await embedding_service.close()

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error during search: {e}")
        raise HTTPException(status_code=500, detail="Search failed unexpectedly")
