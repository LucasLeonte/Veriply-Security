import pytest
from uuid import UUID, uuid4
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from app.models.bot import Bot, BotStatus
from app.models.tenant import Tenant, SubscriptionTier
from app.models.user import User
from app.schemas.bot import BotCreateRequest, BotUpdateRequest
from app.services.bot_service import BotService
from datetime import datetime
import asyncio

# Test fixtures
@pytest.fixture
async def async_db():
    """Create an in-memory SQLite database for testing"""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    # Create tables
    from app.models.base import Base
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with async_session() as session:
        yield session
    
    await engine.dispose()

@pytest.fixture
async def test_tenant(async_db: AsyncSession):
    """Create a test tenant"""
    tenant = Tenant(
        id=uuid4(),
        name="Test Org",
        plan="free",
        subscription_tier=SubscriptionTier.FREE
    )
    async_db.add(tenant)
    await async_db.flush()
    return tenant

@pytest.fixture
async def test_user(async_db: AsyncSession, test_tenant: Tenant):
    """Create a test user"""
    user = User(
        id=uuid4(),
        email="test@example.com",
        password_hash="hashed_password",
        tenant_id=test_tenant.id,
        role="admin"
    )
    async_db.add(user)
    await async_db.flush()
    return user

@pytest.fixture
async def test_pro_tenant(async_db: AsyncSession):
    """Create a pro plan test tenant"""
    tenant = Tenant(
        id=uuid4(),
        name="Pro Org",
        plan="pro",
        subscription_tier=SubscriptionTier.PRO
    )
    async_db.add(tenant)
    await async_db.flush()
    return tenant

# Test Bot Creation
@pytest.mark.asyncio
async def test_create_bot_valid(async_db: AsyncSession, test_tenant: Tenant, test_user: User):
    """Test creating a bot with valid data"""
    bot_data = BotCreateRequest(
        name="HR Bot",
        description="Human Resources Bot",
        confidence_threshold=85
    )
    
    bot = await BotService.create_bot(
        db=async_db,
        tenant_id=test_tenant.id,
        user_id=test_user.id,
        bot_data=bot_data,
    )
    
    assert bot.name == "HR Bot"
    assert bot.description == "Human Resources Bot"
    assert bot.confidence_threshold == 85
    assert bot.status == BotStatus.EMPTY
    assert bot.tenant_id == test_tenant.id
    assert bot.created_by == test_user.id

@pytest.mark.asyncio
async def test_create_bot_invalid_name_short(async_db: AsyncSession, test_tenant: Tenant, test_user: User):
    """Test creating a bot with name too short"""
    bot_data = BotCreateRequest(name="A")  # Too short
    
    with pytest.raises(ValueError):
        await BotService.create_bot(
            db=async_db,
            tenant_id=test_tenant.id,
            user_id=test_user.id,
            bot_data=bot_data,
        )

@pytest.mark.asyncio
async def test_create_bot_invalid_name_long(async_db: AsyncSession, test_tenant: Tenant, test_user: User):
    """Test creating a bot with name too long"""
    bot_data = BotCreateRequest(name="A" * 51)  # Too long
    
    with pytest.raises(ValueError):
        await BotService.create_bot(
            db=async_db,
            tenant_id=test_tenant.id,
            user_id=test_user.id,
            bot_data=bot_data,
        )

@pytest.mark.asyncio
async def test_create_bot_invalid_threshold(async_db: AsyncSession, test_tenant: Tenant, test_user: User):
    """Test creating a bot with invalid confidence threshold"""
    # Pydantic validation should catch this, but testing anyway
    with pytest.raises(ValueError):
        bot_data = BotCreateRequest(
            name="Test Bot",
            confidence_threshold=150  # Invalid: > 100
        )

@pytest.mark.asyncio
async def test_create_bot_duplicate_name(async_db: AsyncSession, test_tenant: Tenant, test_user: User):
    """Test creating a bot with duplicate name in same tenant"""
    bot_data1 = BotCreateRequest(name="HR Bot", description="First")
    bot_data2 = BotCreateRequest(name="HR Bot", description="Second")
    
    await BotService.create_bot(
        db=async_db,
        tenant_id=test_tenant.id,
        user_id=test_user.id,
        bot_data=bot_data1,
    )
    
    with pytest.raises(ValueError, match="already exists"):
        await BotService.create_bot(
            db=async_db,
            tenant_id=test_tenant.id,
            user_id=test_user.id,
            bot_data=bot_data2,
        )

@pytest.mark.asyncio
async def test_create_bot_same_name_different_tenant(async_db: AsyncSession, test_tenant: Tenant, test_user: User, test_pro_tenant: Tenant):
    """Test creating bots with same name in different tenants (should succeed)"""
    bot_data = BotCreateRequest(name="HR Bot")
    
    bot1 = await BotService.create_bot(
        db=async_db,
        tenant_id=test_tenant.id,
        user_id=test_user.id,
        bot_data=bot_data,
    )
    
    # Create user for pro tenant
    user2 = User(
        id=uuid4(),
        email="test2@example.com",
        password_hash="hashed",
        tenant_id=test_pro_tenant.id,
        role="admin"
    )
    async_db.add(user2)
    await async_db.flush()
    
    # Should succeed - different tenant
    bot2 = await BotService.create_bot(
        db=async_db,
        tenant_id=test_pro_tenant.id,
        user_id=user2.id,
        bot_data=bot_data,
    )
    
    assert bot1.id != bot2.id
    assert bot1.tenant_id != bot2.tenant_id

@pytest.mark.asyncio
async def test_create_bot_free_tier_limit(async_db: AsyncSession, test_tenant: Tenant, test_user: User):
    """Test bot limit enforcement for free tier (max 5)"""
    # Create 5 bots (should succeed)
    for i in range(5):
        bot_data = BotCreateRequest(name=f"Bot {i}")
        await BotService.create_bot(
            db=async_db,
            tenant_id=test_tenant.id,
            user_id=test_user.id,
            bot_data=bot_data,
        )
    
    # 6th bot should fail
    with pytest.raises(ValueError, match="limit reached"):
        bot_data = BotCreateRequest(name="Bot 6")
        await BotService.create_bot(
            db=async_db,
            tenant_id=test_tenant.id,
            user_id=test_user.id,
            bot_data=bot_data,
        )

@pytest.mark.asyncio
async def test_create_bot_pro_tier_limit(async_db: AsyncSession, test_pro_tenant: Tenant, test_user: User):
    """Test bot limit enforcement for pro tier (max 25)"""
    # Update user's tenant
    test_user.tenant_id = test_pro_tenant.id
    
    # Create 25 bots (should succeed)
    for i in range(25):
        bot_data = BotCreateRequest(name=f"Bot {i}")
        await BotService.create_bot(
            db=async_db,
            tenant_id=test_pro_tenant.id,
            user_id=test_user.id,
            bot_data=bot_data,
        )
    
    # 26th bot should fail
    with pytest.raises(ValueError, match="limit reached"):
        bot_data = BotCreateRequest(name="Bot 26")
        await BotService.create_bot(
            db=async_db,
            tenant_id=test_pro_tenant.id,
            user_id=test_user.id,
            bot_data=bot_data,
        )

# Test Bot Retrieval
@pytest.mark.asyncio
async def test_get_bot(async_db: AsyncSession, test_tenant: Tenant, test_user: User):
    """Test retrieving a bot"""
    bot_data = BotCreateRequest(name="Test Bot")
    created_bot = await BotService.create_bot(
        db=async_db,
        tenant_id=test_tenant.id,
        user_id=test_user.id,
        bot_data=bot_data,
    )
    
    retrieved_bot = await BotService.get_bot(
        db=async_db,
        bot_id=created_bot.id,
        tenant_id=test_tenant.id,
    )
    
    assert retrieved_bot is not None
    assert retrieved_bot.id == created_bot.id
    assert retrieved_bot.name == "Test Bot"

@pytest.mark.asyncio
async def test_get_bot_cross_tenant_denied(async_db: AsyncSession, test_tenant: Tenant, test_pro_tenant: Tenant, test_user: User):
    """Test RLS: cannot retrieve bot from another tenant"""
    bot_data = BotCreateRequest(name="Test Bot")
    created_bot = await BotService.create_bot(
        db=async_db,
        tenant_id=test_tenant.id,
        user_id=test_user.id,
        bot_data=bot_data,
    )
    
    # Try to retrieve with different tenant
    retrieved_bot = await BotService.get_bot(
        db=async_db,
        bot_id=created_bot.id,
        tenant_id=test_pro_tenant.id,  # Different tenant
    )
    
    assert retrieved_bot is None  # Should not be found

# Test Bot List
@pytest.mark.asyncio
async def test_list_bots(async_db: AsyncSession, test_tenant: Tenant, test_user: User):
    """Test listing bots for a tenant"""
    # Create 5 bots
    for i in range(5):
        bot_data = BotCreateRequest(name=f"Bot {i}")
        await BotService.create_bot(
            db=async_db,
            tenant_id=test_tenant.id,
            user_id=test_user.id,
            bot_data=bot_data,
        )
    
    bots, total_count = await BotService.list_bots(
        db=async_db,
        tenant_id=test_tenant.id,
    )
    
    assert len(bots) == 5
    assert total_count == 5

@pytest.mark.asyncio
async def test_list_bots_pagination(async_db: AsyncSession, test_tenant: Tenant, test_user: User):
    """Test pagination in bot list"""
    # Create 25 bots
    for i in range(25):
        bot_data = BotCreateRequest(name=f"Bot {i:02d}")
        await BotService.create_bot(
            db=async_db,
            tenant_id=test_tenant.id,
            user_id=test_user.id,
            bot_data=bot_data,
        )
    
    # Get first page
    page1, total = await BotService.list_bots(
        db=async_db,
        tenant_id=test_tenant.id,
        limit=10,
        offset=0,
    )
    
    assert len(page1) == 10
    assert total == 25
    
    # Get second page
    page2, total = await BotService.list_bots(
        db=async_db,
        tenant_id=test_tenant.id,
        limit=10,
        offset=10,
    )
    
    assert len(page2) == 10
    assert page1[0].name != page2[0].name

@pytest.mark.asyncio
async def test_list_bots_search(async_db: AsyncSession, test_tenant: Tenant, test_user: User):
    """Test search filtering in bot list"""
    bot_names = ["HR Bot", "IT Bot", "Sales Bot", "HR Analytics"]
    for name in bot_names:
        bot_data = BotCreateRequest(name=name)
        await BotService.create_bot(
            db=async_db,
            tenant_id=test_tenant.id,
            user_id=test_user.id,
            bot_data=bot_data,
        )
    
    # Search for "HR"
    bots, total = await BotService.list_bots(
        db=async_db,
        tenant_id=test_tenant.id,
        search="HR",
    )
    
    assert total == 2
    assert all("HR" in bot.name for bot in bots)

@pytest.mark.asyncio
async def test_list_bots_search_case_insensitive(async_db: AsyncSession, test_tenant: Tenant, test_user: User):
    """Test that search is case-insensitive"""
    bot_data = BotCreateRequest(name="HR Bot")
    await BotService.create_bot(
        db=async_db,
        tenant_id=test_tenant.id,
        user_id=test_user.id,
        bot_data=bot_data,
    )
    
    # Search lowercase
    bots, _ = await BotService.list_bots(
        db=async_db,
        tenant_id=test_tenant.id,
        search="hr",
    )
    
    assert len(bots) == 1

@pytest.mark.asyncio
async def test_list_bots_sort_by_name(async_db: AsyncSession, test_tenant: Tenant, test_user: User):
    """Test sorting bots by name"""
    names = ["Zebra", "Alpha", "Beta"]
    for name in names:
        bot_data = BotCreateRequest(name=name)
        await BotService.create_bot(
            db=async_db,
            tenant_id=test_tenant.id,
            user_id=test_user.id,
            bot_data=bot_data,
        )
    
    bots, _ = await BotService.list_bots(
        db=async_db,
        tenant_id=test_tenant.id,
        sort_by="name",
    )
    
    assert [b.name for b in bots] == ["Alpha", "Beta", "Zebra"]

@pytest.mark.asyncio
async def test_list_bots_rls_isolation(async_db: AsyncSession, test_tenant: Tenant, test_pro_tenant: Tenant, test_user: User):
    """Test RLS: list only shows current tenant's bots"""
    # Create bots in first tenant
    for i in range(3):
        bot_data = BotCreateRequest(name=f"Tenant1 Bot {i}")
        await BotService.create_bot(
            db=async_db,
            tenant_id=test_tenant.id,
            user_id=test_user.id,
            bot_data=bot_data,
        )
    
    # List bots for first tenant
    bots, total = await BotService.list_bots(
        db=async_db,
        tenant_id=test_tenant.id,
    )
    
    assert total == 3
    assert all(b.tenant_id == test_tenant.id for b in bots)

# Test Bot Update
@pytest.mark.asyncio
async def test_update_bot_name(async_db: AsyncSession, test_tenant: Tenant, test_user: User):
    """Test updating a bot's name"""
    bot_data = BotCreateRequest(name="Old Name")
    created_bot = await BotService.create_bot(
        db=async_db,
        tenant_id=test_tenant.id,
        user_id=test_user.id,
        bot_data=bot_data,
    )
    
    update_data = BotUpdateRequest(name="New Name")
    updated_bot = await BotService.update_bot(
        db=async_db,
        bot_id=created_bot.id,
        tenant_id=test_tenant.id,
        bot_data=update_data,
    )
    
    assert updated_bot.name == "New Name"

@pytest.mark.asyncio
async def test_update_bot_description(async_db: AsyncSession, test_tenant: Tenant, test_user: User):
    """Test updating a bot's description"""
    bot_data = BotCreateRequest(name="Test Bot", description="Old")
    created_bot = await BotService.create_bot(
        db=async_db,
        tenant_id=test_tenant.id,
        user_id=test_user.id,
        bot_data=bot_data,
    )
    
    update_data = BotUpdateRequest(description="New Description")
    updated_bot = await BotService.update_bot(
        db=async_db,
        bot_id=created_bot.id,
        tenant_id=test_tenant.id,
        bot_data=update_data,
    )
    
    assert updated_bot.description == "New Description"
    assert updated_bot.name == "Test Bot"  # Name unchanged

@pytest.mark.asyncio
async def test_update_bot_threshold(async_db: AsyncSession, test_tenant: Tenant, test_user: User):
    """Test updating a bot's confidence threshold"""
    bot_data = BotCreateRequest(name="Test Bot", confidence_threshold=80)
    created_bot = await BotService.create_bot(
        db=async_db,
        tenant_id=test_tenant.id,
        user_id=test_user.id,
        bot_data=bot_data,
    )
    
    update_data = BotUpdateRequest(confidence_threshold=95)
    updated_bot = await BotService.update_bot(
        db=async_db,
        bot_id=created_bot.id,
        tenant_id=test_tenant.id,
        bot_data=update_data,
    )
    
    assert updated_bot.confidence_threshold == 95

@pytest.mark.asyncio
async def test_update_bot_duplicate_name(async_db: AsyncSession, test_tenant: Tenant, test_user: User):
    """Test updating bot to duplicate name fails"""
    # Create two bots
    bot_data1 = BotCreateRequest(name="Bot 1")
    bot_data2 = BotCreateRequest(name="Bot 2")
    
    bot1 = await BotService.create_bot(
        db=async_db,
        tenant_id=test_tenant.id,
        user_id=test_user.id,
        bot_data=bot_data1,
    )
    
    bot2 = await BotService.create_bot(
        db=async_db,
        tenant_id=test_tenant.id,
        user_id=test_user.id,
        bot_data=bot_data2,
    )
    
    # Try to rename bot2 to bot1's name
    update_data = BotUpdateRequest(name="Bot 1")
    
    with pytest.raises(ValueError, match="already exists"):
        await BotService.update_bot(
            db=async_db,
            bot_id=bot2.id,
            tenant_id=test_tenant.id,
            bot_data=update_data,
        )

@pytest.mark.asyncio
async def test_update_bot_not_found(async_db: AsyncSession, test_tenant: Tenant):
    """Test updating non-existent bot fails"""
    update_data = BotUpdateRequest(name="New Name")
    
    with pytest.raises(ValueError, match="not found"):
        await BotService.update_bot(
            db=async_db,
            bot_id=uuid4(),
            tenant_id=test_tenant.id,
            bot_data=update_data,
        )

@pytest.mark.asyncio
async def test_update_bot_cross_tenant_denied(async_db: AsyncSession, test_tenant: Tenant, test_pro_tenant: Tenant, test_user: User):
    """Test RLS: cannot update bot from another tenant"""
    bot_data = BotCreateRequest(name="Test Bot")
    created_bot = await BotService.create_bot(
        db=async_db,
        tenant_id=test_tenant.id,
        user_id=test_user.id,
        bot_data=bot_data,
    )
    
    update_data = BotUpdateRequest(name="Hacked Name")
    
    with pytest.raises(ValueError, match="not found"):
        await BotService.update_bot(
            db=async_db,
            bot_id=created_bot.id,
            tenant_id=test_pro_tenant.id,  # Different tenant
            bot_data=update_data,
        )
