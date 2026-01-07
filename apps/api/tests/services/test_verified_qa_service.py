"""Tests for verified_qa service layer."""

import pytest
from uuid import uuid4
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.verified_qa_service import (
    create_verified_qa,
    get_verified_qa_by_id,
    list_verified_qa,
    update_verified_qa,
    delete_verified_qa
)
from app.schemas.verified_qa import VerifiedQACreate, VerifiedQAUpdate


@pytest.mark.asyncio
async def test_create_verified_qa_service(
    db: AsyncSession,
    test_tenant,
    test_group,
    test_bot,
    test_user
):
    """Test creating verified QA through service layer."""
    schema = VerifiedQACreate(
        question_text="What is the shipping cost?",
        answer_text="Shipping is free for orders over $50.",
        source_citations={"documents": ["shipping.pdf"], "pages": [2]},
        bot_id=test_bot.id
    )
    
    embedding = [0.1] * 768
    
    verified_qa = await create_verified_qa(
        db=db,
        tenant_id=test_tenant.id,
        group_id=test_group.id,
        bot_id=test_bot.id,
        question_text=schema.question_text,
        question_embedding=embedding,
        answer_text=schema.answer_text,
        source_citations=schema.source_citations,
        approved_by_user_id=test_user.id
    )
    
    assert verified_qa.id is not None
    assert verified_qa.question_text == schema.question_text
    assert verified_qa.answer_text == schema.answer_text
    assert verified_qa.tenant_id == test_tenant.id
    assert verified_qa.group_id == test_group.id
    assert verified_qa.bot_id == test_bot.id
    assert verified_qa.approved_by_user_id == test_user.id


@pytest.mark.asyncio
async def test_get_verified_qa_by_id_service(
    db: AsyncSession,
    test_tenant,
    test_group,
    test_bot,
    test_user
):
    """Test retrieving verified QA by ID with RLS enforcement."""
    # Create entry
    created_qa = await create_verified_qa(
        db=db,
        tenant_id=test_tenant.id,
        group_id=test_group.id,
        bot_id=test_bot.id,
        question_text="Test question?",
        question_embedding=[0.1] * 768,
        answer_text="Test answer",
        source_citations=None,
        approved_by_user_id=test_user.id
    )
    
    # Retrieve by ID
    retrieved_qa = await get_verified_qa_by_id(
        db=db,
        id=created_qa.id,
        tenant_id=test_tenant.id,
        group_id=test_group.id
    )
    
    assert retrieved_qa is not None
    assert retrieved_qa.id == created_qa.id
    assert retrieved_qa.question_text == "Test question?"


@pytest.mark.asyncio
async def test_get_verified_qa_wrong_tenant_returns_none(
    db: AsyncSession,
    test_tenant,
    test_group,
    test_bot,
    test_user
):
    """Test that querying with wrong tenant_id returns None (RLS enforcement)."""
    # Create entry
    created_qa = await create_verified_qa(
        db=db,
        tenant_id=test_tenant.id,
        group_id=test_group.id,
        bot_id=test_bot.id,
        question_text="Test question?",
        question_embedding=[0.1] * 768,
        answer_text="Test answer",
        source_citations=None,
        approved_by_user_id=test_user.id
    )
    
    # Try to retrieve with wrong tenant_id
    wrong_tenant_id = uuid4()
    retrieved_qa = await get_verified_qa_by_id(
        db=db,
        id=created_qa.id,
        tenant_id=wrong_tenant_id,
        group_id=test_group.id
    )
    
    assert retrieved_qa is None  # Should not be found due to tenant mismatch


@pytest.mark.asyncio
async def test_list_verified_qa_service(
    db: AsyncSession,
    test_tenant,
    test_group,
    test_bot,
    test_user
):
    """Test listing verified QA entries with pagination."""
    # Create multiple entries
    for i in range(5):
        await create_verified_qa(
            db=db,
            tenant_id=test_tenant.id,
            group_id=test_group.id,
            bot_id=test_bot.id,
            question_text=f"Question {i}?",
            question_embedding=[0.1 * i] * 768,
            answer_text=f"Answer {i}",
            source_citations=None,
            approved_by_user_id=test_user.id
        )
    
    # List all
    all_entries = await list_verified_qa(
        db=db,
        tenant_id=test_tenant.id,
        group_id=test_group.id,
        bot_id=None,
        limit=10,
        offset=0
    )
    
    assert len(all_entries) == 5
    
    # List with pagination
    page_1 = await list_verified_qa(
        db=db,
        tenant_id=test_tenant.id,
        group_id=test_group.id,
        bot_id=None,
        limit=2,
        offset=0
    )
    
    assert len(page_1) == 2
    
    page_2 = await list_verified_qa(
        db=db,
        tenant_id=test_tenant.id,
        group_id=test_group.id,
        bot_id=None,
        limit=2,
        offset=2
    )
    
    assert len(page_2) == 2
    assert page_1[0].id != page_2[0].id


@pytest.mark.asyncio
async def test_list_verified_qa_filtered_by_bot(
    db: AsyncSession,
    test_tenant,
    test_group,
    test_bot,
    test_user
):
    """Test filtering verified QA by bot_id."""
    # Create second bot
    from app.models.bot import Bot
    bot_2 = Bot(
        id=uuid4(),
        tenant_id=test_tenant.id,
        group_id=test_group.id,
        name="Bot 2",
        created_at=datetime.utcnow(),
    )
    db.add(bot_2)
    await db.commit()
    
    # Create entries for different bots
    await create_verified_qa(
        db=db,
        tenant_id=test_tenant.id,
        group_id=test_group.id,
        bot_id=test_bot.id,
        question_text="Bot 1 question?",
        question_embedding=[0.1] * 768,
        answer_text="Bot 1 answer",
        source_citations=None,
        approved_by_user_id=test_user.id
    )
    
    await create_verified_qa(
        db=db,
        tenant_id=test_tenant.id,
        group_id=test_group.id,
        bot_id=bot_2.id,
        question_text="Bot 2 question?",
        question_embedding=[0.2] * 768,
        answer_text="Bot 2 answer",
        source_citations=None,
        approved_by_user_id=test_user.id
    )
    
    # List filtered by bot_1
    bot_1_entries = await list_verified_qa(
        db=db,
        tenant_id=test_tenant.id,
        group_id=test_group.id,
        bot_id=test_bot.id,
        limit=10,
        offset=0
    )
    
    assert len(bot_1_entries) == 1
    assert bot_1_entries[0].bot_id == test_bot.id


@pytest.mark.asyncio
async def test_update_verified_qa_service(
    db: AsyncSession,
    test_tenant,
    test_group,
    test_bot,
    test_user
):
    """Test updating verified QA entry."""
    # Create entry
    created_qa = await create_verified_qa(
        db=db,
        tenant_id=test_tenant.id,
        group_id=test_group.id,
        bot_id=test_bot.id,
        question_text="Original question?",
        question_embedding=[0.1] * 768,
        answer_text="Original answer",
        source_citations=None,
        approved_by_user_id=test_user.id
    )
    
    # Update entry
    update_data = VerifiedQAUpdate(
        question_text="Updated question?",
        answer_text="Updated answer",
        source_citations={"documents": ["new.pdf"]}
    )
    
    updated_qa = await update_verified_qa(
        db=db,
        id=created_qa.id,
        tenant_id=test_tenant.id,
        group_id=test_group.id,
        update_data=update_data,
        new_embedding=[0.2] * 768  # New embedding for updated question
    )
    
    assert updated_qa is not None
    assert updated_qa.question_text == "Updated question?"
    assert updated_qa.answer_text == "Updated answer"
    assert updated_qa.source_citations == {"documents": ["new.pdf"]}


@pytest.mark.asyncio
async def test_delete_verified_qa_service(
    db: AsyncSession,
    test_tenant,
    test_group,
    test_bot,
    test_user
):
    """Test deleting verified QA entry."""
    # Create entry
    created_qa = await create_verified_qa(
        db=db,
        tenant_id=test_tenant.id,
        group_id=test_group.id,
        bot_id=test_bot.id,
        question_text="To be deleted?",
        question_embedding=[0.1] * 768,
        answer_text="Delete me",
        source_citations=None,
        approved_by_user_id=test_user.id
    )
    
    # Delete entry
    success = await delete_verified_qa(
        db=db,
        id=created_qa.id,
        tenant_id=test_tenant.id,
        group_id=test_group.id
    )
    
    assert success is True
    
    # Verify deleted
    deleted_qa = await get_verified_qa_by_id(
        db=db,
        id=created_qa.id,
        tenant_id=test_tenant.id,
        group_id=test_group.id
    )
    
    assert deleted_qa is None


@pytest.mark.asyncio
async def test_delete_nonexistent_entry_returns_false(
    db: AsyncSession,
    test_tenant,
    test_group
):
    """Test deleting non-existent entry returns False."""
    nonexistent_id = uuid4()
    
    success = await delete_verified_qa(
        db=db,
        id=nonexistent_id,
        tenant_id=test_tenant.id,
        group_id=test_group.id
    )
    
    assert success is False
