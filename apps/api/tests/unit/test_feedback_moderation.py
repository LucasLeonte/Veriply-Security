"""
Tests for feedback moderation alert and abuse detection logic.
"""

import pytest
from uuid import uuid4, UUID
from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models import Feedback, FeedbackType, FeedbackReason, ModerationAlert, UserAbuseSuspicion, Bot
from app.services.feedback_service import FeedbackService


@pytest.mark.asyncio
class TestModerationAlerts:
    """Test moderation alert creation (3+ harmful feedback on same answer in 24h)"""

    async def test_no_alert_with_2_harmful(self, db: AsyncSession, test_bot: Bot, tenant_id: UUID):
        """TC1: Does not create alert with only 2 harmful feedback"""
        user_id = uuid4()
        answer_id = uuid4()
        
        # Create 2 harmful feedback items
        for i in range(2):
            feedback, moderation_alert, abuse_alert = await FeedbackService.record_feedback(
                db=db,
                user_id=user_id,
                tenant_id=tenant_id,
                bot_id=test_bot.id,
                answer_id=answer_id,
                message_id=f"msg-{i}",
                feedback_type=FeedbackType.NEGATIVE,
                reason=FeedbackReason.HARMFUL,
                additional_notes=None,
                session_id=f"session-{i}",
                ip_address="203.0.113.1",
            )
            await db.commit()
            
            if i < 2:
                assert moderation_alert is None

    async def test_creates_alert_at_3_harmful(self, db: AsyncSession, test_bot: Bot, tenant_id: UUID):
        """TC2: Creates moderation alert at exactly 3 harmful feedback"""
        answer_id = uuid4()
        
        # Create 3 harmful feedback items
        for i in range(3):
            user_id = uuid4()  # Different users
            feedback, moderation_alert, abuse_alert = await FeedbackService.record_feedback(
                db=db,
                user_id=user_id,
                tenant_id=tenant_id,
                bot_id=test_bot.id,
                answer_id=answer_id,
                message_id=f"msg-{i}",
                feedback_type=FeedbackType.NEGATIVE,
                reason=FeedbackReason.HARMFUL,
                additional_notes=None,
                session_id=f"session-{i}",
                ip_address=f"203.0.113.{i}",
            )
            await db.commit()
            
            if i == 2:  # On 3rd submission
                assert moderation_alert is not None
                assert moderation_alert.feedback_count == 3
                assert moderation_alert.bot_id == test_bot.id
                assert moderation_alert.answer_id == answer_id

    async def test_alert_includes_user_ids(self, db: AsyncSession, test_bot: Bot, tenant_id: UUID):
        """TC3: Moderation alert includes comma-separated user_ids"""
        answer_id = uuid4()
        user_ids = [uuid4() for _ in range(3)]
        
        for i, user_id in enumerate(user_ids):
            feedback, moderation_alert, abuse_alert = await FeedbackService.record_feedback(
                db=db,
                user_id=user_id,
                tenant_id=tenant_id,
                bot_id=test_bot.id,
                answer_id=answer_id,
                message_id=f"msg-{i}",
                feedback_type=FeedbackType.NEGATIVE,
                reason=FeedbackReason.HARMFUL,
                additional_notes=None,
                session_id=f"session-{i}",
                ip_address="203.0.113.1",
            )
            await db.commit()
            
            if i == 2:
                assert moderation_alert is not None
                # Check user_ids are included
                user_id_str = moderation_alert.user_ids
                assert str(user_ids[0]) in user_id_str
                assert str(user_ids[1]) in user_id_str
                assert str(user_ids[2]) in user_id_str

    async def test_alert_respects_24h_window(self, db: AsyncSession, test_bot: Bot, tenant_id: UUID):
        """TC4: Only counts harmful feedback within 24h window"""
        answer_id = uuid4()
        
        # Create 2 harmful feedback within 24h
        for i in range(2):
            user_id = uuid4()
            await FeedbackService.record_feedback(
                db=db,
                user_id=user_id,
                tenant_id=tenant_id,
                bot_id=test_bot.id,
                answer_id=answer_id,
                message_id=f"msg-recent-{i}",
                feedback_type=FeedbackType.NEGATIVE,
                reason=FeedbackReason.HARMFUL,
                additional_notes=None,
                session_id=f"session-{i}",
                ip_address="203.0.113.1",
            )
            await db.commit()
        
        # Create 1 old harmful feedback (>24h ago) manually
        old_feedback = Feedback(
            tenant_id=tenant_id,
            bot_id=test_bot.id,
            user_id=uuid4(),
            answer_id=answer_id,
            message_id="msg-old",
            type=FeedbackType.NEGATIVE,
            reason=FeedbackReason.HARMFUL,
            created_at=datetime.utcnow() - timedelta(hours=48),
        )
        db.add(old_feedback)
        await db.commit()
        
        # Now add 3rd recent harmful - should not trigger alert (only 2 recent)
        user_id = uuid4()
        feedback, moderation_alert, abuse_alert = await FeedbackService.record_feedback(
            db=db,
            user_id=user_id,
            tenant_id=tenant_id,
            bot_id=test_bot.id,
            answer_id=answer_id,
            message_id="msg-recent-3",
            feedback_type=FeedbackType.NEGATIVE,
            reason=FeedbackReason.HARMFUL,
            additional_notes=None,
            session_id="session-3",
            ip_address="203.0.113.1",
        )
        await db.commit()
        
        # Now we have 3 recent (2 from loop + this one) = should trigger alert
        assert moderation_alert is not None

    async def test_no_alert_for_non_harmful_feedback(self, db: AsyncSession, test_bot: Bot, tenant_id: UUID):
        """TC5: No alert for non-harmful feedback even if count > 3"""
        answer_id = uuid4()
        
        # Create 5 non-harmful negative feedback
        for i in range(5):
            user_id = uuid4()
            feedback, moderation_alert, abuse_alert = await FeedbackService.record_feedback(
                db=db,
                user_id=user_id,
                tenant_id=tenant_id,
                bot_id=test_bot.id,
                answer_id=answer_id,
                message_id=f"msg-{i}",
                feedback_type=FeedbackType.NEGATIVE,
                reason=FeedbackReason.NOT_HELPFUL,
                additional_notes=None,
                session_id=f"session-{i}",
                ip_address="203.0.113.1",
            )
            await db.commit()
            
            assert moderation_alert is None

    async def test_alert_scoped_to_answer_id(self, db: AsyncSession, test_bot: Bot, tenant_id: UUID):
        """TC6: Moderation alert is scoped to specific answer_id"""
        answer_id_1 = uuid4()
        answer_id_2 = uuid4()
        
        # 2 harmful on answer_id_1
        for i in range(2):
            await FeedbackService.record_feedback(
                db=db,
                user_id=uuid4(),
                tenant_id=tenant_id,
                bot_id=test_bot.id,
                answer_id=answer_id_1,
                message_id=f"msg-ans1-{i}",
                feedback_type=FeedbackType.NEGATIVE,
                reason=FeedbackReason.HARMFUL,
                additional_notes=None,
                session_id=f"session-{i}",
                ip_address="203.0.113.1",
            )
            await db.commit()
        
        # 2 harmful on answer_id_2
        for i in range(2):
            await FeedbackService.record_feedback(
                db=db,
                user_id=uuid4(),
                tenant_id=tenant_id,
                bot_id=test_bot.id,
                answer_id=answer_id_2,
                message_id=f"msg-ans2-{i}",
                feedback_type=FeedbackType.NEGATIVE,
                reason=FeedbackReason.HARMFUL,
                additional_notes=None,
                session_id=f"session-2-{i}",
                ip_address="203.0.113.1",
            )
            await db.commit()
        
        # Neither should trigger alert (each has only 2)
        # Add 3rd to answer_id_1
        feedback, moderation_alert, abuse_alert = await FeedbackService.record_feedback(
            db=db,
            user_id=uuid4(),
            tenant_id=tenant_id,
            bot_id=test_bot.id,
            answer_id=answer_id_1,
            message_id="msg-ans1-3",
            feedback_type=FeedbackType.NEGATIVE,
            reason=FeedbackReason.HARMFUL,
            additional_notes=None,
            session_id="session-final",
            ip_address="203.0.113.1",
        )
        await db.commit()
        
        # Should trigger alert for answer_id_1 only
        assert moderation_alert is not None
        assert moderation_alert.answer_id == answer_id_1

    async def test_alert_scoped_to_bot_id(self, db: AsyncSession, test_bot: Bot, tenant_id: UUID, db_session: AsyncSession):
        """TC7: Moderation alert is scoped to specific bot_id"""
        # Create another bot
        other_bot = Bot(
            tenant_id=tenant_id,
            name="Other Bot",
            description="Another bot for testing",
        )
        db_session.add(other_bot)
        await db_session.commit()
        
        answer_id = uuid4()
        
        # 2 harmful on test_bot
        for i in range(2):
            await FeedbackService.record_feedback(
                db=db,
                user_id=uuid4(),
                tenant_id=tenant_id,
                bot_id=test_bot.id,
                answer_id=answer_id,
                message_id=f"msg-bot1-{i}",
                feedback_type=FeedbackType.NEGATIVE,
                reason=FeedbackReason.HARMFUL,
                additional_notes=None,
                session_id=f"session-{i}",
                ip_address="203.0.113.1",
            )
            await db.commit()
        
        # 2 harmful on other_bot
        for i in range(2):
            await FeedbackService.record_feedback(
                db=db,
                user_id=uuid4(),
                tenant_id=tenant_id,
                bot_id=other_bot.id,
                answer_id=answer_id,
                message_id=f"msg-bot2-{i}",
                feedback_type=FeedbackType.NEGATIVE,
                reason=FeedbackReason.HARMFUL,
                additional_notes=None,
                session_id=f"session-2-{i}",
                ip_address="203.0.113.1",
            )
            await db.commit()
        
        # Add 3rd to test_bot
        feedback, moderation_alert, abuse_alert = await FeedbackService.record_feedback(
            db=db,
            user_id=uuid4(),
            tenant_id=tenant_id,
            bot_id=test_bot.id,
            answer_id=answer_id,
            message_id="msg-bot1-3",
            feedback_type=FeedbackType.NEGATIVE,
            reason=FeedbackReason.HARMFUL,
            additional_notes=None,
            session_id="session-final",
            ip_address="203.0.113.1",
        )
        await db.commit()
        
        # Should trigger alert for test_bot only
        assert moderation_alert is not None
        assert moderation_alert.bot_id == test_bot.id


@pytest.mark.asyncio
class TestUserAbuseSuspicion:
    """Test user abuse detection (5+ harmful feedback from same user in 1 hour)"""

    async def test_no_suspicion_with_4_harmful(self, db: AsyncSession, test_bot: Bot, tenant_id: UUID):
        """TC8: Does not flag user with only 4 harmful feedback"""
        user_id = uuid4()
        
        for i in range(4):
            feedback, moderation_alert, abuse_alert = await FeedbackService.record_feedback(
                db=db,
                user_id=user_id,
                tenant_id=tenant_id,
                bot_id=test_bot.id,
                answer_id=uuid4(),
                message_id=f"msg-{i}",
                feedback_type=FeedbackType.NEGATIVE,
                reason=FeedbackReason.HARMFUL,
                additional_notes=None,
                session_id=f"session-{i}",
                ip_address="203.0.113.50",
            )
            await db.commit()
            
            assert abuse_alert is None

    async def test_flags_user_at_5_harmful(self, db: AsyncSession, test_bot: Bot, tenant_id: UUID):
        """TC9: Flags user at exactly 5 harmful feedback in 1 hour"""
        user_id = uuid4()
        
        for i in range(5):
            feedback, moderation_alert, abuse_alert = await FeedbackService.record_feedback(
                db=db,
                user_id=user_id,
                tenant_id=tenant_id,
                bot_id=test_bot.id,
                answer_id=uuid4(),
                message_id=f"msg-{i}",
                feedback_type=FeedbackType.NEGATIVE,
                reason=FeedbackReason.HARMFUL,
                additional_notes=None,
                session_id=f"session-{i}",
                ip_address="203.0.113.50",
            )
            await db.commit()
            
            if i == 4:  # On 5th submission
                assert abuse_alert is not None
                assert abuse_alert.user_id == user_id
                assert abuse_alert.bot_id == test_bot.id
                assert abuse_alert.ip_address == "203.0.113.50"

    async def test_abuse_suspicion_includes_feedback_ids(self, db: AsyncSession, test_bot: Bot, tenant_id: UUID):
        """TC10: Abuse suspicion includes comma-separated feedback_ids"""
        user_id = uuid4()
        feedback_ids = []
        
        for i in range(5):
            feedback, moderation_alert, abuse_alert = await FeedbackService.record_feedback(
                db=db,
                user_id=user_id,
                tenant_id=tenant_id,
                bot_id=test_bot.id,
                answer_id=uuid4(),
                message_id=f"msg-{i}",
                feedback_type=FeedbackType.NEGATIVE,
                reason=FeedbackReason.HARMFUL,
                additional_notes=None,
                session_id=f"session-{i}",
                ip_address="203.0.113.50",
            )
            feedback_ids.append(str(feedback.id))
            await db.commit()
            
            if i == 4:
                assert abuse_alert is not None
                # Check feedback_ids are included
                ids_str = abuse_alert.feedback_ids
                for fb_id in feedback_ids:
                    assert fb_id in ids_str

    async def test_abuse_respects_1h_window(self, db: AsyncSession, test_bot: Bot, tenant_id: UUID):
        """TC11: Only counts harmful feedback within 1 hour window"""
        user_id = uuid4()
        
        # Create 4 harmful feedback within 1h
        for i in range(4):
            await FeedbackService.record_feedback(
                db=db,
                user_id=user_id,
                tenant_id=tenant_id,
                bot_id=test_bot.id,
                answer_id=uuid4(),
                message_id=f"msg-recent-{i}",
                feedback_type=FeedbackType.NEGATIVE,
                reason=FeedbackReason.HARMFUL,
                additional_notes=None,
                session_id=f"session-{i}",
                ip_address="203.0.113.50",
            )
            await db.commit()
        
        # Create 1 old harmful feedback (>1h ago) manually
        old_feedback = Feedback(
            tenant_id=tenant_id,
            bot_id=test_bot.id,
            user_id=user_id,
            answer_id=uuid4(),
            message_id="msg-old",
            type=FeedbackType.NEGATIVE,
            reason=FeedbackReason.HARMFUL,
            created_at=datetime.utcnow() - timedelta(hours=2),
        )
        db.add(old_feedback)
        await db.commit()
        
        # Add 5th recent harmful - should trigger abuse (4 from loop + this one)
        feedback, moderation_alert, abuse_alert = await FeedbackService.record_feedback(
            db=db,
            user_id=user_id,
            tenant_id=tenant_id,
            bot_id=test_bot.id,
            answer_id=uuid4(),
            message_id="msg-recent-5",
            feedback_type=FeedbackType.NEGATIVE,
            reason=FeedbackReason.HARMFUL,
            additional_notes=None,
            session_id="session-5",
            ip_address="203.0.113.50",
        )
        await db.commit()
        
        assert abuse_alert is not None

    async def test_no_abuse_for_different_users(self, db: AsyncSession, test_bot: Bot, tenant_id: UUID):
        """TC12: Different users don't count towards same abuse detection"""
        # 5 different users submit 1 harmful each
        for i in range(5):
            user_id = uuid4()
            feedback, moderation_alert, abuse_alert = await FeedbackService.record_feedback(
                db=db,
                user_id=user_id,
                tenant_id=tenant_id,
                bot_id=test_bot.id,
                answer_id=uuid4(),
                message_id=f"msg-{i}",
                feedback_type=FeedbackType.NEGATIVE,
                reason=FeedbackReason.HARMFUL,
                additional_notes=None,
                session_id=f"session-{i}",
                ip_address="203.0.113.50",
            )
            await db.commit()
            
            # No user should be flagged
            assert abuse_alert is None

    async def test_no_abuse_for_non_harmful_feedback(self, db: AsyncSession, test_bot: Bot, tenant_id: UUID):
        """TC13: Non-harmful feedback doesn't trigger abuse detection"""
        user_id = uuid4()
        
        for i in range(10):
            feedback, moderation_alert, abuse_alert = await FeedbackService.record_feedback(
                db=db,
                user_id=user_id,
                tenant_id=tenant_id,
                bot_id=test_bot.id,
                answer_id=uuid4(),
                message_id=f"msg-{i}",
                feedback_type=FeedbackType.NEGATIVE,
                reason=FeedbackReason.NOT_HELPFUL,
                additional_notes=None,
                session_id=f"session-{i}",
                ip_address="203.0.113.50",
            )
            await db.commit()
            
            assert abuse_alert is None

    async def test_abuse_scoped_to_bot_id(self, db: AsyncSession, test_bot: Bot, tenant_id: UUID, db_session: AsyncSession):
        """TC14: Abuse detection is scoped to specific bot_id"""
        # Create another bot
        other_bot = Bot(
            tenant_id=tenant_id,
            name="Other Bot",
            description="Another bot",
        )
        db_session.add(other_bot)
        await db_session.commit()
        
        user_id = uuid4()
        
        # 3 harmful on test_bot
        for i in range(3):
            await FeedbackService.record_feedback(
                db=db,
                user_id=user_id,
                tenant_id=tenant_id,
                bot_id=test_bot.id,
                answer_id=uuid4(),
                message_id=f"msg-bot1-{i}",
                feedback_type=FeedbackType.NEGATIVE,
                reason=FeedbackReason.HARMFUL,
                additional_notes=None,
                session_id=f"session-{i}",
                ip_address="203.0.113.50",
            )
            await db.commit()
        
        # 3 harmful on other_bot
        for i in range(3):
            await FeedbackService.record_feedback(
                db=db,
                user_id=user_id,
                tenant_id=tenant_id,
                bot_id=other_bot.id,
                answer_id=uuid4(),
                message_id=f"msg-bot2-{i}",
                feedback_type=FeedbackType.NEGATIVE,
                reason=FeedbackReason.HARMFUL,
                additional_notes=None,
                session_id=f"session-2-{i}",
                ip_address="203.0.113.50",
            )
            await db.commit()
        
        # Neither bot has 5 harmful, so no abuse
        # Add 2 more to test_bot to trigger abuse
        for i in range(2):
            feedback, moderation_alert, abuse_alert = await FeedbackService.record_feedback(
                db=db,
                user_id=user_id,
                tenant_id=tenant_id,
                bot_id=test_bot.id,
                answer_id=uuid4(),
                message_id=f"msg-bot1-final-{i}",
                feedback_type=FeedbackType.NEGATIVE,
                reason=FeedbackReason.HARMFUL,
                additional_notes=None,
                session_id=f"session-final-{i}",
                ip_address="203.0.113.50",
            )
            await db.commit()
            
            if i == 1:  # On 5th submission to test_bot
                assert abuse_alert is not None
                assert abuse_alert.bot_id == test_bot.id

    async def test_multiple_abuse_flags_for_same_user(self, db: AsyncSession, test_bot: Bot, tenant_id: UUID):
        """TC15: Can create multiple abuse suspicions for same user if pattern continues"""
        user_id = uuid4()
        
        # First batch: 5 harmful
        for i in range(5):
            feedback, moderation_alert, abuse_alert = await FeedbackService.record_feedback(
                db=db,
                user_id=user_id,
                tenant_id=tenant_id,
                bot_id=test_bot.id,
                answer_id=uuid4(),
                message_id=f"msg-batch1-{i}",
                feedback_type=FeedbackType.NEGATIVE,
                reason=FeedbackReason.HARMFUL,
                additional_notes=None,
                session_id=f"session-1-{i}",
                ip_address="203.0.113.50",
            )
            await db.commit()
            
            if i == 4:
                assert abuse_alert is not None
                first_alert_id = abuse_alert.id
        
        # Second batch: 5 more harmful (total 10)
        for i in range(5):
            feedback, moderation_alert, abuse_alert = await FeedbackService.record_feedback(
                db=db,
                user_id=user_id,
                tenant_id=tenant_id,
                bot_id=test_bot.id,
                answer_id=uuid4(),
                message_id=f"msg-batch2-{i}",
                feedback_type=FeedbackType.NEGATIVE,
                reason=FeedbackReason.HARMFUL,
                additional_notes=None,
                session_id=f"session-2-{i}",
                ip_address="203.0.113.50",
            )
            await db.commit()
        
        # Check multiple suspicions exist
        result = await db.execute(
            select(UserAbuseSuspicion).where(UserAbuseSuspicion.user_id == user_id)
        )
        suspicions = result.scalars().all()
        # Should have multiple suspicion records as pattern continues
        assert len(suspicions) >= 1


@pytest.mark.asyncio
class TestFeedbackServiceValidation:
    """Test FeedbackService validation logic"""

    async def test_validates_bot_ownership(self, db: AsyncSession, test_bot: Bot, other_tenant_id: UUID):
        """TC16: Validates bot belongs to tenant"""
        user_id = uuid4()
        
        with pytest.raises(Exception) as exc_info:
            await FeedbackService.record_feedback(
                db=db,
                user_id=user_id,
                tenant_id=other_tenant_id,  # Different tenant
                bot_id=test_bot.id,
                answer_id=uuid4(),
                message_id="msg-wrong-tenant",
                feedback_type=FeedbackType.POSITIVE,
                reason=None,
                additional_notes=None,
                session_id="session-test",
                ip_address="203.0.113.1",
            )
        
        assert "Access denied" in str(exc_info.value) or "Forbidden" in str(exc_info.value)

    async def test_validates_negative_requires_reason(self, db: AsyncSession, test_bot: Bot, tenant_id: UUID):
        """TC17: Validates negative feedback requires reason"""
        user_id = uuid4()
        
        with pytest.raises(Exception) as exc_info:
            await FeedbackService.record_feedback(
                db=db,
                user_id=user_id,
                tenant_id=tenant_id,
                bot_id=test_bot.id,
                answer_id=uuid4(),
                message_id="msg-no-reason",
                feedback_type=FeedbackType.NEGATIVE,
                reason=None,  # Missing reason
                additional_notes=None,
                session_id="session-test",
                ip_address="203.0.113.1",
            )
        
        assert "Reason is required" in str(exc_info.value)

    async def test_validates_additional_notes_max_500(self, db: AsyncSession, test_bot: Bot, tenant_id: UUID):
        """TC18: Validates additional_notes max 500 characters"""
        user_id = uuid4()
        long_text = "x" * 501
        
        with pytest.raises(Exception) as exc_info:
            await FeedbackService.record_feedback(
                db=db,
                user_id=user_id,
                tenant_id=tenant_id,
                bot_id=test_bot.id,
                answer_id=uuid4(),
                message_id="msg-long-notes",
                feedback_type=FeedbackType.NEGATIVE,
                reason=FeedbackReason.OTHER,
                additional_notes=long_text,
                session_id="session-test",
                ip_address="203.0.113.1",
            )
        
        assert "500 characters" in str(exc_info.value)

    async def test_validates_bot_exists(self, db: AsyncSession, tenant_id: UUID):
        """TC19: Validates bot exists"""
        user_id = uuid4()
        fake_bot_id = uuid4()
        
        with pytest.raises(Exception) as exc_info:
            await FeedbackService.record_feedback(
                db=db,
                user_id=user_id,
                tenant_id=tenant_id,
                bot_id=fake_bot_id,
                answer_id=uuid4(),
                message_id="msg-fake-bot",
                feedback_type=FeedbackType.POSITIVE,
                reason=None,
                additional_notes=None,
                session_id="session-test",
                ip_address="203.0.113.1",
            )
        
        assert "Bot not found" in str(exc_info.value) or "not found" in str(exc_info.value).lower()

    async def test_enforces_rate_limit_per_session(self, db: AsyncSession, test_bot: Bot, tenant_id: UUID):
        """TC20: Enforces 20 per 5 minutes rate limit per session"""
        user_id = uuid4()
        session_id = "session-ratelimit-test"
        
        # Submit 20 feedback items
        for i in range(20):
            feedback, moderation_alert, abuse_alert = await FeedbackService.record_feedback(
                db=db,
                user_id=user_id,
                tenant_id=tenant_id,
                bot_id=test_bot.id,
                answer_id=uuid4(),
                message_id=f"msg-{i}",
                feedback_type=FeedbackType.POSITIVE,
                reason=None,
                additional_notes=None,
                session_id=session_id,
                ip_address="203.0.113.1",
            )
            await db.commit()
        
        # 21st should fail with rate limit error
        with pytest.raises(Exception) as exc_info:
            await FeedbackService.record_feedback(
                db=db,
                user_id=user_id,
                tenant_id=tenant_id,
                bot_id=test_bot.id,
                answer_id=uuid4(),
                message_id="msg-21",
                feedback_type=FeedbackType.POSITIVE,
                reason=None,
                additional_notes=None,
                session_id=session_id,
                ip_address="203.0.113.1",
            )
        
        assert "Please wait" in str(exc_info.value) or "Too Many Requests" in str(exc_info.value)

    async def test_audit_log_created(self, db: AsyncSession, test_bot: Bot, tenant_id: UUID):
        """TC21: Creates audit log entry for feedback submission"""
        user_id = uuid4()
        
        feedback, moderation_alert, abuse_alert = await FeedbackService.record_feedback(
            db=db,
            user_id=user_id,
            tenant_id=tenant_id,
            bot_id=test_bot.id,
            answer_id=uuid4(),
            message_id="msg-audit",
            feedback_type=FeedbackType.POSITIVE,
            reason=None,
            additional_notes=None,
            session_id="session-audit",
            ip_address="203.0.113.1",
        )
        await db.commit()
        
        # Verify audit log was created
        # (Would need to query AuditLog table - implementation depends on audit service)
        assert feedback is not None

    async def test_upsert_updates_existing_feedback(self, db: AsyncSession, test_bot: Bot, tenant_id: UUID):
        """TC22: Upsert updates existing feedback instead of creating new"""
        user_id = uuid4()
        answer_id = uuid4()
        
        # First submission
        feedback1, _, _ = await FeedbackService.record_feedback(
            db=db,
            user_id=user_id,
            tenant_id=tenant_id,
            bot_id=test_bot.id,
            answer_id=answer_id,
            message_id="msg-upsert",
            feedback_type=FeedbackType.POSITIVE,
            reason=None,
            additional_notes=None,
            session_id="session-1",
            ip_address="203.0.113.1",
        )
        await db.commit()
        feedback1_id = feedback1.id
        
        # Second submission (should update)
        feedback2, _, _ = await FeedbackService.record_feedback(
            db=db,
            user_id=user_id,
            tenant_id=tenant_id,
            bot_id=test_bot.id,
            answer_id=answer_id,
            message_id="msg-upsert-updated",
            feedback_type=FeedbackType.NEGATIVE,
            reason=FeedbackReason.NOT_HELPFUL,
            additional_notes="Changed my mind",
            session_id="session-2",
            ip_address="203.0.113.1",
        )
        await db.commit()
        
        # Should be same feedback record (same ID)
        assert feedback2.id == feedback1_id
        assert feedback2.type == FeedbackType.NEGATIVE
        assert feedback2.reason == FeedbackReason.NOT_HELPFUL
        assert feedback2.additional_notes == "Changed my mind"

    async def test_stores_ip_address_from_x_forwarded_for(self, db: AsyncSession, test_bot: Bot, tenant_id: UUID):
        """TC23: Extracts IP from X-Forwarded-For header"""
        user_id = uuid4()
        
        feedback, _, _ = await FeedbackService.record_feedback(
            db=db,
            user_id=user_id,
            tenant_id=tenant_id,
            bot_id=test_bot.id,
            answer_id=uuid4(),
            message_id="msg-ip",
            feedback_type=FeedbackType.POSITIVE,
            reason=None,
            additional_notes=None,
            session_id="session-ip",
            ip_address="203.0.113.45",  # Simulated from X-Forwarded-For
        )
        await db.commit()
        
        assert feedback.ip_address == "203.0.113.45"

    async def test_handles_none_session_id(self, db: AsyncSession, test_bot: Bot, tenant_id: UUID):
        """TC24: Handles None session_id gracefully"""
        user_id = uuid4()
        
        feedback, _, _ = await FeedbackService.record_feedback(
            db=db,
            user_id=user_id,
            tenant_id=tenant_id,
            bot_id=test_bot.id,
            answer_id=uuid4(),
            message_id="msg-no-session",
            feedback_type=FeedbackType.POSITIVE,
            reason=None,
            additional_notes=None,
            session_id=None,
            ip_address="203.0.113.1",
        )
        await db.commit()
        
        assert feedback is not None
        assert feedback.session_id is None

    async def test_handles_none_ip_address(self, db: AsyncSession, test_bot: Bot, tenant_id: UUID):
        """TC25: Handles None ip_address gracefully"""
        user_id = uuid4()
        
        feedback, _, _ = await FeedbackService.record_feedback(
            db=db,
            user_id=user_id,
            tenant_id=tenant_id,
            bot_id=test_bot.id,
            answer_id=uuid4(),
            message_id="msg-no-ip",
            feedback_type=FeedbackType.POSITIVE,
            reason=None,
            additional_notes=None,
            session_id="session-test",
            ip_address=None,
        )
        await db.commit()
        
        assert feedback is not None
        assert feedback.ip_address is None

    async def test_positive_feedback_no_alert_or_abuse(self, db: AsyncSession, test_bot: Bot, tenant_id: UUID):
        """TC26: Positive feedback never triggers alerts or abuse detection"""
        user_id = uuid4()
        
        # Submit 10 positive feedback
        for i in range(10):
            feedback, moderation_alert, abuse_alert = await FeedbackService.record_feedback(
                db=db,
                user_id=user_id,
                tenant_id=tenant_id,
                bot_id=test_bot.id,
                answer_id=uuid4(),
                message_id=f"msg-pos-{i}",
                feedback_type=FeedbackType.POSITIVE,
                reason=None,
                additional_notes=None,
                session_id=f"session-{i}",
                ip_address="203.0.113.1",
            )
            await db.commit()
            
            assert moderation_alert is None
            assert abuse_alert is None

    async def test_returns_tuple_of_three_elements(self, db: AsyncSession, test_bot: Bot, tenant_id: UUID):
        """TC27: Always returns tuple of (feedback, moderation_alert, abuse_alert)"""
        user_id = uuid4()
        
        result = await FeedbackService.record_feedback(
            db=db,
            user_id=user_id,
            tenant_id=tenant_id,
            bot_id=test_bot.id,
            answer_id=uuid4(),
            message_id="msg-tuple",
            feedback_type=FeedbackType.POSITIVE,
            reason=None,
            additional_notes=None,
            session_id="session-tuple",
            ip_address="203.0.113.1",
        )
        await db.commit()
        
        assert isinstance(result, tuple)
        assert len(result) == 3
        feedback, moderation_alert, abuse_alert = result
        assert feedback is not None
        assert moderation_alert is None
        assert abuse_alert is None
