"""Chat history endpoints for authenticated users."""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user
from app.core.database import get_db
from app.models import Bot, ChatMessageLog
from app.schemas.chat_history import ChatHistoryItem


router = APIRouter(prefix="/bots", tags=["chat-history"])


@router.get("/{bot_id}/history", response_model=List[ChatHistoryItem])
async def get_chat_history(
    bot_id: UUID,
    session_id: Optional[str] = Query(None, alias="session_id"),
    answer_id: Optional[str] = Query(None, alias="answer_id"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Return chat history for a bot scoped to the current tenant/user.

    Filters:
    - session_id: restrict to a specific chat session
    - answer_id: restrict to a specific answer/thread
    Pagination:
    - limit (1-500), offset
    """

    tenant_id = current_user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing tenant context",
        )

    # Ensure bot exists and belongs to the same tenant
    bot = await db.get(Bot, bot_id)
    if not bot:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bot not found")
    if str(bot.tenant_id) != str(tenant_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    stmt = (
        select(ChatMessageLog)
        .where(ChatMessageLog.bot_id == bot_id)
        .where(ChatMessageLog.tenant_id == UUID(str(tenant_id)))
    )

    if session_id:
        stmt = stmt.where(ChatMessageLog.session_id == session_id)
    if answer_id:
        stmt = stmt.where(ChatMessageLog.answer_id == UUID(answer_id))

    stmt = stmt.order_by(ChatMessageLog.created_at.desc()).limit(limit).offset(offset)

    result = await db.execute(stmt)
    records = result.scalars().all()

    # Return in ascending chronological order for readability
    return list(reversed(records))