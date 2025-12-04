from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from app.core.database import get_db
from app.api.v1.auth import get_current_user, get_current_tenant
from app.schemas.bot import BotCreateRequest, BotUpdateRequest, BotResponse, BotListResponse
from app.services.bot_service import BotService
from app.models.user import User
from app.models.bot import BotStatus
import logging

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
    sort_by: str = Query("name", regex="^(name|created_at)$"),
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
