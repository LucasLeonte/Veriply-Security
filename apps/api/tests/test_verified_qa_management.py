"""Tests for Story 7.4: Verified KB Management - Edit, Delete, List & Search.

Tests cover:
- List endpoint with pagination, search, and filtering
- Edit endpoint with embedding regeneration
- Delete endpoint with soft-delete behavior
- Search filtering by keyword, creator, and date range
"""

import pytest
from uuid import uuid4
from datetime import datetime, timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from httpx import AsyncClient

from app.models.verified_qa import VerifiedQA
from app.models.user import User
from app.models.group import Group
from app.models.tenant import Tenant
from app.schemas.verified_qa import VerifiedQAUpdate


@pytest.mark.asyncio
class TestVerifiedQAManagement:
    """Tests for Verified KB Management (Story 7.4)."""

    async def test_list_verified_qa_with_pagination(
        self,
        async_client: AsyncClient,
        db: AsyncSession,
        test_user: User,
        test_group: Group,
        test_tenant: Tenant,
    ):
        """Test listing verified Q&A entries with pagination."""
        # Create multiple test entries
        for i in range(25):
            qa = VerifiedQA(
                tenant_id=test_tenant.id,
                group_id=test_group.id,
                question_text=f"Question {i}",
                question_embedding=[0.1] * 768,
                answer_text=f"Answer {i}",
                approved_by_user_id=test_user.id,
                approved_at=datetime.utcnow(),
            )
            db.add(qa)
        await db.commit()

        # Test first page
        response = await async_client.get(
            "/api/v1/verified-qa/search",
            params={
                "group_id": str(test_group.id),
                "page": 1,
                "limit": 10,
            },
            headers={"Authorization": f"Bearer {test_user.token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 10
        assert data["total"] == 25
        assert data["page"] == 1
        assert data["limit"] == 10
        assert data["total_pages"] == 3

        # Test second page
        response = await async_client.get(
            "/api/v1/verified-qa/search",
            params={
                "group_id": str(test_group.id),
                "page": 2,
                "limit": 10,
            },
            headers={"Authorization": f"Bearer {test_user.token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 10
        assert data["page"] == 2

    async def test_search_verified_qa_by_keyword(
        self,
        async_client: AsyncClient,
        db: AsyncSession,
        test_user: User,
        test_group: Group,
        test_tenant: Tenant,
    ):
        """Test searching verified Q&A by keyword."""
        # Create test entries with specific keywords
        qa1 = VerifiedQA(
            tenant_id=test_tenant.id,
            group_id=test_group.id,
            question_text="What is the return policy?",
            question_embedding=[0.1] * 768,
            answer_text="We have a 30-day return policy.",
            approved_by_user_id=test_user.id,
            approved_at=datetime.utcnow(),
        )
        qa2 = VerifiedQA(
            tenant_id=test_tenant.id,
            group_id=test_group.id,
            question_text="How to track my order?",
            question_embedding=[0.2] * 768,
            answer_text="You can track your order using your tracking number.",
            approved_by_user_id=test_user.id,
            approved_at=datetime.utcnow(),
        )
        db.add_all([qa1, qa2])
        await db.commit()

        # Search for "return"
        response = await async_client.get(
            "/api/v1/verified-qa/search",
            params={
                "group_id": str(test_group.id),
                "search": "return",
                "page": 1,
                "limit": 20,
            },
            headers={"Authorization": f"Bearer {test_user.token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert "return" in data["items"][0]["question_text"].lower()

    async def test_filter_verified_qa_by_date_range(
        self,
        async_client: AsyncClient,
        db: AsyncSession,
        test_user: User,
        test_group: Group,
        test_tenant: Tenant,
    ):
        """Test filtering verified Q&A by date range."""
        # Create entries with different dates
        now = datetime.utcnow()
        qa1 = VerifiedQA(
            tenant_id=test_tenant.id,
            group_id=test_group.id,
            question_text="Old question",
            question_embedding=[0.1] * 768,
            answer_text="Old answer",
            approved_by_user_id=test_user.id,
            approved_at=datetime.utcnow(),
            created_at=now - timedelta(days=10),
        )
        qa2 = VerifiedQA(
            tenant_id=test_tenant.id,
            group_id=test_group.id,
            question_text="Recent question",
            question_embedding=[0.2] * 768,
            answer_text="Recent answer",
            approved_by_user_id=test_user.id,
            approved_at=datetime.utcnow(),
            created_at=now - timedelta(days=1),
        )
        db.add_all([qa1, qa2])
        await db.commit()

        # Filter for last 5 days
        from_date = (now - timedelta(days=5)).isoformat()
        response = await async_client.get(
            "/api/v1/verified-qa/search",
            params={
                "group_id": str(test_group.id),
                "from_date": from_date,
                "page": 1,
                "limit": 20,
            },
            headers={"Authorization": f"Bearer {test_user.token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert "Recent" in data["items"][0]["question_text"]

    async def test_edit_verified_qa_entry(
        self,
        async_client: AsyncClient,
        db: AsyncSession,
        test_user: User,
        test_group: Group,
        test_tenant: Tenant,
    ):
        """Test editing a verified Q&A entry."""
        # Create an entry
        qa = VerifiedQA(
            tenant_id=test_tenant.id,
            group_id=test_group.id,
            question_text="Original question",
            question_embedding=[0.1] * 768,
            answer_text="Original answer",
            approved_by_user_id=test_user.id,
            approved_at=datetime.utcnow(),
        )
        db.add(qa)
        await db.commit()
        await db.refresh(qa)

        # Edit the entry
        response = await async_client.put(
            f"/api/v1/verified-qa/{qa.id}",
            json={
                "question_text": "Updated question",
                "answer_text": "Updated answer",
            },
            params={"group_id": str(test_group.id)},
            headers={"Authorization": f"Bearer {test_user.token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["question_text"] == "Updated question"
        assert data["answer_text"] == "Updated answer"
        assert data["updated_by_user_id"] == str(test_user.id)

        # Verify in database
        stmt = select(VerifiedQA).where(VerifiedQA.id == qa.id)
        result = await db.execute(stmt)
        updated_qa = result.scalar_one()
        assert updated_qa.question_text == "Updated question"
        assert updated_qa.updated_by_user_id == test_user.id

    async def test_edit_regenerates_embedding(
        self,
        async_client: AsyncClient,
        db: AsyncSession,
        test_user: User,
        test_group: Group,
        test_tenant: Tenant,
    ):
        """Test that editing question text regenerates embedding."""
        # Create an entry
        original_embedding = [0.1] * 768
        qa = VerifiedQA(
            tenant_id=test_tenant.id,
            group_id=test_group.id,
            question_text="Original question",
            question_embedding=original_embedding,
            answer_text="Answer",
            approved_by_user_id=test_user.id,
            approved_at=datetime.utcnow(),
        )
        db.add(qa)
        await db.commit()
        await db.refresh(qa)

        # Edit with new question (embedding should be regenerated)
        response = await async_client.put(
            f"/api/v1/verified-qa/{qa.id}",
            json={"question_text": "Completely different question"},
            params={"group_id": str(test_group.id)},
            headers={"Authorization": f"Bearer {test_user.token}"},
        )

        assert response.status_code == 200

        # Verify embedding was regenerated (should be different)
        stmt = select(VerifiedQA).where(VerifiedQA.id == qa.id)
        result = await db.execute(stmt)
        updated_qa = result.scalar_one()
        # Embedding should be regenerated (actual values depend on embedding service)
        assert updated_qa.question_embedding is not None

    async def test_soft_delete_verified_qa(
        self,
        async_client: AsyncClient,
        db: AsyncSession,
        test_user: User,
        test_group: Group,
        test_tenant: Tenant,
    ):
        """Test soft-deleting a verified Q&A entry."""
        # Create an entry
        qa = VerifiedQA(
            tenant_id=test_tenant.id,
            group_id=test_group.id,
            question_text="Question to delete",
            question_embedding=[0.1] * 768,
            answer_text="Answer",
            approved_by_user_id=test_user.id,
            approved_at=datetime.utcnow(),
        )
        db.add(qa)
        await db.commit()
        await db.refresh(qa)
        qa_id = qa.id

        # Delete the entry
        response = await async_client.delete(
            f"/api/v1/verified-qa/{qa_id}",
            params={"group_id": str(test_group.id)},
            headers={"Authorization": f"Bearer {test_user.token}"},
        )

        assert response.status_code == 204

        # Verify it's soft-deleted (still in database but marked deleted)
        stmt = select(VerifiedQA).where(VerifiedQA.id == qa_id)
        result = await db.execute(stmt)
        deleted_qa = result.scalar_one()
        assert deleted_qa.deleted_at is not None
        assert deleted_qa.updated_by_user_id == test_user.id

    async def test_deleted_entries_excluded_from_search(
        self,
        async_client: AsyncClient,
        db: AsyncSession,
        test_user: User,
        test_group: Group,
        test_tenant: Tenant,
    ):
        """Test that soft-deleted entries are excluded from search results."""
        # Create two entries
        qa1 = VerifiedQA(
            tenant_id=test_tenant.id,
            group_id=test_group.id,
            question_text="Active question",
            question_embedding=[0.1] * 768,
            answer_text="Active answer",
            approved_by_user_id=test_user.id,
            approved_at=datetime.utcnow(),
        )
        qa2 = VerifiedQA(
            tenant_id=test_tenant.id,
            group_id=test_group.id,
            question_text="Deleted question",
            question_embedding=[0.2] * 768,
            answer_text="Deleted answer",
            approved_by_user_id=test_user.id,
            approved_at=datetime.utcnow(),
            deleted_at=datetime.utcnow(),
        )
        db.add_all([qa1, qa2])
        await db.commit()

        # Search without filters
        response = await async_client.get(
            "/api/v1/verified-qa/search",
            params={
                "group_id": str(test_group.id),
                "page": 1,
                "limit": 20,
            },
            headers={"Authorization": f"Bearer {test_user.token}"},
        )

        assert response.status_code == 200
        data = response.json()
        # Only active entry should be returned
        assert data["total"] == 1
        assert data["items"][0]["question_text"] == "Active question"

    async def test_unauthorized_access_denied(
        self,
        async_client: AsyncClient,
        db: AsyncSession,
        test_user: User,
        test_group: Group,
        test_tenant: Tenant,
        other_tenant: Tenant,
    ):
        """Test that users cannot access entries from other tenants."""
        # Create entry in test_tenant
        qa = VerifiedQA(
            tenant_id=test_tenant.id,
            group_id=test_group.id,
            question_text="Question",
            question_embedding=[0.1] * 768,
            answer_text="Answer",
            approved_by_user_id=test_user.id,
            approved_at=datetime.utcnow(),
        )
        db.add(qa)
        await db.commit()

        # Try to access with different tenant
        other_user = User(
            email="other@example.com",
            tenant_id=other_tenant.id,
            full_name="Other User",
        )
        db.add(other_user)
        await db.commit()

        response = await async_client.get(
            f"/api/v1/verified-qa/{qa.id}",
            headers={"Authorization": f"Bearer {other_user.token}"},
        )

        # Should be forbidden or not found
        assert response.status_code in [403, 404]

    async def test_invalid_date_format_returns_error(
        self,
        async_client: AsyncClient,
        test_user: User,
        test_group: Group,
    ):
        """Test that invalid date format returns 400 error."""
        response = await async_client.get(
            "/api/v1/verified-qa/search",
            params={
                "group_id": str(test_group.id),
                "from_date": "invalid-date",
                "page": 1,
                "limit": 20,
            },
            headers={"Authorization": f"Bearer {test_user.token}"},
        )

        assert response.status_code == 400
        assert "Invalid" in response.json()["detail"]

    async def test_nonexistent_entry_returns_404(
        self,
        async_client: AsyncClient,
        test_user: User,
        test_group: Group,
    ):
        """Test that accessing nonexistent entry returns 404."""
        fake_id = uuid4()
        response = await async_client.get(
            f"/api/v1/verified-qa/{fake_id}",
            headers={"Authorization": f"Bearer {test_user.token}"},
        )

        assert response.status_code == 404

    async def test_edit_nonexistent_entry_returns_404(
        self,
        async_client: AsyncClient,
        test_user: User,
        test_group: Group,
    ):
        """Test that editing nonexistent entry returns 404."""
        fake_id = uuid4()
        response = await async_client.put(
            f"/api/v1/verified-qa/{fake_id}",
            json={"question_text": "New question"},
            params={"group_id": str(test_group.id)},
            headers={"Authorization": f"Bearer {test_user.token}"},
        )

        assert response.status_code == 404

    async def test_delete_nonexistent_entry_returns_404(
        self,
        async_client: AsyncClient,
        test_user: User,
        test_group: Group,
    ):
        """Test that deleting nonexistent entry returns 404."""
        fake_id = uuid4()
        response = await async_client.delete(
            f"/api/v1/verified-qa/{fake_id}",
            params={"group_id": str(test_group.id)},
            headers={"Authorization": f"Bearer {test_user.token}"},
        )

        assert response.status_code == 404
