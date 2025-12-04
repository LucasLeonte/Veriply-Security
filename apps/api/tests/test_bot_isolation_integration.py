"""
Bot Isolation Integration Tests
End-to-end tests verifying bot isolation enforcement across API and database layers.

Tests the complete flow:
1. User creates multiple bots
2. User creates documents for each bot
3. User performs queries and verifies isolation
4. System prevents cross-bot access
5. Audit trail is maintained
"""

import pytest
from uuid import uuid4
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from datetime import datetime
import json

# Mock FastAPI app for testing
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.responses import JSONResponse

# Import models and services
from app.models.bot import Bot, BotStatus
from app.models.tenant import Tenant, SubscriptionTier
from app.models.user import User
from app.models.document import Document
from app.models.chunk import Chunk
from app.models.embedding import Embedding
from app.models.audit_log import AuditLog
from app.core.bot_isolation import validate_bot_access, check_bot_isolation
from app.services.bot_access_audit import BotAccessAudit


# ============================================================================
# TEST FIXTURES - Database Setup
# ============================================================================

@pytest.fixture
async def async_engine():
    """Create in-memory database engine for testing"""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async_session_local = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    from app.models.base import Base
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    await engine.dispose()


@pytest.fixture
async def async_db(async_engine):
    """Create database session for test"""
    async_session_local = async_sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session_local() as session:
        yield session


@pytest.fixture
async def setup_multi_tenant_scenario(async_db: AsyncSession):
    """
    Set up complete multi-tenant scenario:
    - 2 tenants (Company A, Company B)
    - 2 users per tenant
    - 2 bots per tenant (4 total bots)
    - Documents and chunks for each bot
    """
    # Create Tenants
    tenant_a = Tenant(
        id=uuid4(),
        name="Company A",
        plan="pro",
        subscription_tier=SubscriptionTier.PRO
    )
    tenant_b = Tenant(
        id=uuid4(),
        name="Company B",
        plan="pro",
        subscription_tier=SubscriptionTier.PRO
    )
    async_db.add_all([tenant_a, tenant_b])
    await async_db.flush()
    
    # Create Users
    user_a1 = User(
        id=uuid4(),
        email="alice@companya.com",
        password_hash="hashed",
        tenant_id=tenant_a.id,
        role="admin"
    )
    user_a2 = User(
        id=uuid4(),
        email="bob@companya.com",
        password_hash="hashed",
        tenant_id=tenant_a.id,
        role="user"
    )
    user_b1 = User(
        id=uuid4(),
        email="charlie@companyb.com",
        password_hash="hashed",
        tenant_id=tenant_b.id,
        role="admin"
    )
    user_b2 = User(
        id=uuid4(),
        email="diana@companyb.com",
        password_hash="hashed",
        tenant_id=tenant_b.id,
        role="user"
    )
    async_db.add_all([user_a1, user_a2, user_b1, user_b2])
    await async_db.flush()
    
    # Create Bots for Tenant A
    bot_a_hr = Bot(
        id=uuid4(),
        tenant_id=tenant_a.id,
        name="HR Bot",
        description="Human Resources assistance",
        confidence_threshold=80,
        status=BotStatus.READY,
        created_by=user_a1.id,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    bot_a_sales = Bot(
        id=uuid4(),
        tenant_id=tenant_a.id,
        name="Sales Bot",
        description="Sales support",
        confidence_threshold=80,
        status=BotStatus.READY,
        created_by=user_a1.id,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    
    # Create Bots for Tenant B
    bot_b_support = Bot(
        id=uuid4(),
        tenant_id=tenant_b.id,
        name="Support Bot",
        description="Customer support",
        confidence_threshold=80,
        status=BotStatus.READY,
        created_by=user_b1.id,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    bot_b_finance = Bot(
        id=uuid4(),
        tenant_id=tenant_b.id,
        name="Finance Bot",
        description="Finance assistance",
        confidence_threshold=80,
        status=BotStatus.READY,
        created_by=user_b1.id,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    async_db.add_all([bot_a_hr, bot_a_sales, bot_b_support, bot_b_finance])
    await async_db.flush()
    
    # Create Documents for each bot
    doc_a_hr_handbook = Document(
        id=uuid4(),
        bot_id=bot_a_hr.id,
        tenant_id=tenant_a.id,
        title="HR Handbook",
        status="ready",
        created_at=datetime.utcnow(),
    )
    doc_a_hr_policies = Document(
        id=uuid4(),
        bot_id=bot_a_hr.id,
        tenant_id=tenant_a.id,
        title="HR Policies",
        status="ready",
        created_at=datetime.utcnow(),
    )
    doc_a_sales_commission = Document(
        id=uuid4(),
        bot_id=bot_a_sales.id,
        tenant_id=tenant_a.id,
        title="Commission Structure",
        status="ready",
        created_at=datetime.utcnow(),
    )
    
    doc_b_support_faq = Document(
        id=uuid4(),
        bot_id=bot_b_support.id,
        tenant_id=tenant_b.id,
        title="Support FAQ",
        status="ready",
        created_at=datetime.utcnow(),
    )
    doc_b_finance_guide = Document(
        id=uuid4(),
        bot_id=bot_b_finance.id,
        tenant_id=tenant_b.id,
        title="Finance Guide",
        status="ready",
        created_at=datetime.utcnow(),
    )
    
    async_db.add_all([
        doc_a_hr_handbook, doc_a_hr_policies, doc_a_sales_commission,
        doc_b_support_faq, doc_b_finance_guide
    ])
    await async_db.flush()
    
    # Create Chunks for each document
    chunk_a_hr_1 = Chunk(
        id=uuid4(),
        document_id=doc_a_hr_handbook.id,
        bot_id=bot_a_hr.id,
        content="HR policies and procedures",
        page_number=1,
        chunk_index=0,
    )
    chunk_a_hr_2 = Chunk(
        id=uuid4(),
        document_id=doc_a_hr_policies.id,
        bot_id=bot_a_hr.id,
        content="Leave policies and guidelines",
        page_number=1,
        chunk_index=0,
    )
    chunk_a_sales_1 = Chunk(
        id=uuid4(),
        document_id=doc_a_sales_commission.id,
        bot_id=bot_a_sales.id,
        content="Commission rates and tiers",
        page_number=1,
        chunk_index=0,
    )
    chunk_b_support_1 = Chunk(
        id=uuid4(),
        document_id=doc_b_support_faq.id,
        bot_id=bot_b_support.id,
        content="Frequently asked questions",
        page_number=1,
        chunk_index=0,
    )
    chunk_b_finance_1 = Chunk(
        id=uuid4(),
        document_id=doc_b_finance_guide.id,
        bot_id=bot_b_finance.id,
        content="Financial policies and procedures",
        page_number=1,
        chunk_index=0,
    )
    
    async_db.add_all([
        chunk_a_hr_1, chunk_a_hr_2, chunk_a_sales_1,
        chunk_b_support_1, chunk_b_finance_1
    ])
    await async_db.flush()
    
    return {
        "tenants": {
            "a": tenant_a,
            "b": tenant_b,
        },
        "users": {
            "a1": user_a1,
            "a2": user_a2,
            "b1": user_b1,
            "b2": user_b2,
        },
        "bots": {
            "a_hr": bot_a_hr,
            "a_sales": bot_a_sales,
            "b_support": bot_b_support,
            "b_finance": bot_b_finance,
        },
        "documents": {
            "a_hr_handbook": doc_a_hr_handbook,
            "a_hr_policies": doc_a_hr_policies,
            "a_sales_commission": doc_a_sales_commission,
            "b_support_faq": doc_b_support_faq,
            "b_finance_guide": doc_b_finance_guide,
        },
        "chunks": {
            "a_hr_1": chunk_a_hr_1,
            "a_hr_2": chunk_a_hr_2,
            "a_sales_1": chunk_a_sales_1,
            "b_support_1": chunk_b_support_1,
            "b_finance_1": chunk_b_finance_1,
        }
    }


# ============================================================================
# TEST SUITE 1: Bot Access Validation
# ============================================================================

class TestBotAccessValidationIntegration:
    """Integration tests for bot access validation"""
    
    async def test_user_can_access_own_bot(self, async_db, setup_multi_tenant_scenario):
        """User A1 should access HR Bot in Tenant A"""
        scenario = setup_multi_tenant_scenario
        
        bot = await validate_bot_access(
            db=async_db,
            bot_id=scenario["bots"]["a_hr"].id,
            tenant_id=scenario["tenants"]["a"].id,
            user_id=scenario["users"]["a1"].id,
        )
        
        assert bot.id == scenario["bots"]["a_hr"].id
        assert bot.tenant_id == scenario["tenants"]["a"].id
        assert bot.name == "HR Bot"
    
    async def test_user_cannot_access_cross_tenant_bot(self, async_db, setup_multi_tenant_scenario):
        """User A1 should NOT access Bot from Tenant B"""
        from fastapi import HTTPException
        scenario = setup_multi_tenant_scenario
        
        with pytest.raises(HTTPException) as exc_info:
            await validate_bot_access(
                db=async_db,
                bot_id=scenario["bots"]["b_support"].id,
                tenant_id=scenario["tenants"]["a"].id,  # Wrong tenant
                user_id=scenario["users"]["a1"].id,
            )
        
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
    
    async def test_user_can_access_any_bot_in_same_tenant(self, async_db, setup_multi_tenant_scenario):
        """User A1 can access both HR Bot and Sales Bot in Tenant A"""
        scenario = setup_multi_tenant_scenario
        
        # Access HR Bot
        bot_hr = await validate_bot_access(
            db=async_db,
            bot_id=scenario["bots"]["a_hr"].id,
            tenant_id=scenario["tenants"]["a"].id,
            user_id=scenario["users"]["a1"].id,
        )
        assert bot_hr.id == scenario["bots"]["a_hr"].id
        
        # Access Sales Bot
        bot_sales = await validate_bot_access(
            db=async_db,
            bot_id=scenario["bots"]["a_sales"].id,
            tenant_id=scenario["tenants"]["a"].id,
            user_id=scenario["users"]["a1"].id,
        )
        assert bot_sales.id == scenario["bots"]["a_sales"].id


# ============================================================================
# TEST SUITE 2: Document Isolation
# ============================================================================

class TestDocumentIsolationIntegration:
    """Integration tests for document isolation across bots and tenants"""
    
    async def test_query_only_returns_bot_documents(self, async_db, setup_multi_tenant_scenario):
        """Querying HR Bot documents only returns HR Bot documents"""
        from sqlalchemy import select
        scenario = setup_multi_tenant_scenario
        
        stmt = select(Document).where(
            (Document.bot_id == scenario["bots"]["a_hr"].id) &
            (Document.tenant_id == scenario["tenants"]["a"].id)
        )
        result = await async_db.execute(stmt)
        docs = result.scalars().all()
        
        # Should only return HR Bot documents (2)
        assert len(docs) == 2
        assert all(doc.bot_id == scenario["bots"]["a_hr"].id for doc in docs)
        doc_titles = {doc.title for doc in docs}
        assert doc_titles == {"HR Handbook", "HR Policies"}
    
    async def test_cross_bot_query_returns_empty(self, async_db, setup_multi_tenant_scenario):
        """Querying Sales Bot doesn't return HR Bot documents"""
        from sqlalchemy import select
        scenario = setup_multi_tenant_scenario
        
        # Query for Sales Bot
        stmt = select(Document).where(
            (Document.bot_id == scenario["bots"]["a_sales"].id) &
            (Document.tenant_id == scenario["tenants"]["a"].id)
        )
        result = await async_db.execute(stmt)
        docs = result.scalars().all()
        
        # Should only return Sales Bot documents (1)
        assert len(docs) == 1
        assert docs[0].title == "Commission Structure"
        assert docs[0].bot_id == scenario["bots"]["a_sales"].id
    
    async def test_cross_tenant_query_returns_empty(self, async_db, setup_multi_tenant_scenario):
        """Querying Tenant A documents doesn't return Tenant B documents"""
        from sqlalchemy import select
        scenario = setup_multi_tenant_scenario
        
        stmt = select(Document).where(
            Document.tenant_id == scenario["tenants"]["a"].id
        )
        result = await async_db.execute(stmt)
        docs_a = result.scalars().all()
        
        stmt = select(Document).where(
            Document.tenant_id == scenario["tenants"]["b"].id
        )
        result = await async_db.execute(stmt)
        docs_b = result.scalars().all()
        
        # Tenant A has 3 docs, Tenant B has 2 docs
        assert len(docs_a) == 3
        assert len(docs_b) == 2
        
        # No overlap
        tenant_a_ids = {doc.id for doc in docs_a}
        tenant_b_ids = {doc.id for doc in docs_b}
        assert len(tenant_a_ids & tenant_b_ids) == 0


# ============================================================================
# TEST SUITE 3: Chunk/Search Isolation
# ============================================================================

class TestChunkIsolationIntegration:
    """Integration tests for chunk isolation in vector search"""
    
    async def test_search_only_within_bot(self, async_db, setup_multi_tenant_scenario):
        """Vector search returns only chunks from requested bot"""
        from sqlalchemy import select
        scenario = setup_multi_tenant_scenario
        
        # Search in HR Bot - should find 2 chunks
        stmt = select(Chunk).where(Chunk.bot_id == scenario["bots"]["a_hr"].id)
        result = await async_db.execute(stmt)
        hr_chunks = result.scalars().all()
        
        assert len(hr_chunks) == 2
        assert all(chunk.bot_id == scenario["bots"]["a_hr"].id for chunk in hr_chunks)
        
        # Search in Sales Bot - should find 1 chunk
        stmt = select(Chunk).where(Chunk.bot_id == scenario["bots"]["a_sales"].id)
        result = await async_db.execute(stmt)
        sales_chunks = result.scalars().all()
        
        assert len(sales_chunks) == 1
        assert sales_chunks[0].bot_id == scenario["bots"]["a_sales"].id
    
    async def test_cross_tenant_search_isolation(self, async_db, setup_multi_tenant_scenario):
        """Search in Tenant A doesn't find chunks from Tenant B"""
        from sqlalchemy import select
        scenario = setup_multi_tenant_scenario
        
        # Count total chunks in Tenant A
        stmt = select(Chunk).where(
            Chunk.bot_id.in_([
                scenario["bots"]["a_hr"].id,
                scenario["bots"]["a_sales"].id
            ])
        )
        result = await async_db.execute(stmt)
        chunks_a = result.scalars().all()
        
        # Count total chunks in Tenant B
        stmt = select(Chunk).where(
            Chunk.bot_id.in_([
                scenario["bots"]["b_support"].id,
                scenario["bots"]["b_finance"].id
            ])
        )
        result = await async_db.execute(stmt)
        chunks_b = result.scalars().all()
        
        # Tenant A has 3 chunks, Tenant B has 2 chunks
        assert len(chunks_a) == 3
        assert len(chunks_b) == 2
        
        # No overlap
        chunk_a_ids = {chunk.id for chunk in chunks_a}
        chunk_b_ids = {chunk.id for chunk in chunks_b}
        assert len(chunk_a_ids & chunk_b_ids) == 0


# ============================================================================
# TEST SUITE 4: Audit Logging
# ============================================================================

class TestAuditLoggingIntegration:
    """Integration tests for audit logging of bot access"""
    
    async def test_successful_access_logged(self, async_db, setup_multi_tenant_scenario):
        """Successful bot access is logged"""
        scenario = setup_multi_tenant_scenario
        
        await BotAccessAudit.log_bot_access(
            db=async_db,
            user_id=scenario["users"]["a1"].id,
            bot_id=scenario["bots"]["a_hr"].id,
            tenant_id=scenario["tenants"]["a"].id,
            action="query",
            status="success",
            ip_address="192.168.1.1",
        )
        
        from sqlalchemy import select
        stmt = select(AuditLog).where(AuditLog.actor_id == scenario["users"]["a1"].id)
        result = await async_db.execute(stmt)
        logs = result.scalars().all()
        
        assert len(logs) == 1
        assert logs[0].action == "bot_access_query"
        assert logs[0].tenant_id == scenario["tenants"]["a"].id
        
        # Verify details
        details = json.loads(logs[0].details)
        assert details["action"] == "query"
        assert details["status"] == "success"
        assert details["ip_address"] == "192.168.1.1"
    
    async def test_unauthorized_access_logged(self, async_db, setup_multi_tenant_scenario):
        """Unauthorized access attempts are logged"""
        scenario = setup_multi_tenant_scenario
        
        await BotAccessAudit.log_unauthorized_access(
            db=async_db,
            user_id=scenario["users"]["a1"].id,
            bot_id=scenario["bots"]["b_support"].id,  # Bot from other tenant
            tenant_id=scenario["tenants"]["a"].id,
            action="query",
            ip_address="192.168.1.2",
        )
        
        from sqlalchemy import select
        stmt = select(AuditLog).where(AuditLog.actor_id == scenario["users"]["a1"].id)
        result = await async_db.execute(stmt)
        logs = result.scalars().all()
        
        assert len(logs) == 1
        assert "unauthorized" in logs[0].action.lower()
        
        details = json.loads(logs[0].details)
        assert details["action"] == "query"
        assert details["status"] == "failed"
    
    async def test_multiple_access_attempts_logged(self, async_db, setup_multi_tenant_scenario):
        """Multiple access attempts by same user are all logged"""
        scenario = setup_multi_tenant_scenario
        
        # Log 3 successful accesses
        for i, bot_key in enumerate(["a_hr", "a_sales"]):
            await BotAccessAudit.log_bot_access(
                db=async_db,
                user_id=scenario["users"]["a1"].id,
                bot_id=scenario["bots"][bot_key].id,
                tenant_id=scenario["tenants"]["a"].id,
                action="query",
                status="success",
            )
        
        # Log 1 unauthorized attempt
        await BotAccessAudit.log_unauthorized_access(
            db=async_db,
            user_id=scenario["users"]["a1"].id,
            bot_id=scenario["bots"]["b_support"].id,
            tenant_id=scenario["tenants"]["a"].id,
            action="query",
        )
        
        from sqlalchemy import select
        stmt = select(AuditLog).where(AuditLog.actor_id == scenario["users"]["a1"].id)
        result = await async_db.execute(stmt)
        logs = result.scalars().all()
        
        # Should have 3 logs
        assert len(logs) == 3
        
        # 2 successful, 1 unauthorized
        success_logs = [log for log in logs if "unauthorized" not in log.action.lower()]
        fail_logs = [log for log in logs if "unauthorized" in log.action.lower()]
        
        assert len(success_logs) == 2
        assert len(fail_logs) == 1


# ============================================================================
# TEST SUITE 5: End-to-End Security Scenarios
# ============================================================================

class TestEndToEndSecurityScenarios:
    """Complete end-to-end security test scenarios"""
    
    async def test_complete_isolation_scenario(self, async_db, setup_multi_tenant_scenario):
        """
        Complete scenario:
        1. User A1 accesses HR Bot documents → Success
        2. User A1 tries to access Tenant B's Support Bot → Denied
        3. All actions are logged
        4. Audit trail shows attempted unauthorized access
        """
        scenario = setup_multi_tenant_scenario
        
        # Step 1: User A1 accesses HR Bot documents
        bot = await validate_bot_access(
            db=async_db,
            bot_id=scenario["bots"]["a_hr"].id,
            tenant_id=scenario["tenants"]["a"].id,
            user_id=scenario["users"]["a1"].id,
        )
        assert bot.id == scenario["bots"]["a_hr"].id
        
        # Log successful access
        await BotAccessAudit.log_bot_access(
            db=async_db,
            user_id=scenario["users"]["a1"].id,
            bot_id=scenario["bots"]["a_hr"].id,
            tenant_id=scenario["tenants"]["a"].id,
            action="view_documents",
            status="success",
        )
        
        # Step 2: Query HR Bot documents
        from sqlalchemy import select
        stmt = select(Document).where(
            (Document.bot_id == scenario["bots"]["a_hr"].id) &
            (Document.tenant_id == scenario["tenants"]["a"].id)
        )
        result = await async_db.execute(stmt)
        docs = result.scalars().all()
        assert len(docs) == 2
        
        # Step 3: User A1 tries to access Tenant B's Support Bot (should fail)
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            await validate_bot_access(
                db=async_db,
                bot_id=scenario["bots"]["b_support"].id,
                tenant_id=scenario["tenants"]["a"].id,  # Wrong tenant
                user_id=scenario["users"]["a1"].id,
            )
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        
        # Log unauthorized attempt
        await BotAccessAudit.log_unauthorized_access(
            db=async_db,
            user_id=scenario["users"]["a1"].id,
            bot_id=scenario["bots"]["b_support"].id,
            tenant_id=scenario["tenants"]["a"].id,
            action="view_documents",
        )
        
        # Step 4: Verify audit trail
        stmt = select(AuditLog).where(AuditLog.actor_id == scenario["users"]["a1"].id)
        result = await async_db.execute(stmt)
        logs = result.scalars().all()
        
        assert len(logs) == 2
        assert logs[0].action == "bot_access_view_documents"
        assert "unauthorized" in logs[1].action.lower()
    
    async def test_multi_tenant_isolation_scenario(self, async_db, setup_multi_tenant_scenario):
        """
        Multi-tenant scenario:
        1. Both tenants have bots and documents
        2. User A1 can only access Tenant A resources
        3. User B1 can only access Tenant B resources
        4. No cross-tenant data leakage
        """
        from sqlalchemy import select
        scenario = setup_multi_tenant_scenario
        
        # User A1 can access Tenant A documents
        stmt = select(Document).where(
            Document.tenant_id == scenario["tenants"]["a"].id
        )
        result = await async_db.execute(stmt)
        docs_a = result.scalars().all()
        assert len(docs_a) == 3
        
        # User B1 can access Tenant B documents
        stmt = select(Document).where(
            Document.tenant_id == scenario["tenants"]["b"].id
        )
        result = await async_db.execute(stmt)
        docs_b = result.scalars().all()
        assert len(docs_b) == 2
        
        # User A1 cannot access Tenant B bots
        from fastapi import HTTPException
        for bot_key in ["b_support", "b_finance"]:
            with pytest.raises(HTTPException):
                await validate_bot_access(
                    db=async_db,
                    bot_id=scenario["bots"][bot_key].id,
                    tenant_id=scenario["tenants"]["a"].id,
                    user_id=scenario["users"]["a1"].id,
                )
        
        # User B1 cannot access Tenant A bots
        for bot_key in ["a_hr", "a_sales"]:
            with pytest.raises(HTTPException):
                await validate_bot_access(
                    db=async_db,
                    bot_id=scenario["bots"][bot_key].id,
                    tenant_id=scenario["tenants"]["b"].id,
                    user_id=scenario["users"]["b1"].id,
                )


# ============================================================================
# TEST SUITE 6: In-Memory Validation Performance
# ============================================================================

class TestInMemoryValidationPerformance:
    """Tests for in-memory quick validation function"""
    
    def test_quick_check_with_large_bot_list(self):
        """check_bot_isolation should be fast even with many bots"""
        # Create list of 1000 bot IDs
        user_bots = [uuid4() for _ in range(1000)]
        target_bot = user_bots[500]  # Find middle one
        
        result = check_bot_isolation(target_bot, uuid4(), user_bots)
        assert result is True
    
    def test_quick_check_with_missing_bot(self):
        """check_bot_isolation returns False for non-existent bot"""
        user_bots = [uuid4() for _ in range(100)]
        missing_bot = uuid4()
        
        result = check_bot_isolation(missing_bot, uuid4(), user_bots)
        assert result is False
    
    def test_quick_check_consistency(self):
        """check_bot_isolation gives consistent results"""
        user_bots = [uuid4() for _ in range(10)]
        target_bot = user_bots[3]
        tenant_id = uuid4()
        
        # Call multiple times
        results = [
            check_bot_isolation(target_bot, tenant_id, user_bots)
            for _ in range(100)
        ]
        
        # All should be True
        assert all(results)
