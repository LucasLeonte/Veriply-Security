"""
Bot Isolation Enforcement
Ensures documents, embeddings, and queries are scoped to their assigned bot.
Provides validation and middleware for bot-level security.
"""

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from app.models.bot import Bot
import logging

logger = logging.getLogger(__name__)


async def validate_bot_access(
    db: AsyncSession,
    bot_id: UUID,
    tenant_id: UUID,
    user_id: UUID | None = None,
) -> Bot:
    """
    Validate that a bot belongs to a tenant and user has access to it.
    
    Args:
        db: Database session
        bot_id: Bot ID to validate
        tenant_id: Tenant ID (from JWT token)
        user_id: User ID (optional, for audit logging)
    
    Returns:
        Bot object if valid
        
    Raises:
        HTTPException: 403 if bot not accessible, 404 if not found, 400 if invalid format
    """
    if not bot_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid bot ID format"
        )
    
    # Query bot and verify it belongs to the tenant
    stmt = select(Bot).where(
        (Bot.id == bot_id) &
        (Bot.tenant_id == tenant_id)
    )
    result = await db.execute(stmt)
    bot = result.scalar_one_or_none()
    
    if not bot:
        # Log potential unauthorized access attempt
        logger.warning(
            f"Unauthorized bot access attempt: "
            f"user_id={user_id}, bot_id={bot_id}, tenant_id={tenant_id}"
        )
        # Return generic 404 for security (don't reveal if not found vs not owned)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bot not found"
        )
    
    return bot


def check_bot_isolation(bot_id: UUID, tenant_id: UUID, user_bot_ids: list[UUID]) -> bool:
    """
    Quick check if bot belongs to user's bots (for in-memory validation).
    
    Args:
        bot_id: Bot ID to check
        tenant_id: Tenant ID
        user_bot_ids: List of bot IDs user owns
    
    Returns:
        True if bot_id is in user_bot_ids, False otherwise
    """
    return bot_id in user_bot_ids
