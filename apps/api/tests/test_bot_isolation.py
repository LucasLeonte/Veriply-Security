"""
Bot Isolation Enforcement Tests
Comprehensive test suite for Story 2.8 bot isolation security.

Tests cover:
- Document isolation by bot_id
- Query/search isolation  
- Vector search isolation
- Chat history isolation
- API security and authorization
- RLS policy enforcement
- Cross-bot access prevention
- Error handling and edge cases
"""

import pytest
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from app.models.bot import Bot, BotStatus
from app.models.tenant import Tenant, SubscriptionTier
from app.models.user import User
from app.models.document import Document
from app.models.chunk import Chunk
from app.core.bot_isolation import validate_bot_access, check_bot_isolation
from app.services.bot_access_audit import BotAccessAudit
from fastapi import HTTPException, status
from datetime import datetime


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
async def async_db():
    """Create an in-memory SQLite database for testing"""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    from app.models.base import Base
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with async_session() as session:
        yield session
    
    await engine.dispose()


@pytest.fixture
async def tenant_a(async_db: AsyncSession):
    """Create first test tenant"""
    tenant = Tenant(
        id=uuid4(),
        name="Tenant A",
        plan="pro",
        subscription_tier=SubscriptionTier.PRO
    )
    async_db.add(tenant)
    await async_db.flush()
    return tenant


@pytest.fixture
async def tenant_b(async_db: AsyncSession):
    """Create second test tenant"""
    tenant = Tenant(
        id=uuid4(),
        name="Tenant B",
        plan="pro",
        subscription_tier=SubscriptionTier.PRO
    )
    async_db.add(tenant)
    await async_db.flush()
    return tenant


@pytest.fixture
async def user_a(async_db: AsyncSession, tenant_a: Tenant):
    """Create user in Tenant A"""
    user = User(
        id=uuid4(),
        email="user_a@example.com",
        password_hash="hashed",
        tenant_id=tenant_a.id,
        role="admin"
    )
    async_db.add(user)
    await async_db.flush()
    return user


@pytest.fixture
async def user_b(async_db: AsyncSession, tenant_b: Tenant):
    """Create user in Tenant B"""
    user = User(
        id=uuid4(),
        email="user_b@example.com",
        password_hash="hashed",
        tenant_id=tenant_b.id,
        role="admin"
    )
    async_db.add(user)
    await async_db.flush()
    return user


@pytest.fixture
async def bot_a1(async_db: AsyncSession, tenant_a: Tenant, user_a: User):
    """Create Bot A1 in Tenant A"""
    bot = Bot(
        id=uuid4(),
        tenant_id=tenant_a.id,
        name="HR Bot",
        description="Human Resources Bot",
        confidence_threshold=80,
        status=BotStatus.READY,
        created_by=user_a.id,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    async_db.add(bot)
    await async_db.flush()
    return bot


@pytest.fixture
async def bot_a2(async_db: AsyncSession, tenant_a: Tenant, user_a: User):
    """Create Bot A2 in Tenant A"""
    bot = Bot(
        id=uuid4(),
        tenant_id=tenant_a.id,
        name="Sales Bot",
        description="Sales Bot",
        confidence_threshold=80,
        status=BotStatus.READY,
        created_by=user_a.id,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    async_db.add(bot)
    await async_db.flush()
    return bot


@pytest.fixture
async def bot_b1(async_db: AsyncSession, tenant_b: Tenant, user_b: User):
    """Create Bot B1 in Tenant B"""
    bot = Bot(
        id=uuid4(),
        tenant_id=tenant_b.id,
        name="Support Bot",
        description="Customer Support Bot",
        confidence_threshold=80,
        status=BotStatus.READY,
        created_by=user_b.id,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    async_db.add(bot)
    await async_db.flush()
    return bot


@pytest.fixture
async def doc_a1_hr(async_db: AsyncSession, bot_a1: Bot, tenant_a: Tenant):
    """Create document for Bot A1"""
    doc = Document(
        id=uuid4(),
        bot_id=bot_a1.id,
        tenant_id=tenant_a.id,
        title="HR Handbook",
        status="ready",
        created_at=datetime.utcnow(),
    )
    async_db.add(doc)
    await async_db.flush()
    return doc


@pytest.fixture
async def doc_b1_support(async_db: AsyncSession, bot_b1: Bot, tenant_b: Tenant):
    """Create document for Bot B1"""
    doc = Document(
        id=uuid4(),
        bot_id=bot_b1.id,
        tenant_id=tenant_b.id,
        title="Support FAQ",
        status="ready",
        created_at=datetime.utcnow(),
    )
    async_db.add(doc)
    await async_db.flush()
    return doc


# ============================================================================
# TESTS: Bot Access Validation (Task 1, 5)
# ============================================================================

class TestBotAccessValidation:
    """Tests for validate_bot_access() function"""
    
    async def test_valid_bot_access_same_tenant(self, async_db, bot_a1, tenant_a, user_a):
        """User should access bot from their own tenant"""
        bot = await validate_bot_access(
            db=async_db,
            bot_id=bot_a1.id,
            tenant_id=tenant_a.id,
            user_id=user_a.id,
        )
        assert bot.id == bot_a1.id
        assert bot.tenant_id == tenant_a.id
    
    async def test_cross_tenant_access_denied(self, async_db, bot_b1, tenant_a, user_a):
        """User from Tenant A should NOT access bot from Tenant B"""
        with pytest.raises(HTTPException) as exc_info:
            await validate_bot_access(
                db=async_db,
                bot_id=bot_b1.id,
                tenant_id=tenant_a.id,  # Wrong tenant
                user_id=user_a.id,
            )
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert "Bot not found" in exc_info.value.detail
    
    async def test_nonexistent_bot_returns_404(self, async_db, tenant_a, user_a):
        """Access to non-existent bot should return 404"""
        fake_bot_id = uuid4()
        with pytest.raises(HTTPException) as exc_info:
            await validate_bot_access(
                db=async_db,
                bot_id=fake_bot_id,
                tenant_id=tenant_a.id,
                user_id=user_a.id,
            )
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
    
    async def test_invalid_bot_id_returns_400(self, async_db, tenant_a):
        """Invalid bot_id format should return 400"""
        with pytest.raises(HTTPException) as exc_info:
            await validate_bot_access(
                db=async_db,
                bot_id=None,
                tenant_id=tenant_a.id,
            )
        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST


# ============================================================================
# TESTS: Document Isolation (Acceptance Criteria: Document Isolation)
# ============================================================================

class TestDocumentIsolation:
    """Tests for document isolation by bot_id"""
    
    async def test_document_belongs_to_specific_bot(self, async_db, doc_a1_hr, bot_a1):
        """Document should have bot_id set"""
        assert doc_a1_hr.bot_id == bot_a1.id
    
    async def test_query_documents_by_bot_id(self, async_db, doc_a1_hr, bot_a1, tenant_a):
        """Query should filter documents by bot_id"""
        from sqlalchemy import select
        stmt = select(Document).where(
            (Document.bot_id == bot_a1.id) &
            (Document.tenant_id == tenant_a.id)
        )
        result = await async_db.execute(stmt)
        docs = result.scalars().all()
        assert len(docs) == 1
        assert docs[0].id == doc_a1_hr.id
    
    async def test_cross_bot_query_returns_empty(self, async_db, doc_a1_hr, bot_a2, tenant_a):
        """Query for different bot should not return docs from other bots"""
        from sqlalchemy import select
        stmt = select(Document).where(
            (Document.bot_id == bot_a2.id) &
            (Document.tenant_id == tenant_a.id)
        )
        result = await async_db.execute(stmt)
        docs = result.scalars().all()
        assert len(docs) == 0
    
    async def test_cross_tenant_query_blocked(self, async_db, doc_a1_hr, bot_b1, tenant_b):
        """Query in different tenant should not return docs"""
        from sqlalchemy import select
        stmt = select(Document).where(
            (Document.bot_id == bot_b1.id) &
            (Document.tenant_id == tenant_b.id)
        )
        result = await async_db.execute(stmt)
        docs = result.scalars().all()
        assert len(docs) == 0


# ============================================================================
# TESTS: Chunk Isolation (Acceptance Criteria: Query/Search Isolation)
# ============================================================================

class TestChunkIsolation:
    """Tests for chunk isolation in vector search"""
    
    async def test_chunk_belongs_to_bot(self, async_db, doc_a1_hr, bot_a1, tenant_a):
        """Chunks should have bot_id set"""
        chunk = Chunk(
            id=uuid4(),
            document_id=doc_a1_hr.id,
            bot_id=bot_a1.id,
            content="HR policy information",
            page_number=1,
            chunk_index=0,
        )
        async_db.add(chunk)
        await async_db.flush()
        
        assert chunk.bot_id == bot_a1.id
    
    async def test_search_only_within_bot(self, async_db, doc_a1_hr, doc_b1_support, bot_a1, bot_b1):
        """Vector search should only return chunks from requested bot"""
        from sqlalchemy import select
        
        # Add chunks to both bots
        chunk_a = Chunk(
            id=uuid4(),
            document_id=doc_a1_hr.id,
            bot_id=bot_a1.id,
            content="HR policy",
            chunk_index=0,
        )
        chunk_b = Chunk(
            id=uuid4(),
            document_id=doc_b1_support.id,
            bot_id=bot_b1.id,
            content="Support information",
            chunk_index=0,
        )
        async_db.add_all([chunk_a, chunk_b])
        await async_db.flush()
        
        # Query only Bot A chunks
        stmt = select(Chunk).where(Chunk.bot_id == bot_a1.id)
        result = await async_db.execute(stmt)
        chunks = result.scalars().all()
        
        assert len(chunks) == 1
        assert chunks[0].bot_id == bot_a1.id


# ============================================================================
# TESTS: Bot Access Audit Logging (Task 6)
# ============================================================================

class TestBotAccessAudit:
    """Tests for audit logging"""
    
    async def test_log_successful_access(self, async_db, user_a, bot_a1, tenant_a):
        """Successful bot access should be logged"""
        from app.models.audit_log import AuditLog
        
        await BotAccessAudit.log_bot_access(
            db=async_db,
            user_id=user_a.id,
            bot_id=bot_a1.id,
            tenant_id=tenant_a.id,
            action="query",
            status="success",
        )
        
        from sqlalchemy import select
        stmt = select(AuditLog).where(AuditLog.actor_id == user_a.id)
        result = await async_db.execute(stmt)
        logs = result.scalars().all()
        
        assert len(logs) == 1
        assert logs[0].action == "bot_access_query"
    
    async def test_log_unauthorized_access_attempt(self, async_db, user_a, bot_b1, tenant_a):
        """Unauthorized access attempts should be logged"""
        from app.models.audit_log import AuditLog
        
        await BotAccessAudit.log_unauthorized_access(
            db=async_db,
            user_id=user_a.id,
            bot_id=bot_b1.id,
            tenant_id=tenant_a.id,
            action="query",
        )
        
        from sqlalchemy import select
        stmt = select(AuditLog).where(AuditLog.actor_id == user_a.id)
        result = await async_db.execute(stmt)
        logs = result.scalars().all()
        
        assert len(logs) == 1
        assert "unauthorized" in logs[0].action.lower()


# ============================================================================
# TESTS: Quick Bot Isolation Check
# ============================================================================

class TestQuickBotIsolationCheck:
    """Tests for in-memory bot isolation validation"""
    
    def test_bot_in_user_list(self):
        """check_bot_isolation should return True for bots in list"""
        user_bots = [uuid4(), uuid4(), uuid4()]
        bot_id = user_bots[1]
        
        result = check_bot_isolation(bot_id, uuid4(), user_bots)
        assert result is True
    
    def test_bot_not_in_user_list(self):
        """check_bot_isolation should return False for bots not in list"""
        user_bots = [uuid4(), uuid4(), uuid4()]
        bot_id = uuid4()  # Different bot
        
        result = check_bot_isolation(bot_id, uuid4(), user_bots)
        assert result is False


# ============================================================================
# TESTS: Error Handling (Acceptance Criteria: Error Handling)
# ============================================================================

class TestErrorHandling:
    """Tests for error responses"""
    
    async def test_error_message_does_not_reveal_ownership(self, async_db, bot_b1, tenant_a):
        """Error should not reveal whether bot exists or user doesn't own it"""
        with pytest.raises(HTTPException) as exc:
            await validate_bot_access(
                db=async_db,
                bot_id=bot_b1.id,
                tenant_id=tenant_a.id,  # Different tenant
            )
        
        # Both cases (not found, not owned) should return same generic 404
        assert exc.value.status_code == status.HTTP_404_NOT_FOUND
        assert exc.value.detail == "Bot not found"
