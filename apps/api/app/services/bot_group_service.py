"""Bot service with group scoping and provenance."""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from uuid import UUID
from datetime import datetime
import logging

from app.models import Bot, BotStatus, Group

logger = logging.getLogger(__name__)


class BotGroupService:
    """Service for group-scoped bot operations."""

    @staticmethod
    async def create_bot(
        db: AsyncSession,
        tenant_id: UUID,
        group_id: UUID,
        user_id: UUID,
        name: str,
        description: str | None = None,
        confidence_threshold: int = 80,
    ) -> Bot:
        """
        Create a new bot in a group.
        
        Args:
            db: Database session
            tenant_id: Tenant ID
            group_id: Group ID
            user_id: User ID (creator)
            name: Bot name (unique per group)
            description: Optional description
            confidence_threshold: Confidence threshold 0-100
            
        Returns:
            Created Bot object
            
        Raises:
            ValueError: If group not found or bot name exists in group
        """
        # Verify group exists
        group = await db.scalar(
            select(Group).where(
                (Group.id == group_id) & (Group.tenant_id == tenant_id)
            )
        )
        if not group:
            raise ValueError(f"Group {group_id} not found")

        # Check for duplicate name in group
        existing = await db.scalar(
            select(Bot).where(
                (Bot.group_id == group_id)
                & (Bot.tenant_id == tenant_id)
                & (Bot.name == name)
            )
        )
        if existing:
            raise ValueError(f"Bot name '{name}' already exists in this group")

        # Create bot
        new_bot = Bot(
            tenant_id=tenant_id,
            group_id=group_id,
            name=name,
            description=description,
            confidence_threshold=confidence_threshold,
            status=BotStatus.EMPTY,
            created_by=user_id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(new_bot)
        await db.flush()

        logger.info(
            f"Bot created: id={new_bot.id}, group_id={group_id}, "
            f"tenant_id={tenant_id}, name={name}"
        )
        return new_bot

    @staticmethod
    async def get_bot(
        db: AsyncSession, bot_id: UUID, group_id: UUID, tenant_id: UUID
    ) -> Bot | None:
        """Get a bot with group and tenant isolation."""
        return await db.scalar(
            select(Bot).where(
                (Bot.id == bot_id)
                & (Bot.group_id == group_id)
                & (Bot.tenant_id == tenant_id)
            )
        )

    @staticmethod
    async def list_group_bots(
        db: AsyncSession,
        group_id: UUID,
        tenant_id: UUID,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[Bot], int]:
        """List all bots in a group with pagination."""
        # Count query
        total = await db.scalar(
            select(func.count(Bot.id)).where(
                (Bot.group_id == group_id) & (Bot.tenant_id == tenant_id)
            )
        )

        # List query
        bots = list(
            await db.scalars(
                select(Bot)
                .where(
                    (Bot.group_id == group_id) & (Bot.tenant_id == tenant_id)
                )
                .order_by(Bot.created_at.desc())
                .limit(limit)
                .offset(offset)
            )
        )

        return bots, total or 0

    @staticmethod
    async def update_bot(
        db: AsyncSession,
        bot_id: UUID,
        group_id: UUID,
        tenant_id: UUID,
        name: str | None = None,
        description: str | None = None,
        confidence_threshold: int | None = None,
        avatar_url: str | None = None,
        welcome_message: str | None = None,
        is_public: bool | None = None,
        is_active: bool | None = None,
    ) -> Bot:
        """Update bot details."""
        bot = await BotGroupService.get_bot(db, bot_id, group_id, tenant_id)
        if not bot:
            raise ValueError(f"Bot {bot_id} not found")

        if name:
            # Check for duplicate name in group
            existing = await db.scalar(
                select(Bot).where(
                    (Bot.group_id == group_id)
                    & (Bot.tenant_id == tenant_id)
                    & (Bot.name == name)
                    & (Bot.id != bot_id)
                )
            )
            if existing:
                raise ValueError(f"Bot name '{name}' already exists in this group")
            bot.name = name

        if description is not None:
            bot.description = description

        if confidence_threshold is not None:
            bot.confidence_threshold = confidence_threshold

        if avatar_url is not None:
            bot.avatar_url = avatar_url

        if welcome_message is not None:
            bot.welcome_message = welcome_message

        if is_public is not None:
            bot.is_public = is_public
        
        if is_active is not None:
            bot.is_active = is_active

        bot.updated_at = datetime.utcnow()
        await db.flush()
        logger.info(f"Bot updated: id={bot_id}, group_id={group_id}")
        return bot

    @staticmethod
    async def delete_bot(
        db: AsyncSession, bot_id: UUID, group_id: UUID, tenant_id: UUID
    ) -> bool:
        """
        Delete a bot from a group.
        
        Note: Documents and chunks in the group KB are NOT deleted
        (they may be referenced by other bots in the group).
        """
        bot = await BotGroupService.get_bot(db, bot_id, group_id, tenant_id)
        if not bot:
            raise ValueError(f"Bot {bot_id} not found")

        await db.delete(bot)
        await db.flush()
        logger.info(f"Bot deleted: id={bot_id}, group_id={group_id}")
        return True

    @staticmethod
    async def set_bot_status(
        db: AsyncSession,
        bot_id: UUID,
        group_id: UUID,
        tenant_id: UUID,
        status: BotStatus,
    ) -> Bot:
        """Update bot processing status."""
        bot = await BotGroupService.get_bot(db, bot_id, group_id, tenant_id)
        if not bot:
            raise ValueError(f"Bot {bot_id} not found")

        bot.status = status
        bot.updated_at = datetime.utcnow()
        await db.flush()
        logger.info(f"Bot status updated: id={bot_id}, status={status.value}")
        return bot
