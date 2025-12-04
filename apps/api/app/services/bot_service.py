from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from uuid import UUID
from app.models.bot import Bot, BotStatus
from app.models.tenant import Tenant, SubscriptionTier
from app.schemas.bot import BotCreateRequest, BotUpdateRequest
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# Bot tier limits
BOT_LIMITS = {
    SubscriptionTier.FREE: 5,
    SubscriptionTier.PRO: 25,
    SubscriptionTier.ENTERPRISE: None,  # Unlimited
}

class BotService:
    """Service for bot management operations"""
    
    @staticmethod
    async def create_bot(
        db: AsyncSession,
        tenant_id: UUID,
        user_id: UUID,
        bot_data: BotCreateRequest,
    ) -> Bot:
        """
        Create a new bot for a tenant.
        
        Args:
            db: Database session
            tenant_id: Tenant ID
            user_id: User ID (creator)
            bot_data: Bot creation request data
            
        Returns:
            Created Bot object
            
        Raises:
            ValueError: If tenant not found, bot limit exceeded, or name already exists
        """
        # Get tenant and check subscription tier
        tenant = await db.get(Tenant, tenant_id)
        if not tenant:
            raise ValueError(f"Tenant {tenant_id} not found")
        
        # Check bot limit
        bot_limit = BOT_LIMITS.get(tenant.subscription_tier, 5)
        if bot_limit is not None:  # None = unlimited
            bot_count = await BotService._get_bot_count(db, tenant_id)
            if bot_count >= bot_limit:
                raise ValueError(f"Bot limit reached: {bot_limit}")
        
        # Check for duplicate name within tenant
        existing = await BotService._get_bot_by_name(db, tenant_id, bot_data.name)
        if existing:
            raise ValueError(f"Bot name '{bot_data.name}' already exists in this organization")
        
        # Create new bot
        new_bot = Bot(
            id=__import__('uuid').uuid4(),
            tenant_id=tenant_id,
            name=bot_data.name,
            description=bot_data.description,
            confidence_threshold=bot_data.confidence_threshold,
            status=BotStatus.EMPTY,
            created_by=user_id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        
        db.add(new_bot)
        await db.flush()
        
        logger.info(f"Bot created: id={new_bot.id}, tenant_id={tenant_id}, name={bot_data.name}")
        
        return new_bot
    
    @staticmethod
    async def get_bot(db: AsyncSession, bot_id: UUID, tenant_id: UUID) -> Bot | None:
        """
        Get a bot by ID with tenant isolation (RLS).
        
        Args:
            db: Database session
            bot_id: Bot ID
            tenant_id: Tenant ID (for RLS check)
            
        Returns:
            Bot object or None if not found
        """
        stmt = select(Bot).where(Bot.id == bot_id, Bot.tenant_id == tenant_id)
        result = await db.execute(stmt)
        return result.scalars().first()
    
    @staticmethod
    async def list_bots(
        db: AsyncSession,
        tenant_id: UUID,
        limit: int = 20,
        offset: int = 0,
        search: str | None = None,
        sort_by: str = "name",
    ) -> tuple[list[Bot], int]:
        """
        List bots for a tenant with pagination and filtering.
        
        Args:
            db: Database session
            tenant_id: Tenant ID
            limit: Page size
            offset: Page offset
            search: Filter by name (case-insensitive)
            sort_by: Sort field (name or created_at)
            
        Returns:
            Tuple of (bots list, total count)
        """
        # Base query
        query = select(Bot).where(Bot.tenant_id == tenant_id)
        
        # Apply search filter
        if search:
            query = query.where(Bot.name.ilike(f"%{search}%"))
        
        # Apply sorting
        if sort_by == "created_at":
            query = query.order_by(Bot.created_at.desc())
        else:  # Default to name
            query = query.order_by(Bot.name.asc())
        
        # Get total count
        count_query = select(func.count(Bot.id)).where(Bot.tenant_id == tenant_id)
        if search:
            count_query = count_query.where(Bot.name.ilike(f"%{search}%"))
        
        count_result = await db.execute(count_query)
        total_count = count_result.scalar() or 0
        
        # Apply pagination
        query = query.limit(limit).offset(offset)
        
        # Execute query
        result = await db.execute(query)
        bots = result.scalars().all()
        
        return bots, total_count
    
    @staticmethod
    async def update_bot(
        db: AsyncSession,
        bot_id: UUID,
        tenant_id: UUID,
        bot_data: BotUpdateRequest,
    ) -> Bot:
        """
        Update a bot with tenant isolation (RLS).
        
        Args:
            db: Database session
            bot_id: Bot ID
            tenant_id: Tenant ID (for RLS check)
            bot_data: Update request data
            
        Returns:
            Updated Bot object
            
        Raises:
            ValueError: If bot not found, name already exists, or other validation fails
        """
        # Get bot with RLS check
        bot = await BotService.get_bot(db, bot_id, tenant_id)
        if not bot:
            raise ValueError(f"Bot {bot_id} not found or access denied")
        
        # Check for duplicate name if name is being updated
        if bot_data.name and bot_data.name != bot.name:
            existing = await BotService._get_bot_by_name(db, tenant_id, bot_data.name)
            if existing:
                raise ValueError(f"Bot name '{bot_data.name}' already exists in this organization")
            bot.name = bot_data.name
        
        # Update other fields
        if bot_data.description is not None:
            bot.description = bot_data.description
        
        if bot_data.confidence_threshold is not None:
            bot.confidence_threshold = bot_data.confidence_threshold
        
        bot.updated_at = datetime.utcnow()
        
        await db.flush()
        
        logger.info(f"Bot updated: id={bot_id}, tenant_id={tenant_id}")
        
        return bot
    
    @staticmethod
    async def _get_bot_by_name(db: AsyncSession, tenant_id: UUID, name: str) -> Bot | None:
        """Get a bot by name within a tenant"""
        stmt = select(Bot).where(Bot.tenant_id == tenant_id, Bot.name.ilike(name))
        result = await db.execute(stmt)
        return result.scalars().first()
    
    @staticmethod
    async def _get_bot_count(db: AsyncSession, tenant_id: UUID) -> int:
        """Get the count of bots for a tenant"""
        stmt = select(func.count(Bot.id)).where(Bot.tenant_id == tenant_id)
        result = await db.execute(stmt)
        return result.scalar() or 0
    
    @staticmethod
    def get_bot_limit(tier: SubscriptionTier) -> int | None:
        """Get bot limit for a subscription tier"""
        return BOT_LIMITS.get(tier, 5)
