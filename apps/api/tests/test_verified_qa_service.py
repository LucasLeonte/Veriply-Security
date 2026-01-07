"""Tests for verified QA service layer.

Covers:
- create_verified_qa: Entry creation with validation
- get_verified_qa_by_id: Retrieval with RLS
- list_verified_qa: List with filtering and pagination
- Embedding generation and integration
- Multi-tenant scoping enforcement
"""

import pytest
from uuid import uuid4
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.models.verified_qa import VerifiedQA
from app.models.bot import Bot
from app.models.user import User
from app.services.verified_qa import (
    create_verified_qa,
    get_verified_qa_by_id,
    list_verified_qa,
)


@pytest.fixture
async def setup_test_data(db: AsyncSession):
    """Set up test data with users, bots, etc."""
    # Create users
    user1 = User(
        id=uuid4(),
        email="user1@example.com",
        username="user1",
        first_name="User",
        last_name="One",
        hashed_password="hashed",
    )
    user2 = User(
        id=uuid4(),
        email="user2@example.com",
        username="user2",
        first_name="User",
        last_name="Two",
        hashed_password="hashed",
    )
    db.add(user1)
    db.add(user2)

    # Create bots (will be created in routes)
    await db.flush()

    return {"user1": user1, "user2": user2}


class TestCreateVerifiedQA:
    """Tests for create_verified_qa service function."""

    async def test_create_entry_success(
        self, db: AsyncSession, test_user: User, test_bot: Bot, test_tenant, test_group
    ):
        """Successfully create a verified Q&A entry."""
        embedding = [0.1] * 768  # Valid 768-dim embedding

        qa = await create_verified_qa(
            db=db,
            tenant_id=test_tenant.id,
            group_id=test_group.id,
            bot_id=test_bot.id,
            question_text="What is your policy?",
            question_embedding=embedding,
            answer_text="Our policy is ...",
            approved_by_user_id=test_user.id,
            approved_at=datetime.utcnow(),
            source_citations={"docs": ["policy.pdf"]},
        )

        assert qa.id is not None
        assert qa.question_text == "What is your policy?"
        assert qa.answer_text == "Our policy is ..."
        assert qa.tenant_id == test_tenant.id
        assert qa.group_id == test_group.id
        assert qa.bot_id == test_bot.id
        assert qa.approved_by_user_id == test_user.id

    async def test_create_entry_strips_whitespace(
        self, db: AsyncSession, test_user: User, test_bot: Bot, test_tenant, test_group
    ):
        """Whitespace is stripped from question and answer."""
        embedding = [0.1] * 768

        qa = await create_verified_qa(
            db=db,
            tenant_id=test_tenant.id,
            group_id=test_group.id,
            bot_id=test_bot.id,
            question_text="  What is your policy?  ",
            question_embedding=embedding,
            answer_text="  Our policy is ...  ",
            approved_by_user_id=test_user.id,
            approved_at=datetime.utcnow(),
        )

        assert qa.question_text == "What is your policy?"
        assert qa.answer_text == "Our policy is ..."

    async def test_create_entry_question_too_long(
        self, db: AsyncSession, test_user: User, test_bot: Bot, test_tenant, test_group
    ):
        """Fail when question exceeds 2000 characters."""
        embedding = [0.1] * 768

        with pytest.raises(ValueError, match="exceeds maximum length"):
            await create_verified_qa(
                db=db,
                tenant_id=test_tenant.id,
                group_id=test_group.id,
                bot_id=test_bot.id,
                question_text="Q" * 2001,
                question_embedding=embedding,
                answer_text="Answer",
                approved_by_user_id=test_user.id,
                approved_at=datetime.utcnow(),
            )

    async def test_create_entry_wrong_embedding_dimension(
        self, db: AsyncSession, test_user: User, test_bot: Bot, test_tenant, test_group
    ):
        """Fail when embedding is not 768 dimensions."""
        embedding = [0.1] * 1024  # Wrong dimension

        with pytest.raises(ValueError, match="768 dimensions"):
            await create_verified_qa(
                db=db,
                tenant_id=test_tenant.id,
                group_id=test_group.id,
                bot_id=test_bot.id,
                question_text="Question?",
                question_embedding=embedding,
                answer_text="Answer",
                approved_by_user_id=test_user.id,
                approved_at=datetime.utcnow(),
            )

    async def test_create_entry_bot_not_found(
        self, db: AsyncSession, test_user: User, test_tenant, test_group
    ):
        """Fail when bot doesn't belong to tenant/group."""
        embedding = [0.1] * 768
        wrong_bot_id = uuid4()

        with pytest.raises(ValueError, match="not found"):
            await create_verified_qa(
                db=db,
                tenant_id=test_tenant.id,
                group_id=test_group.id,
                bot_id=wrong_bot_id,
                question_text="Question?",
                question_embedding=embedding,
                answer_text="Answer",
                approved_by_user_id=test_user.id,
                approved_at=datetime.utcnow(),
            )


class TestGetVerifiedQA:
    """Tests for get_verified_qa_by_id service function."""

    async def test_get_entry_success(
        self, db: AsyncSession, test_user: User, test_bot: Bot, test_tenant, test_group
    ):
        """Successfully retrieve an entry."""
        embedding = [0.1] * 768

        # Create entry
        created_qa = await create_verified_qa(
            db=db,
            tenant_id=test_tenant.id,
            group_id=test_group.id,
            bot_id=test_bot.id,
            question_text="Question?",
            question_embedding=embedding,
            answer_text="Answer",
            approved_by_user_id=test_user.id,
            approved_at=datetime.utcnow(),
        )
        await db.commit()

        # Retrieve entry
        qa = await get_verified_qa_by_id(
            db=db,
            entry_id=created_qa.id,
            tenant_id=test_tenant.id,
        )

        assert qa is not None
        assert qa.id == created_qa.id
        assert qa.question_text == "Question?"

    async def test_get_entry_not_found(
        self, db: AsyncSession, test_tenant
    ):
        """Return None when entry doesn't exist."""
        qa = await get_verified_qa_by_id(
            db=db,
            entry_id=uuid4(),
            tenant_id=test_tenant.id,
        )

        assert qa is None


class TestListVerifiedQA:
    """Tests for list_verified_qa service function."""

    async def test_list_entries_success(
        self, db: AsyncSession, test_user: User, test_bot: Bot, test_tenant, test_group
    ):
        """Successfully list entries."""
        embedding = [0.1] * 768

        # Create 3 entries
        for i in range(3):
            await create_verified_qa(
                db=db,
                tenant_id=test_tenant.id,
                group_id=test_group.id,
                bot_id=test_bot.id,
                question_text=f"Question {i}?",
                question_embedding=embedding,
                answer_text=f"Answer {i}",
                approved_by_user_id=test_user.id,
                approved_at=datetime.utcnow(),
            )
        await db.commit()

        # List entries
        entries = await list_verified_qa(
            db=db,
            tenant_id=test_tenant.id,
            skip=0,
            limit=10,
        )

        assert len(entries) == 3

    async def test_list_entries_pagination(
        self, db: AsyncSession, test_user: User, test_bot: Bot, test_tenant, test_group
    ):
        """Pagination works correctly."""
        embedding = [0.1] * 768

        # Create 15 entries
        for i in range(15):
            await create_verified_qa(
                db=db,
                tenant_id=test_tenant.id,
                group_id=test_group.id,
                bot_id=test_bot.id,
                question_text=f"Question {i}?",
                question_embedding=embedding,
                answer_text=f"Answer {i}",
                approved_by_user_id=test_user.id,
                approved_at=datetime.utcnow(),
            )
        await db.commit()

        # First page
        page1 = await list_verified_qa(
            db=db,
            tenant_id=test_tenant.id,
            skip=0,
            limit=10,
        )
        assert len(page1) == 10

        # Second page
        page2 = await list_verified_qa(
            db=db,
            tenant_id=test_tenant.id,
            skip=10,
            limit=10,
        )
        assert len(page2) == 5

    async def test_list_entries_filter_by_bot(
        self, db: AsyncSession, test_user: User, test_bot: Bot, test_tenant, test_group
    ):
        """Filtering by bot_id works."""
        embedding = [0.1] * 768

        # Create entries for bot 1
        for i in range(3):
            await create_verified_qa(
                db=db,
                tenant_id=test_tenant.id,
                group_id=test_group.id,
                bot_id=test_bot.id,
                question_text=f"Question {i}?",
                question_embedding=embedding,
                answer_text=f"Answer {i}",
                approved_by_user_id=test_user.id,
                approved_at=datetime.utcnow(),
            )
        await db.commit()

        # List with bot filter
        entries = await list_verified_qa(
            db=db,
            tenant_id=test_tenant.id,
            bot_id=test_bot.id,
            skip=0,
            limit=10,
        )

        assert len(entries) == 3
        assert all(e.bot_id == test_bot.id for e in entries)

    async def test_list_entries_filter_by_group(
        self, db: AsyncSession, test_user: User, test_bot: Bot, test_tenant, test_group
    ):
        """Filtering by group_id works."""
        embedding = [0.1] * 768

        # Create entries
        for i in range(3):
            await create_verified_qa(
                db=db,
                tenant_id=test_tenant.id,
                group_id=test_group.id,
                bot_id=test_bot.id,
                question_text=f"Question {i}?",
                question_embedding=embedding,
                answer_text=f"Answer {i}",
                approved_by_user_id=test_user.id,
                approved_at=datetime.utcnow(),
            )
        await db.commit()

        # List with group filter
        entries = await list_verified_qa(
            db=db,
            tenant_id=test_tenant.id,
            group_id=test_group.id,
            skip=0,
            limit=10,
        )

        assert len(entries) == 3
        assert all(e.group_id == test_group.id for e in entries)

    async def test_list_entries_enforces_tenant_isolation(
        self, db: AsyncSession, test_user: User, test_bot: Bot, test_tenant, test_group
    ):
        """Entries are isolated by tenant."""
        embedding = [0.1] * 768

        # Create entries for tenant 1
        await create_verified_qa(
            db=db,
            tenant_id=test_tenant.id,
            group_id=test_group.id,
            bot_id=test_bot.id,
            question_text="Question?",
            question_embedding=embedding,
            answer_text="Answer",
            approved_by_user_id=test_user.id,
            approved_at=datetime.utcnow(),
        )
        await db.commit()

        # List with different tenant
        entries = await list_verified_qa(
            db=db,
            tenant_id=uuid4(),  # Different tenant
            skip=0,
            limit=10,
        )

        assert len(entries) == 0
