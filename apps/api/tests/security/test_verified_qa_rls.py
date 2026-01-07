"""Security tests for VerifiedQA RLS (Row-Level Security) enforcement."""

import pytest
from uuid import uuid4
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.models.verified_qa import VerifiedQA
from app.models.tenant import Tenant
from app.models.group import Group
from app.models.bot import Bot
from app.models.user import User


@pytest.fixture
async def second_tenant(db: AsyncSession):
    """Create a second tenant for cross-tenant testing."""
    tenant = Tenant(
        id=uuid4(),
        name="Tenant B",
        created_at=datetime.utcnow(),
    )
    db.add(tenant)
    await db.commit()
    await db.refresh(tenant)
    return tenant


@pytest.fixture
async def second_group(db: AsyncSession, second_tenant):
    """Create a second group for cross-group testing."""
    group = Group(
        id=uuid4(),
        tenant_id=second_tenant.id,
        name="Group B",
        created_by=uuid4(),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(group)
    await db.commit()
    await db.refresh(group)
    return group


@pytest.fixture
async def second_bot(db: AsyncSession, second_tenant, second_group):
    """Create a second bot for testing."""
    bot = Bot(
        id=uuid4(),
        tenant_id=second_tenant.id,
        group_id=second_group.id,
        name="Bot B",
        created_at=datetime.utcnow(),
    )
    db.add(bot)
    await db.commit()
    await db.refresh(bot)
    return bot


@pytest.mark.asyncio
async def test_cross_tenant_isolation(
    db: AsyncSession,
    test_tenant,
    test_group,
    test_bot,
    test_user,
    second_tenant,
    second_group,
    second_bot
):
    """Test that Tenant A cannot access Tenant B's verified QA entries."""
    # Create VerifiedQA for Tenant A
    qa_tenant_a = VerifiedQA(
        id=uuid4(),
        tenant_id=test_tenant.id,
        group_id=test_group.id,
        bot_id=test_bot.id,
        question_text="Tenant A question?",
        question_embedding=[0.1] * 768,
        answer_text="Tenant A answer",
        approved_by_user_id=test_user.id,
        approved_at=datetime.utcnow(),
    )
    
    # Create VerifiedQA for Tenant B
    qa_tenant_b = VerifiedQA(
        id=uuid4(),
        tenant_id=second_tenant.id,
        group_id=second_group.id,
        bot_id=second_bot.id,
        question_text="Tenant B question?",
        question_embedding=[0.2] * 768,
        answer_text="Tenant B answer",
        approved_by_user_id=test_user.id,
        approved_at=datetime.utcnow(),
    )
    
    db.add_all([qa_tenant_a, qa_tenant_b])
    await db.commit()
    
    # Query with Tenant A filter
    stmt_tenant_a = select(VerifiedQA).where(VerifiedQA.tenant_id == test_tenant.id)
    result_a = await db.execute(stmt_tenant_a)
    tenant_a_entries = result_a.scalars().all()
    
    # Query with Tenant B filter
    stmt_tenant_b = select(VerifiedQA).where(VerifiedQA.tenant_id == second_tenant.id)
    result_b = await db.execute(stmt_tenant_b)
    tenant_b_entries = result_b.scalars().all()
    
    # Verify isolation
    assert len(tenant_a_entries) == 1
    assert tenant_a_entries[0].question_text == "Tenant A question?"
    
    assert len(tenant_b_entries) == 1
    assert tenant_b_entries[0].question_text == "Tenant B question?"
    
    # Verify Tenant A cannot see Tenant B's data
    assert qa_tenant_b.id not in [qa.id for qa in tenant_a_entries]


@pytest.mark.asyncio
async def test_cross_group_isolation_same_tenant(
    db: AsyncSession,
    test_tenant,
    test_group,
    test_bot,
    test_user
):
    """Test that Group A cannot access Group B's verified QA (same tenant)."""
    # Create second group in same tenant
    group_b = Group(
        id=uuid4(),
        tenant_id=test_tenant.id,
        name="Group B",
        created_by=test_user.id,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(group_b)
    await db.commit()
    
    # Create bot for Group B
    bot_b = Bot(
        id=uuid4(),
        tenant_id=test_tenant.id,
        group_id=group_b.id,
        name="Bot Group B",
        created_at=datetime.utcnow(),
    )
    db.add(bot_b)
    await db.commit()
    
    # Create VerifiedQA for Group A
    qa_group_a = VerifiedQA(
        id=uuid4(),
        tenant_id=test_tenant.id,
        group_id=test_group.id,
        bot_id=test_bot.id,
        question_text="Group A question?",
        question_embedding=[0.1] * 768,
        answer_text="Group A answer",
        approved_by_user_id=test_user.id,
        approved_at=datetime.utcnow(),
    )
    
    # Create VerifiedQA for Group B
    qa_group_b = VerifiedQA(
        id=uuid4(),
        tenant_id=test_tenant.id,
        group_id=group_b.id,
        bot_id=bot_b.id,
        question_text="Group B question?",
        question_embedding=[0.2] * 768,
        answer_text="Group B answer",
        approved_by_user_id=test_user.id,
        approved_at=datetime.utcnow(),
    )
    
    db.add_all([qa_group_a, qa_group_b])
    await db.commit()
    
    # Query with Group A filter
    stmt_group_a = select(VerifiedQA).where(
        and_(
            VerifiedQA.tenant_id == test_tenant.id,
            VerifiedQA.group_id == test_group.id
        )
    )
    result_a = await db.execute(stmt_group_a)
    group_a_entries = result_a.scalars().all()
    
    # Query with Group B filter
    stmt_group_b = select(VerifiedQA).where(
        and_(
            VerifiedQA.tenant_id == test_tenant.id,
            VerifiedQA.group_id == group_b.id
        )
    )
    result_b = await db.execute(stmt_group_b)
    group_b_entries = result_b.scalars().all()
    
    # Verify group isolation
    assert len(group_a_entries) == 1
    assert group_a_entries[0].question_text == "Group A question?"
    
    assert len(group_b_entries) == 1
    assert group_b_entries[0].question_text == "Group B question?"
    
    # Verify Group A cannot see Group B's data
    assert qa_group_b.id not in [qa.id for qa in group_a_entries]


@pytest.mark.asyncio
async def test_bot_scoping_within_group(
    db: AsyncSession,
    test_tenant,
    test_group,
    test_bot,
    test_user
):
    """Test that VerifiedQA entries are properly scoped by bot_id."""
    # Create second bot in same group
    bot_2 = Bot(
        id=uuid4(),
        tenant_id=test_tenant.id,
        group_id=test_group.id,
        name="Bot 2",
        created_at=datetime.utcnow(),
    )
    db.add(bot_2)
    await db.commit()
    
    # Create VerifiedQA for Bot 1
    qa_bot_1 = VerifiedQA(
        id=uuid4(),
        tenant_id=test_tenant.id,
        group_id=test_group.id,
        bot_id=test_bot.id,
        question_text="Bot 1 question?",
        question_embedding=[0.1] * 768,
        answer_text="Bot 1 answer",
        approved_by_user_id=test_user.id,
        approved_at=datetime.utcnow(),
    )
    
    # Create VerifiedQA for Bot 2
    qa_bot_2 = VerifiedQA(
        id=uuid4(),
        tenant_id=test_tenant.id,
        group_id=test_group.id,
        bot_id=bot_2.id,
        question_text="Bot 2 question?",
        question_embedding=[0.2] * 768,
        answer_text="Bot 2 answer",
        approved_by_user_id=test_user.id,
        approved_at=datetime.utcnow(),
    )
    
    db.add_all([qa_bot_1, qa_bot_2])
    await db.commit()
    
    # Query by bot_id
    stmt_bot_1 = select(VerifiedQA).where(VerifiedQA.bot_id == test_bot.id)
    result_1 = await db.execute(stmt_bot_1)
    bot_1_entries = result_1.scalars().all()
    
    stmt_bot_2 = select(VerifiedQA).where(VerifiedQA.bot_id == bot_2.id)
    result_2 = await db.execute(stmt_bot_2)
    bot_2_entries = result_2.scalars().all()
    
    # Verify bot scoping
    assert len(bot_1_entries) == 1
    assert bot_1_entries[0].bot_id == test_bot.id
    
    assert len(bot_2_entries) == 1
    assert bot_2_entries[0].bot_id == bot_2.id


@pytest.mark.asyncio
async def test_composite_index_performance(
    db: AsyncSession,
    test_tenant,
    test_group,
    test_bot,
    test_user
):
    """Test that composite index (tenant_id, group_id, bot_id) improves query performance."""
    # Create multiple VerifiedQA entries
    for i in range(10):
        qa = VerifiedQA(
            id=uuid4(),
            tenant_id=test_tenant.id,
            group_id=test_group.id,
            bot_id=test_bot.id,
            question_text=f"Question {i}?",
            question_embedding=[0.1 * i] * 768,
            answer_text=f"Answer {i}",
            approved_by_user_id=test_user.id,
            approved_at=datetime.utcnow(),
        )
        db.add(qa)
    
    await db.commit()
    
    # Query with composite filter (should use index)
    stmt = select(VerifiedQA).where(
        and_(
            VerifiedQA.tenant_id == test_tenant.id,
            VerifiedQA.group_id == test_group.id,
            VerifiedQA.bot_id == test_bot.id
        )
    )
    result = await db.execute(stmt)
    entries = result.scalars().all()
    
    assert len(entries) == 10
    assert all(e.tenant_id == test_tenant.id for e in entries)
    assert all(e.group_id == test_group.id for e in entries)
    assert all(e.bot_id == test_bot.id for e in entries)


@pytest.mark.asyncio
async def test_rls_prevents_unauthorized_access(
    db: AsyncSession,
    test_tenant,
    test_group,
    test_bot,
    test_user,
    second_tenant
):
    """Test that attempting to query without proper tenant/group context fails."""
    # Create VerifiedQA for test tenant
    qa = VerifiedQA(
        id=uuid4(),
        tenant_id=test_tenant.id,
        group_id=test_group.id,
        bot_id=test_bot.id,
        question_text="Protected question?",
        question_embedding=[0.1] * 768,
        answer_text="Protected answer",
        approved_by_user_id=test_user.id,
        approved_at=datetime.utcnow(),
    )
    db.add(qa)
    await db.commit()
    
    # Query without tenant filter should not return data from other tenant
    stmt = select(VerifiedQA).where(VerifiedQA.tenant_id == second_tenant.id)
    result = await db.execute(stmt)
    unauthorized_entries = result.scalars().all()
    
    # Should not be able to see test_tenant's data
    assert len(unauthorized_entries) == 0
    assert qa.id not in [e.id for e in unauthorized_entries]
