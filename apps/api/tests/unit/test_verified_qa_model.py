"""Unit tests for VerifiedQA model."""

import pytest
from datetime import datetime
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.verified_qa import VerifiedQA
from app.models.tenant import Tenant
from app.models.group import Group
from app.models.bot import Bot
from app.models.user import User


@pytest.mark.asyncio
async def test_create_verified_qa(db: AsyncSession, test_tenant, test_group, test_bot, test_user):
    """Test creating a verified QA entry with all required fields."""
    verified_qa = VerifiedQA(
        id=uuid4(),
        tenant_id=test_tenant.id,
        group_id=test_group.id,
        bot_id=test_bot.id,
        question_text="What is the refund policy?",
        question_embedding=[0.1] * 768,  # 768-dimensional vector
        answer_text="Our refund policy allows returns within 30 days.",
        source_citations={"documents": ["policy.pdf"], "pages": [1]},
        approved_by_user_id=test_user.id,
        approved_at=datetime.utcnow(),
    )
    
    db.add(verified_qa)
    await db.commit()
    await db.refresh(verified_qa)
    
    assert verified_qa.id is not None
    assert verified_qa.question_text == "What is the refund policy?"
    assert len(verified_qa.question_embedding) == 768
    assert verified_qa.answer_text == "Our refund policy allows returns within 30 days."
    assert verified_qa.source_citations["documents"] == ["policy.pdf"]
    assert verified_qa.approved_by_user_id == test_user.id


@pytest.mark.asyncio
async def test_verified_qa_relationships(db: AsyncSession, test_tenant, test_group, test_bot, test_user):
    """Test VerifiedQA relationships to Bot, Group, Tenant, and User."""
    verified_qa = VerifiedQA(
        id=uuid4(),
        tenant_id=test_tenant.id,
        group_id=test_group.id,
        bot_id=test_bot.id,
        question_text="Test question?",
        question_embedding=[0.5] * 768,
        answer_text="Test answer.",
        approved_by_user_id=test_user.id,
        approved_at=datetime.utcnow(),
    )
    
    db.add(verified_qa)
    await db.commit()
    
    # Query with relationships loaded
    stmt = select(VerifiedQA).where(VerifiedQA.id == verified_qa.id)
    result = await db.execute(stmt)
    qa = result.scalar_one()
    
    assert qa.tenant_id == test_tenant.id
    assert qa.group_id == test_group.id
    assert qa.bot_id == test_bot.id
    assert qa.approved_by_user_id == test_user.id


@pytest.mark.asyncio
async def test_question_text_max_length_validation(db: AsyncSession, test_tenant, test_group, test_bot, test_user):
    """Test that question_text respects 2000 character limit."""
    # Create question text that exceeds 2000 characters
    long_question = "A" * 2001
    
    verified_qa = VerifiedQA(
        id=uuid4(),
        tenant_id=test_tenant.id,
        group_id=test_group.id,
        bot_id=test_bot.id,
        question_text=long_question,
        question_embedding=[0.1] * 768,
        answer_text="Answer",
        approved_by_user_id=test_user.id,
        approved_at=datetime.utcnow(),
    )
    
    db.add(verified_qa)
    
    # Should raise validation error due to CHECK constraint
    with pytest.raises(Exception):  # Database constraint error
        await db.commit()


@pytest.mark.asyncio
async def test_embedding_dimension_validation(db: AsyncSession, test_tenant, test_group, test_bot, test_user):
    """Test that embedding must be exactly 768 dimensions."""
    # Correct dimension should work
    verified_qa_correct = VerifiedQA(
        id=uuid4(),
        tenant_id=test_tenant.id,
        group_id=test_group.id,
        bot_id=test_bot.id,
        question_text="Correct dimension test?",
        question_embedding=[0.1] * 768,
        answer_text="Answer",
        approved_by_user_id=test_user.id,
        approved_at=datetime.utcnow(),
    )
    
    db.add(verified_qa_correct)
    await db.commit()
    assert verified_qa_correct.id is not None
    
    # Wrong dimension (1024) should fail
    verified_qa_wrong = VerifiedQA(
        id=uuid4(),
        tenant_id=test_tenant.id,
        group_id=test_group.id,
        bot_id=test_bot.id,
        question_text="Wrong dimension test?",
        question_embedding=[0.1] * 1024,  # Wrong dimension
        answer_text="Answer",
        approved_by_user_id=test_user.id,
        approved_at=datetime.utcnow(),
    )
    
    db.add(verified_qa_wrong)
    
    with pytest.raises(Exception):  # Vector dimension mismatch error
        await db.commit()


@pytest.mark.asyncio
async def test_timestamps_auto_populate(db: AsyncSession, test_tenant, test_group, test_bot, test_user):
    """Test that created_at and updated_at timestamps are automatically set."""
    verified_qa = VerifiedQA(
        id=uuid4(),
        tenant_id=test_tenant.id,
        group_id=test_group.id,
        bot_id=test_bot.id,
        question_text="Timestamp test?",
        question_embedding=[0.1] * 768,
        answer_text="Answer",
        approved_by_user_id=test_user.id,
        approved_at=datetime.utcnow(),
    )
    
    db.add(verified_qa)
    await db.commit()
    await db.refresh(verified_qa)
    
    assert verified_qa.created_at is not None
    assert verified_qa.updated_at is not None
    assert isinstance(verified_qa.created_at, datetime)
    assert isinstance(verified_qa.updated_at, datetime)


@pytest.mark.asyncio
async def test_source_citations_jsonb(db: AsyncSession, test_tenant, test_group, test_bot, test_user):
    """Test that source_citations stores complex JSON data."""
    citations = {
        "documents": ["doc1.pdf", "doc2.pdf"],
        "pages": [1, 5, 10],
        "sections": ["Introduction", "Pricing"],
        "confidence": 0.95
    }
    
    verified_qa = VerifiedQA(
        id=uuid4(),
        tenant_id=test_tenant.id,
        group_id=test_group.id,
        bot_id=test_bot.id,
        question_text="Complex citations test?",
        question_embedding=[0.1] * 768,
        answer_text="Answer with multiple sources.",
        source_citations=citations,
        approved_by_user_id=test_user.id,
        approved_at=datetime.utcnow(),
    )
    
    db.add(verified_qa)
    await db.commit()
    await db.refresh(verified_qa)
    
    assert verified_qa.source_citations == citations
    assert verified_qa.source_citations["documents"] == ["doc1.pdf", "doc2.pdf"]
    assert verified_qa.source_citations["confidence"] == 0.95


@pytest.mark.asyncio
async def test_required_fields_validation(db: AsyncSession, test_tenant, test_group, test_bot, test_user):
    """Test that all required fields must be present."""
    # Missing question_text
    with pytest.raises(Exception):
        verified_qa = VerifiedQA(
            id=uuid4(),
            tenant_id=test_tenant.id,
            group_id=test_group.id,
            bot_id=test_bot.id,
            # question_text missing
            question_embedding=[0.1] * 768,
            answer_text="Answer",
            approved_by_user_id=test_user.id,
            approved_at=datetime.utcnow(),
        )
        db.add(verified_qa)
        await db.commit()
    
    await db.rollback()
    
    # Missing answer_text
    with pytest.raises(Exception):
        verified_qa = VerifiedQA(
            id=uuid4(),
            tenant_id=test_tenant.id,
            group_id=test_group.id,
            bot_id=test_bot.id,
            question_text="Question?",
            question_embedding=[0.1] * 768,
            # answer_text missing
            approved_by_user_id=test_user.id,
            approved_at=datetime.utcnow(),
        )
        db.add(verified_qa)
        await db.commit()


@pytest.mark.asyncio
async def test_foreign_key_constraints(db: AsyncSession, test_tenant, test_group, test_bot):
    """Test that foreign key constraints are enforced."""
    # Invalid user_id should fail
    invalid_user_id = uuid4()
    
    verified_qa = VerifiedQA(
        id=uuid4(),
        tenant_id=test_tenant.id,
        group_id=test_group.id,
        bot_id=test_bot.id,
        question_text="FK test?",
        question_embedding=[0.1] * 768,
        answer_text="Answer",
        approved_by_user_id=invalid_user_id,  # Non-existent user
        approved_at=datetime.utcnow(),
    )
    
    db.add(verified_qa)
    
    with pytest.raises(Exception):  # Foreign key constraint error
        await db.commit()
