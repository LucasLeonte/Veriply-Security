"""Tests for Story 5.3: Approve & Edit Flow.

Tests for approve/edit functionality including:
- AC1: Approve button sends response, updates KB, removes item, auto-loads next
- AC2: Edit field allows modification, system records diff
- AC3: Success toast on send (frontend)
"""

import pytest
from uuid import uuid4
from datetime import datetime
from sqlalchemy import select

from app.models.confidence_log import ConfidenceLog, RoutingDecision
from app.models.bot import Bot
from app.models.user import User


class TestApproveEditFlow:
    """Tests for approve/edit HITL flow (Story 5.3)."""

    @pytest.mark.asyncio
    async def test_approve_without_edits_marks_resolved_and_updates_kb(
        self, client, db_session, test_user, test_bot, auth_headers
    ):
        """AC1: Approve marks item resolved and adds to Verified KB."""
        # Create a pending HITL item
        confidence_log = ConfidenceLog(
            bot_id=test_bot.id,
            tenant_id=test_user.tenant_id,
            query_id=uuid4(),
            query_text="What is your return policy?",
            retrieval_confidence=0.65,
            overall_confidence=0.65,
            threshold_used=0.8,
            routing_decision=RoutingDecision.hitl,
            hitl_resolved=False,
            is_verified_kb=False,
            metadata_json={
                "type": "chat",
                "ai_draft": "Our return policy allows 30-day returns for most items.",
                "citations": [],
            },
        )
        db_session.add(confidence_log)
        await db_session.commit()
        await db_session.refresh(confidence_log)

        # Approve the item without edits
        response = await client.post(
            f"/api/v1/hitl/queue/{confidence_log.id}/approve",
            json={},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "approved"
        assert data["item_id"] == str(confidence_log.id)
        assert data["was_edited"] is False
        assert data["verified_kb_updated"] is True
        assert data["diff"] is None
        assert data["resolved_answer"] == "Our return policy allows 30-day returns for most items."

        # Verify item is marked resolved in DB
        result = await db_session.execute(
            select(ConfidenceLog).where(ConfidenceLog.id == confidence_log.id)
        )
        updated_item = result.scalars().first()
        
        assert updated_item.hitl_resolved is True
        assert updated_item.is_verified_kb is True
        assert updated_item.resolution_user_id == test_user.id
        assert updated_item.resolution_timestamp is not None
        assert updated_item.metadata_json["resolution_action"] == "approved"
        assert updated_item.metadata_json["verified_kb_added"] is True
        assert updated_item.metadata_json["human_final_answer"] == "Our return policy allows 30-day returns for most items."

    @pytest.mark.asyncio
    async def test_approve_with_edits_records_diff(
        self, client, db_session, test_user, test_bot, auth_headers
    ):
        """AC2: Editing draft records diff between AI and human version."""
        ai_draft = "Our return policy allows 30-day returns."
        human_edit = "Our return policy allows 30-day returns for most items, except electronics which have a 14-day return window."

        # Create a pending HITL item
        confidence_log = ConfidenceLog(
            bot_id=test_bot.id,
            tenant_id=test_user.tenant_id,
            query_id=uuid4(),
            query_text="What is your return policy?",
            retrieval_confidence=0.65,
            overall_confidence=0.65,
            threshold_used=0.8,
            routing_decision=RoutingDecision.hitl,
            hitl_resolved=False,
            is_verified_kb=False,
            metadata_json={
                "type": "chat",
                "ai_draft": ai_draft,
                "citations": [],
            },
        )
        db_session.add(confidence_log)
        await db_session.commit()
        await db_session.refresh(confidence_log)

        # Approve with edits
        response = await client.post(
            f"/api/v1/hitl/queue/{confidence_log.id}/approve",
            json={"edits": human_edit},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "approved"
        assert data["was_edited"] is True
        assert data["verified_kb_updated"] is True
        assert data["resolved_answer"] == human_edit

        # Verify diff was recorded
        assert data["diff"] is not None
        assert data["diff"]["ai_version"] == ai_draft
        assert data["diff"]["human_version"] == human_edit
        assert data["diff"]["edited_by"] == str(test_user.id)
        assert "edited_at" in data["diff"]
        assert data["diff"]["char_diff"]["ai_length"] == len(ai_draft)
        assert data["diff"]["char_diff"]["human_length"] == len(human_edit)
        assert data["diff"]["char_diff"]["diff_length"] == len(human_edit) - len(ai_draft)

        # Verify in DB
        result = await db_session.execute(
            select(ConfidenceLog).where(ConfidenceLog.id == confidence_log.id)
        )
        updated_item = result.scalars().first()
        
        assert updated_item.hitl_resolved is True
        assert updated_item.is_verified_kb is True
        assert updated_item.metadata_json["resolution_action"] == "approved_with_edits"
        assert updated_item.metadata_json["human_edits"] == human_edit
        assert updated_item.metadata_json["diff"]["ai_version"] == ai_draft
        assert updated_item.metadata_json["diff"]["human_version"] == human_edit

    @pytest.mark.asyncio
    async def test_approve_nonexistent_item_returns_404(
        self, client, auth_headers
    ):
        """Approving a non-existent item returns 404."""
        fake_id = str(uuid4())
        response = await client.post(
            f"/api/v1/hitl/queue/{fake_id}/approve",
            json={},
            headers=auth_headers,
        )

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_approve_item_from_different_tenant_returns_404(
        self, client, db_session, test_user, test_bot, auth_headers
    ):
        """Cannot approve items from another tenant."""
        # Create item for a different tenant
        other_tenant_id = uuid4()
        confidence_log = ConfidenceLog(
            bot_id=test_bot.id,
            tenant_id=other_tenant_id,  # Different tenant
            query_id=uuid4(),
            query_text="Test question",
            retrieval_confidence=0.5,
            overall_confidence=0.5,
            threshold_used=0.8,
            routing_decision=RoutingDecision.hitl,
            hitl_resolved=False,
            metadata_json={"ai_draft": "Test answer"},
        )
        db_session.add(confidence_log)
        await db_session.commit()
        await db_session.refresh(confidence_log)

        # Try to approve with current user's auth
        response = await client.post(
            f"/api/v1/hitl/queue/{confidence_log.id}/approve",
            json={},
            headers=auth_headers,
        )

        assert response.status_code == 404  # Tenant isolation prevents access

    @pytest.mark.asyncio
    async def test_approve_already_resolved_item_updates_metadata(
        self, client, db_session, test_user, test_bot, auth_headers
    ):
        """Approving an already-resolved item updates its metadata."""
        # Create already-resolved item
        confidence_log = ConfidenceLog(
            bot_id=test_bot.id,
            tenant_id=test_user.tenant_id,
            query_id=uuid4(),
            query_text="Already resolved question",
            retrieval_confidence=0.6,
            overall_confidence=0.6,
            threshold_used=0.8,
            routing_decision=RoutingDecision.hitl,
            hitl_resolved=True,  # Already resolved
            resolution_user_id=test_user.id,
            resolution_timestamp=datetime.utcnow(),
            metadata_json={"ai_draft": "Original answer"},
        )
        db_session.add(confidence_log)
        await db_session.commit()
        await db_session.refresh(confidence_log)

        # Approve again (should succeed and update metadata)
        response = await client.post(
            f"/api/v1/hitl/queue/{confidence_log.id}/approve",
            json={"edits": "Updated answer"},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["resolved_answer"] == "Updated answer"

    @pytest.mark.asyncio
    async def test_approve_preserves_citations(
        self, client, db_session, test_user, test_bot, auth_headers
    ):
        """Approving preserves citation metadata."""
        citations = [
            {"source": "FAQ Document", "relevance": 0.95},
            {"source": "Policy Manual", "relevance": 0.88},
        ]

        confidence_log = ConfidenceLog(
            bot_id=test_bot.id,
            tenant_id=test_user.tenant_id,
            query_id=uuid4(),
            query_text="Question with citations",
            retrieval_confidence=0.7,
            overall_confidence=0.7,
            threshold_used=0.8,
            routing_decision=RoutingDecision.hitl,
            hitl_resolved=False,
            metadata_json={
                "ai_draft": "Answer with sources",
                "citations": citations,
            },
        )
        db_session.add(confidence_log)
        await db_session.commit()
        await db_session.refresh(confidence_log)

        # Approve the item
        response = await client.post(
            f"/api/v1/hitl/queue/{confidence_log.id}/approve",
            json={},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["citations"] == citations

    @pytest.mark.asyncio
    async def test_queue_excludes_approved_items(
        self, client, db_session, test_user, test_bot, auth_headers
    ):
        """AC1: Approved items are removed from queue (hitl_resolved=True)."""
        # Create 3 items
        items = []
        for i in range(3):
            item = ConfidenceLog(
                bot_id=test_bot.id,
                tenant_id=test_user.tenant_id,
                query_id=uuid4(),
                query_text=f"Question {i}",
                retrieval_confidence=0.6,
                overall_confidence=0.6,
                threshold_used=0.8,
                routing_decision=RoutingDecision.hitl,
                hitl_resolved=False,
                metadata_json={"ai_draft": f"Answer {i}"},
            )
            db_session.add(item)
            items.append(item)
        
        await db_session.commit()
        for item in items:
            await db_session.refresh(item)

        # Get queue - should have 3 items
        response = await client.get(
            "/api/v1/hitl/queue",
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.json()["stats"]["total"] == 3

        # Approve first item
        await client.post(
            f"/api/v1/hitl/queue/{items[0].id}/approve",
            json={},
            headers=auth_headers,
        )

        # Get queue again - should have 2 items (AC1: item removed from queue)
        response = await client.get(
            "/api/v1/hitl/queue",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["stats"]["total"] == 2
        assert str(items[0].id) not in [item["id"] for item in data["items"]]

    @pytest.mark.asyncio
    async def test_approve_sets_verified_kb_flag(
        self, client, db_session, test_user, test_bot, auth_headers
    ):
        """AC1: Approving sets is_verified_kb=True for future KB queries."""
        confidence_log = ConfidenceLog(
            bot_id=test_bot.id,
            tenant_id=test_user.tenant_id,
            query_id=uuid4(),
            query_text="KB test question",
            retrieval_confidence=0.6,
            overall_confidence=0.6,
            threshold_used=0.8,
            routing_decision=RoutingDecision.hitl,
            hitl_resolved=False,
            is_verified_kb=False,
            metadata_json={"ai_draft": "KB test answer"},
        )
        db_session.add(confidence_log)
        await db_session.commit()
        await db_session.refresh(confidence_log)

        # Approve
        response = await client.post(
            f"/api/v1/hitl/queue/{confidence_log.id}/approve",
            json={},
            headers=auth_headers,
        )

        assert response.status_code == 200
        assert response.json()["verified_kb_updated"] is True

        # Verify DB flag
        result = await db_session.execute(
            select(ConfidenceLog).where(ConfidenceLog.id == confidence_log.id)
        )
        updated = result.scalars().first()
        assert updated.is_verified_kb is True
