"""
Tests for feedback submission API endpoints.
"""

import pytest
from uuid import uuid4, UUID
from datetime import datetime, timedelta

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models import Feedback, FeedbackType, FeedbackReason, ModerationAlert, UserAbuseSuspicion, Bot


@pytest.mark.asyncio
class TestFeedbackSubmission:
    """Test feedback submission endpoint POST /api/v1/bots/{bot_id}/feedback"""

    async def test_submit_positive_feedback(self, client: AsyncClient, auth_headers: dict, db: AsyncSession, test_bot: Bot):
        """TC1: Successfully submit positive feedback"""
        payload = {
            "answer_id": str(uuid4()),
            "message_id": "msg-123",
            "type": "positive",
            "session_id": "session-abc",
        }
        
        response = await client.post(
            f"/api/v1/bots/{test_bot.id}/feedback",
            json=payload,
            headers=auth_headers,
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "feedback_id" in data
        assert data["message"] == "Feedback recorded"

    async def test_submit_negative_feedback_with_reason(self, client: AsyncClient, auth_headers: dict, db: AsyncSession, test_bot: Bot):
        """TC2: Successfully submit negative feedback with reason"""
        payload = {
            "answer_id": str(uuid4()),
            "message_id": "msg-456",
            "type": "negative",
            "reason": "not_helpful",
            "session_id": "session-xyz",
        }
        
        response = await client.post(
            f"/api/v1/bots/{test_bot.id}/feedback",
            json=payload,
            headers=auth_headers,
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    async def test_submit_negative_with_additional_notes(self, client: AsyncClient, auth_headers: dict, test_bot: Bot):
        """TC3: Submit negative feedback with additional notes"""
        payload = {
            "answer_id": str(uuid4()),
            "message_id": "msg-789",
            "type": "negative",
            "reason": "other",
            "additional_notes": "The response was too generic and did not address my specific question.",
            "session_id": "session-123",
        }
        
        response = await client.post(
            f"/api/v1/bots/{test_bot.id}/feedback",
            json=payload,
            headers=auth_headers,
        )
        
        assert response.status_code == 200

    async def test_reject_negative_without_reason(self, client: AsyncClient, auth_headers: dict, test_bot: Bot):
        """TC4: Reject negative feedback without reason"""
        payload = {
            "answer_id": str(uuid4()),
            "message_id": "msg-999",
            "type": "negative",
            "session_id": "session-fail",
        }
        
        response = await client.post(
            f"/api/v1/bots/{test_bot.id}/feedback",
            json=payload,
            headers=auth_headers,
        )
        
        assert response.status_code == 400
        assert "Reason is required for negative feedback" in response.text

    async def test_reject_invalid_type(self, client: AsyncClient, auth_headers: dict, test_bot: Bot):
        """TC5: Reject invalid feedback type"""
        payload = {
            "answer_id": str(uuid4()),
            "message_id": "msg-invalid",
            "type": "neutral",  # Invalid type
            "session_id": "session-bad",
        }
        
        response = await client.post(
            f"/api/v1/bots/{test_bot.id}/feedback",
            json=payload,
            headers=auth_headers,
        )
        
        assert response.status_code == 400
        assert "Invalid feedback type" in response.text

    async def test_reject_invalid_reason(self, client: AsyncClient, auth_headers: dict, test_bot: Bot):
        """TC6: Reject invalid feedback reason"""
        payload = {
            "answer_id": str(uuid4()),
            "message_id": "msg-bad",
            "type": "negative",
            "reason": "invalid_reason",
            "session_id": "session-bad",
        }
        
        response = await client.post(
            f"/api/v1/bots/{test_bot.id}/feedback",
            json=payload,
            headers=auth_headers,
        )
        
        assert response.status_code == 400

    async def test_reject_additional_notes_exceeding_500_chars(self, client: AsyncClient, auth_headers: dict, test_bot: Bot):
        """TC7: Reject feedback with additional_notes > 500 characters"""
        long_text = "x" * 501
        payload = {
            "answer_id": str(uuid4()),
            "message_id": "msg-long",
            "type": "negative",
            "reason": "other",
            "additional_notes": long_text,
            "session_id": "session-long",
        }
        
        response = await client.post(
            f"/api/v1/bots/{test_bot.id}/feedback",
            json=payload,
            headers=auth_headers,
        )
        
        assert response.status_code == 400
        assert "500 characters" in response.text

    async def test_reject_nonexistent_bot(self, client: AsyncClient, auth_headers: dict):
        """TC8: Reject feedback for non-existent bot"""
        fake_bot_id = uuid4()
        payload = {
            "answer_id": str(uuid4()),
            "message_id": "msg-fake",
            "type": "positive",
            "session_id": "session-fake",
        }
        
        response = await client.post(
            f"/api/v1/bots/{fake_bot_id}/feedback",
            json=payload,
            headers=auth_headers,
        )
        
        assert response.status_code == 404
        assert "Bot not found" in response.text

    async def test_reject_unauthorized(self, client: AsyncClient, test_bot: Bot):
        """TC9: Reject feedback without authentication"""
        payload = {
            "answer_id": str(uuid4()),
            "message_id": "msg-unauth",
            "type": "positive",
            "session_id": "session-unauth",
        }
        
        response = await client.post(
            f"/api/v1/bots/{test_bot.id}/feedback",
            json=payload,
        )
        
        assert response.status_code == 401

    async def test_rate_limiting_20_per_5_minutes(self, client: AsyncClient, auth_headers: dict, test_bot: Bot):
        """TC10: Enforce rate limiting at 20 submissions per session in 5 minutes"""
        session_id = "session-ratelimit"
        
        # Submit 20 feedback items
        for i in range(20):
            payload = {
                "answer_id": str(uuid4()),
                "message_id": f"msg-{i}",
                "type": "positive",
                "session_id": session_id,
            }
            response = await client.post(
                f"/api/v1/bots/{test_bot.id}/feedback",
                json=payload,
                headers=auth_headers,
            )
            assert response.status_code == 200
        
        # 21st should be rate limited
        payload = {
            "answer_id": str(uuid4()),
            "message_id": "msg-21",
            "type": "positive",
            "session_id": session_id,
        }
        response = await client.post(
            f"/api/v1/bots/{test_bot.id}/feedback",
            json=payload,
            headers=auth_headers,
        )
        
        assert response.status_code == 429
        assert "Please wait before providing more feedback" in response.text

    async def test_upsert_feedback_same_user_answer(self, client: AsyncClient, auth_headers: dict, db: AsyncSession, test_bot: Bot, test_user_id: UUID):
        """TC11: Upsert behavior - one feedback per user per answer"""
        answer_id = uuid4()
        
        # First submission: positive
        payload1 = {
            "answer_id": str(answer_id),
            "message_id": "msg-same",
            "type": "positive",
            "session_id": "session-upsert",
        }
        response1 = await client.post(
            f"/api/v1/bots/{test_bot.id}/feedback",
            json=payload1,
            headers=auth_headers,
        )
        assert response1.status_code == 200
        feedback_id_1 = response1.json()["feedback_id"]
        
        # Second submission: negative (should update, not create new)
        payload2 = {
            "answer_id": str(answer_id),
            "message_id": "msg-same",
            "type": "negative",
            "reason": "not_helpful",
            "session_id": "session-upsert",
        }
        response2 = await client.post(
            f"/api/v1/bots/{test_bot.id}/feedback",
            json=payload2,
            headers=auth_headers,
        )
        assert response2.status_code == 200
        
        # Check database: should be only 1 feedback entry
        result = await db.execute(
            select(Feedback).where(
                Feedback.user_id == test_user_id,
                Feedback.answer_id == answer_id,
            )
        )
        feedbacks = result.scalars().all()
        assert len(feedbacks) == 1
        assert feedbacks[0].type == FeedbackType.NEGATIVE
        assert feedbacks[0].reason == FeedbackReason.NOT_HELPFUL

    async def test_stores_user_id_session_id_ip_address(self, client: AsyncClient, auth_headers: dict, db: AsyncSession, test_bot: Bot, test_user_id: UUID):
        """TC12: Stores user_id, session_id, ip_address for audit trail"""
        payload = {
            "answer_id": str(uuid4()),
            "message_id": "msg-audit",
            "type": "positive",
            "session_id": "session-audit-123",
        }
        
        # Add X-Forwarded-For header to simulate proxy
        headers_with_ip = {**auth_headers, "X-Forwarded-For": "203.0.113.45, 10.0.0.1"}
        
        response = await client.post(
            f"/api/v1/bots/{test_bot.id}/feedback",
            json=payload,
            headers=headers_with_ip,
        )
        
        assert response.status_code == 200
        feedback_id = UUID(response.json()["feedback_id"])
        
        # Verify database entry
        feedback = await db.get(Feedback, feedback_id)
        assert feedback is not None
        assert feedback.user_id == test_user_id
        assert feedback.session_id == "session-audit-123"
        assert feedback.ip_address == "203.0.113.45"  # First IP from X-Forwarded-For

    async def test_creates_moderation_alert_at_3_harmful(self, client: AsyncClient, auth_headers: dict, db: AsyncSession, test_bot: Bot):
        """TC13: Creates moderation alert when 3+ harmful feedback on same answer in 24h"""
        answer_id = uuid4()
        
        # Submit 3 harmful feedback items from different users
        for i in range(3):
            payload = {
                "answer_id": str(answer_id),
                "message_id": f"msg-harmful-{i}",
                "type": "negative",
                "reason": "harmful",
                "session_id": f"session-{i}",
            }
            response = await client.post(
                f"/api/v1/bots/{test_bot.id}/feedback",
                json=payload,
                headers=auth_headers,
            )
            assert response.status_code == 200
            
            if i == 2:  # On 3rd submission
                assert response.json()["moderation_alert_id"] is not None

    async def test_creates_abuse_suspicion_at_5_harmful_per_user(self, client: AsyncClient, auth_headers: dict, db: AsyncSession, test_bot: Bot):
        """TC14: Flags user abuse after 5+ harmful feedback in 1 hour"""
        # Submit 5 harmful feedback items from same user
        for i in range(5):
            payload = {
                "answer_id": str(uuid4()),
                "message_id": f"msg-abuse-{i}",
                "type": "negative",
                "reason": "harmful",
                "session_id": "session-abuse",
            }
            response = await client.post(
                f"/api/v1/bots/{test_bot.id}/feedback",
                json=payload,
                headers=auth_headers,
            )
            assert response.status_code == 200
            
            if i == 4:  # On 5th submission
                assert response.json()["abuse_suspicion_id"] is not None

    async def test_tenant_isolation_different_tenant_bot(self, client: AsyncClient, auth_headers: dict, other_tenant_bot: Bot):
        """TC15: Reject feedback for bot from different tenant"""
        payload = {
            "answer_id": str(uuid4()),
            "message_id": "msg-other-tenant",
            "type": "positive",
            "session_id": "session-other",
        }
        
        response = await client.post(
            f"/api/v1/bots/{other_tenant_bot.id}/feedback",
            json=payload,
            headers=auth_headers,
        )
        
        assert response.status_code == 403
        assert "Access denied" in response.text


@pytest.mark.asyncio
class TestFeedbackStatsEndpoint:
    """Test feedback stats endpoint GET /api/v1/bots/{bot_id}/feedback/stats"""

    async def test_get_feedback_stats_default_24h(self, client: AsyncClient, auth_headers: dict, test_bot: Bot, db: AsyncSession):
        """TC16: Get feedback stats for default 24 hours"""
        response = await client.get(
            f"/api/v1/bots/{test_bot.id}/feedback/stats",
            headers=auth_headers,
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "positive_count" in data
        assert "negative_count" in data
        assert "negative_reasons" in data
        assert "harmful_count" in data
        assert data["window_hours"] == 24

    async def test_get_feedback_stats_custom_window(self, client: AsyncClient, auth_headers: dict, test_bot: Bot):
        """TC17: Get feedback stats for custom time window"""
        response = await client.get(
            f"/api/v1/bots/{test_bot.id}/feedback/stats?hours=48",
            headers=auth_headers,
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["window_hours"] == 48

    async def test_feedback_stats_counts_correctly(self, client: AsyncClient, auth_headers: dict, test_bot: Bot, db: AsyncSession, test_user_id: UUID, tenant_id: UUID):
        """TC18: Stats counts feedback correctly"""
        # Create test feedback data
        answer_id = uuid4()
        
        feedback_positive = Feedback(
            tenant_id=tenant_id,
            bot_id=test_bot.id,
            user_id=test_user_id,
            answer_id=answer_id,
            message_id="msg-stats-1",
            type=FeedbackType.POSITIVE,
        )
        feedback_negative = Feedback(
            tenant_id=tenant_id,
            bot_id=test_bot.id,
            user_id=test_user_id,
            answer_id=uuid4(),
            message_id="msg-stats-2",
            type=FeedbackType.NEGATIVE,
            reason=FeedbackReason.NOT_HELPFUL,
        )
        
        db.add_all([feedback_positive, feedback_negative])
        await db.commit()
        
        response = await client.get(
            f"/api/v1/bots/{test_bot.id}/feedback/stats",
            headers=auth_headers,
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 2
        assert data["positive_count"] >= 1
        assert data["negative_count"] >= 1

    async def test_stats_unauthorized(self, client: AsyncClient, test_bot: Bot):
        """TC19: Reject stats request without authentication"""
        response = await client.get(
            f"/api/v1/bots/{test_bot.id}/feedback/stats",
        )
        
        assert response.status_code == 401

    async def test_stats_tenant_isolation(self, client: AsyncClient, auth_headers: dict, other_tenant_bot: Bot):
        """TC20: Cannot get stats for bot from different tenant"""
        response = await client.get(
            f"/api/v1/bots/{other_tenant_bot.id}/feedback/stats",
            headers=auth_headers,
        )
        
        # Should return 0 counts or error depending on implementation
        assert response.status_code in [200, 403]


@pytest.mark.asyncio
class TestModerationAlertsEndpoint:
    """Test moderation alerts endpoint GET /api/v1/bots/moderation/alerts"""

    async def test_list_moderation_alerts(self, client: AsyncClient, auth_headers: dict, db: AsyncSession, test_bot: Bot, tenant_id: UUID):
        """TC21: List moderation alerts for tenant"""
        # Create test alert
        alert = ModerationAlert(
            tenant_id=tenant_id,
            bot_id=test_bot.id,
            answer_id=uuid4(),
            feedback_count=3,
            user_ids="user1,user2,user3",
        )
        db.add(alert)
        await db.commit()
        
        response = await client.get(
            "/api/v1/bots/moderation/alerts",
            headers=auth_headers,
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    async def test_filter_alerts_by_bot(self, client: AsyncClient, auth_headers: dict, db: AsyncSession, test_bot: Bot, tenant_id: UUID):
        """TC22: Filter moderation alerts by bot_id"""
        alert = ModerationAlert(
            tenant_id=tenant_id,
            bot_id=test_bot.id,
            answer_id=uuid4(),
            feedback_count=5,
            user_ids="user1,user2,user3,user4,user5",
        )
        db.add(alert)
        await db.commit()
        
        response = await client.get(
            f"/api/v1/bots/moderation/alerts?bot_id={test_bot.id}",
            headers=auth_headers,
        )
        
        assert response.status_code == 200
        data = response.json()
        for item in data:
            assert item["bot_id"] == str(test_bot.id)

    async def test_moderation_alerts_unauthorized(self, client: AsyncClient):
        """TC23: Reject moderation alerts without authentication"""
        response = await client.get("/api/v1/bots/moderation/alerts")
        
        assert response.status_code == 401


@pytest.mark.asyncio
class TestUserAbuseSuspicionEndpoint:
    """Test user abuse suspicion endpoint GET /api/v1/bots/moderation/user-abuse"""

    async def test_list_user_abuse_suspicions_admin_only(self, client: AsyncClient, admin_auth_headers: dict, db: AsyncSession, test_bot: Bot, tenant_id: UUID, test_user_id: UUID):
        """TC24: Admin can list user abuse suspicions"""
        suspicion = UserAbuseSuspicion(
            tenant_id=tenant_id,
            user_id=test_user_id,
            bot_id=test_bot.id,
            ip_address="203.0.113.50",
            feedback_ids="fb1,fb2,fb3,fb4,fb5",
            window_start=datetime.utcnow() - timedelta(hours=1),
        )
        db.add(suspicion)
        await db.commit()
        
        response = await client.get(
            "/api/v1/bots/moderation/user-abuse",
            headers=admin_auth_headers,
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    async def test_user_abuse_forbidden_non_admin(self, client: AsyncClient, auth_headers: dict):
        """TC25: Non-admin users cannot access user abuse endpoint"""
        response = await client.get(
            "/api/v1/bots/moderation/user-abuse",
            headers=auth_headers,
        )
        
        assert response.status_code == 403
        assert "Admin or owner role required" in response.text
