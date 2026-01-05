"""Analytics aggregation for feedback."""

from datetime import datetime, timedelta
from typing import Dict, Any
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Feedback, FeedbackReason, FeedbackType


class FeedbackAnalyticsService:
    """Compute aggregate feedback statistics for a bot."""

    @staticmethod
    async def aggregate_stats(
        db: AsyncSession,
        *,
        bot_id: UUID,
        tenant_id: UUID,
        hours: int = 24,
    ) -> Dict[str, Any]:
        window_start = datetime.utcnow() - timedelta(hours=hours)

        base_filter = (
            Feedback.bot_id == bot_id,
            Feedback.created_at >= window_start,
        )

        total = await db.scalar(select(func.count(Feedback.id)).where(*base_filter)) or 0

        positive = await db.scalar(
            select(func.count(Feedback.id)).where(*base_filter, Feedback.type == FeedbackType.POSITIVE)
        ) or 0

        negative = await db.scalar(
            select(func.count(Feedback.id)).where(*base_filter, Feedback.type == FeedbackType.NEGATIVE)
        ) or 0

        harmful = await db.scalar(
            select(func.count(Feedback.id)).where(
                *base_filter,
                Feedback.type == FeedbackType.NEGATIVE,
                Feedback.reason == FeedbackReason.HARMFUL,
            )
        ) or 0

        # Top negative reasons grouped
        reason_rows = await db.execute(
            select(Feedback.reason, func.count(Feedback.id))
            .where(*base_filter, Feedback.type == FeedbackType.NEGATIVE)
            .group_by(Feedback.reason)
        )
        negative_reasons = {
            (reason.value if reason else "unknown"): count for reason, count in reason_rows.all()
        }

        return {
            "total": total,
            "positive_count": positive,
            "negative_count": negative,
            "negative_reasons": negative_reasons,
            "harmful_count": harmful,
            "window_hours": hours,
        }