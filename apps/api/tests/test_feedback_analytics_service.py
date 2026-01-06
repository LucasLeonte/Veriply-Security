"""
Tests for feedback analytics service.
"""

import pytest
from uuid import uuid4, UUID
from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Feedback, FeedbackType, FeedbackReason
from app.services.feedback_analytics_service import FeedbackAnalyticsService


@pytest.mark.asyncio
class TestFeedbackAnalyticsService:
    """Test feedback analytics aggregation logic"""

    async def test_aggregate_stats_empty_bot(self, db: AsyncSession, test_bot_id: UUID, tenant_id: UUID):
        """TC1: Returns zero counts for bot with no feedback"""
        stats = await FeedbackAnalyticsService.aggregate_stats(
            db=db,
            bot_id=test_bot_id,
            tenant_id=tenant_id,
            hours=24,
        )
        
        assert stats["total"] == 0
        assert stats["positive_count"] == 0
        assert stats["negative_count"] == 0
        assert stats["harmful_count"] == 0
        assert stats["negative_reasons"] == {}
        assert stats["window_hours"] == 24

    async def test_counts_positive_feedback(self, db: AsyncSession, test_bot_id: UUID, tenant_id: UUID, test_user_id: UUID):
        """TC2: Correctly counts positive feedback"""
        # Create 3 positive feedback items
        for i in range(3):
            feedback = Feedback(
                tenant_id=tenant_id,
                bot_id=test_bot_id,
                user_id=test_user_id,
                answer_id=uuid4(),
                message_id=f"msg-pos-{i}",
                type=FeedbackType.POSITIVE,
            )
            db.add(feedback)
        await db.commit()
        
        stats = await FeedbackAnalyticsService.aggregate_stats(
            db=db,
            bot_id=test_bot_id,
            tenant_id=tenant_id,
            hours=24,
        )
        
        assert stats["positive_count"] == 3
        assert stats["total"] == 3

    async def test_counts_negative_feedback(self, db: AsyncSession, test_bot_id: UUID, tenant_id: UUID, test_user_id: UUID):
        """TC3: Correctly counts negative feedback"""
        # Create 2 negative feedback items
        for i in range(2):
            feedback = Feedback(
                tenant_id=tenant_id,
                bot_id=test_bot_id,
                user_id=test_user_id,
                answer_id=uuid4(),
                message_id=f"msg-neg-{i}",
                type=FeedbackType.NEGATIVE,
                reason=FeedbackReason.NOT_HELPFUL,
            )
            db.add(feedback)
        await db.commit()
        
        stats = await FeedbackAnalyticsService.aggregate_stats(
            db=db,
            bot_id=test_bot_id,
            tenant_id=tenant_id,
            hours=24,
        )
        
        assert stats["negative_count"] == 2
        assert stats["total"] == 2

    async def test_groups_negative_reasons(self, db: AsyncSession, test_bot_id: UUID, tenant_id: UUID, test_user_id: UUID):
        """TC4: Groups negative feedback by reason"""
        reasons = [
            FeedbackReason.INCORRECT,
            FeedbackReason.INCORRECT,
            FeedbackReason.NOT_HELPFUL,
            FeedbackReason.INCOMPLETE,
            FeedbackReason.HARMFUL,
        ]
        
        for i, reason in enumerate(reasons):
            feedback = Feedback(
                tenant_id=tenant_id,
                bot_id=test_bot_id,
                user_id=test_user_id,
                answer_id=uuid4(),
                message_id=f"msg-reason-{i}",
                type=FeedbackType.NEGATIVE,
                reason=reason,
            )
            db.add(feedback)
        await db.commit()
        
        stats = await FeedbackAnalyticsService.aggregate_stats(
            db=db,
            bot_id=test_bot_id,
            tenant_id=tenant_id,
            hours=24,
        )
        
        assert stats["negative_reasons"]["incorrect"] == 2
        assert stats["negative_reasons"]["not_helpful"] == 1
        assert stats["negative_reasons"]["incomplete"] == 1
        assert stats["negative_reasons"]["harmful"] == 1

    async def test_counts_harmful_feedback(self, db: AsyncSession, test_bot_id: UUID, tenant_id: UUID, test_user_id: UUID):
        """TC5: Correctly counts harmful feedback"""
        # Create 2 harmful feedback items
        for i in range(2):
            feedback = Feedback(
                tenant_id=tenant_id,
                bot_id=test_bot_id,
                user_id=test_user_id,
                answer_id=uuid4(),
                message_id=f"msg-harmful-{i}",
                type=FeedbackType.NEGATIVE,
                reason=FeedbackReason.HARMFUL,
            )
            db.add(feedback)
        await db.commit()
        
        stats = await FeedbackAnalyticsService.aggregate_stats(
            db=db,
            bot_id=test_bot_id,
            tenant_id=tenant_id,
            hours=24,
        )
        
        assert stats["harmful_count"] == 2

    async def test_respects_time_window_24h(self, db: AsyncSession, test_bot_id: UUID, tenant_id: UUID, test_user_id: UUID):
        """TC6: Only counts feedback within 24-hour window"""
        # Recent feedback (within 24h)
        recent_feedback = Feedback(
            tenant_id=tenant_id,
            bot_id=test_bot_id,
            user_id=test_user_id,
            answer_id=uuid4(),
            message_id="msg-recent",
            type=FeedbackType.POSITIVE,
            created_at=datetime.utcnow() - timedelta(hours=12),
        )
        
        # Old feedback (older than 24h)
        old_feedback = Feedback(
            tenant_id=tenant_id,
            bot_id=test_bot_id,
            user_id=test_user_id,
            answer_id=uuid4(),
            message_id="msg-old",
            type=FeedbackType.POSITIVE,
            created_at=datetime.utcnow() - timedelta(hours=48),
        )
        
        db.add_all([recent_feedback, old_feedback])
        await db.commit()
        
        stats = await FeedbackAnalyticsService.aggregate_stats(
            db=db,
            bot_id=test_bot_id,
            tenant_id=tenant_id,
            hours=24,
        )
        
        assert stats["total"] == 1  # Only recent feedback counted

    async def test_custom_time_window_48h(self, db: AsyncSession, test_bot_id: UUID, tenant_id: UUID, test_user_id: UUID):
        """TC7: Supports custom time window (48 hours)"""
        # Feedback 36 hours ago
        feedback = Feedback(
            tenant_id=tenant_id,
            bot_id=test_bot_id,
            user_id=test_user_id,
            answer_id=uuid4(),
            message_id="msg-36h",
            type=FeedbackType.POSITIVE,
            created_at=datetime.utcnow() - timedelta(hours=36),
        )
        db.add(feedback)
        await db.commit()
        
        # Should not be counted in 24h window
        stats_24h = await FeedbackAnalyticsService.aggregate_stats(
            db=db,
            bot_id=test_bot_id,
            tenant_id=tenant_id,
            hours=24,
        )
        assert stats_24h["total"] == 0
        
        # Should be counted in 48h window
        stats_48h = await FeedbackAnalyticsService.aggregate_stats(
            db=db,
            bot_id=test_bot_id,
            tenant_id=tenant_id,
            hours=48,
        )
        assert stats_48h["total"] == 1
        assert stats_48h["window_hours"] == 48

    async def test_filters_by_bot_id(self, db: AsyncSession, test_bot_id: UUID, tenant_id: UUID, test_user_id: UUID):
        """TC8: Only counts feedback for specified bot"""
        other_bot_id = uuid4()
        
        # Feedback for test_bot
        feedback1 = Feedback(
            tenant_id=tenant_id,
            bot_id=test_bot_id,
            user_id=test_user_id,
            answer_id=uuid4(),
            message_id="msg-bot1",
            type=FeedbackType.POSITIVE,
        )
        
        # Feedback for other_bot
        feedback2 = Feedback(
            tenant_id=tenant_id,
            bot_id=other_bot_id,
            user_id=test_user_id,
            answer_id=uuid4(),
            message_id="msg-bot2",
            type=FeedbackType.POSITIVE,
        )
        
        db.add_all([feedback1, feedback2])
        await db.commit()
        
        stats = await FeedbackAnalyticsService.aggregate_stats(
            db=db,
            bot_id=test_bot_id,
            tenant_id=tenant_id,
            hours=24,
        )
        
        assert stats["total"] == 1  # Only feedback1 for test_bot

    async def test_mixed_positive_and_negative(self, db: AsyncSession, test_bot_id: UUID, tenant_id: UUID, test_user_id: UUID):
        """TC9: Correctly counts mixed positive and negative feedback"""
        # 3 positive, 2 negative
        for i in range(3):
            db.add(Feedback(
                tenant_id=tenant_id,
                bot_id=test_bot_id,
                user_id=test_user_id,
                answer_id=uuid4(),
                message_id=f"msg-pos-{i}",
                type=FeedbackType.POSITIVE,
            ))
        
        for i in range(2):
            db.add(Feedback(
                tenant_id=tenant_id,
                bot_id=test_bot_id,
                user_id=test_user_id,
                answer_id=uuid4(),
                message_id=f"msg-neg-{i}",
                type=FeedbackType.NEGATIVE,
                reason=FeedbackReason.NOT_HELPFUL,
            ))
        
        await db.commit()
        
        stats = await FeedbackAnalyticsService.aggregate_stats(
            db=db,
            bot_id=test_bot_id,
            tenant_id=tenant_id,
            hours=24,
        )
        
        assert stats["total"] == 5
        assert stats["positive_count"] == 3
        assert stats["negative_count"] == 2

    async def test_handles_none_reason(self, db: AsyncSession, test_bot_id: UUID, tenant_id: UUID, test_user_id: UUID):
        """TC10: Handles negative feedback with None reason (should not happen but defensive)"""
        feedback = Feedback(
            tenant_id=tenant_id,
            bot_id=test_bot_id,
            user_id=test_user_id,
            answer_id=uuid4(),
            message_id="msg-none-reason",
            type=FeedbackType.NEGATIVE,
            reason=None,  # Should not happen but test defensive code
        )
        db.add(feedback)
        await db.commit()
        
        stats = await FeedbackAnalyticsService.aggregate_stats(
            db=db,
            bot_id=test_bot_id,
            tenant_id=tenant_id,
            hours=24,
        )
        
        # Should handle gracefully
        assert stats["negative_count"] == 1
        assert "unknown" in stats["negative_reasons"] or len(stats["negative_reasons"]) == 0
