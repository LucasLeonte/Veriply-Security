"""Business logic for recording and moderating feedback."""

from datetime import datetime, timedelta
from typing import Optional, Tuple
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    Feedback,
    FeedbackReason,
    FeedbackType,
    ModerationAlert,
    UserAbuseSuspicion,
    Bot,
)
from app.services.audit_service import AuditService
from app.services.feedback_analytics_service import FeedbackAnalyticsService
from app.services.moderation_notification_service import ModerationNotificationService


class FeedbackService:
    RATE_LIMIT_COUNT = 20
    RATE_LIMIT_WINDOW_MINUTES = 5
    ABUSE_WINDOW_HOURS = 1
    ABUSE_THRESHOLD = 5
    HARMFUL_ALERT_THRESHOLD = 3

    @staticmethod
    async def record_feedback(
        db: AsyncSession,
        *,
        user_id: UUID,
        tenant_id: UUID,
        bot_id: UUID,
        answer_id: UUID,
        message_id: str,
        feedback_type: FeedbackType,
        reason: Optional[FeedbackReason],
        additional_notes: Optional[str],
        session_id: Optional[str],
        ip_address: Optional[str],
    ) -> Tuple[Feedback, Optional[ModerationAlert], Optional[UserAbuseSuspicion]]:
        """Create or update a feedback entry with validation and monitoring."""

        # Validate bot ownership (tenant isolation)
        bot = await db.get(Bot, bot_id)
        if not bot:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bot not found",
            )
        if bot.tenant_id != tenant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied for this bot",
            )

        # Validate payload
        if feedback_type == FeedbackType.NEGATIVE and not reason:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Reason is required for negative feedback",
            )

        if additional_notes and len(additional_notes) > 500:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="additional_notes must be 500 characters or fewer",
            )

        # Rate limiting per session
        if session_id:
            window_start = datetime.utcnow() - timedelta(minutes=FeedbackService.RATE_LIMIT_WINDOW_MINUTES)
            rate_count = await db.scalar(
                select(func.count(Feedback.id)).where(
                    Feedback.session_id == session_id,
                    Feedback.created_at >= window_start,
                )
            )
            if (rate_count or 0) >= FeedbackService.RATE_LIMIT_COUNT:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Please wait before providing more feedback",
                )

        # Upsert feedback (one per user per answer)
        existing = await db.scalar(
            select(Feedback).where(
                Feedback.answer_id == answer_id,
                Feedback.user_id == user_id,
            )
        )

        if existing:
            existing.type = feedback_type
            existing.reason = reason
            existing.additional_notes = additional_notes
            existing.session_id = session_id
            existing.ip_address = ip_address
            existing.message_id = message_id
            existing.created_at = datetime.utcnow()
            feedback = existing
        else:
            feedback = Feedback(
                tenant_id=tenant_id,
                bot_id=bot_id,
                user_id=user_id,
                answer_id=answer_id,
                message_id=message_id,
                type=feedback_type,
                reason=reason,
                additional_notes=additional_notes,
                session_id=session_id,
                ip_address=ip_address,
            )
            db.add(feedback)

        await db.flush()

        # Audit trail
        await AuditService.log_action(
            db=db,
            actor_id=user_id,
            action="feedback_submitted",
            tenant_id=tenant_id,
            target_type="feedback",
            target_id=feedback.id,
            details={
                "bot_id": str(bot_id),
                "answer_id": str(answer_id),
                "message_id": message_id,
                "type": feedback_type.value,
                "reason": reason.value if reason else None,
                "ip_address": ip_address,
                "session_id": session_id,
            },
        )

        moderation_alert = None
        abuse_alert = None
        if feedback_type == FeedbackType.NEGATIVE and reason == FeedbackReason.HARMFUL:
            moderation_alert = await FeedbackService._maybe_create_moderation_alert(
                db=db,
                tenant_id=tenant_id,
                bot_id=bot_id,
                answer_id=answer_id,
            )
            abuse_alert = await FeedbackService._maybe_flag_user_abuse(
                db=db,
                tenant_id=tenant_id,
                bot_id=bot_id,
                user_id=user_id,
                ip_address=ip_address,
            )
        
        # Invalidate analytics cache for this bot
        await FeedbackAnalyticsService.invalidate_cache(bot_id)

        return feedback, moderation_alert, abuse_alert

    @staticmethod
    async def _maybe_create_moderation_alert(
        db: AsyncSession,
        *,
        tenant_id: UUID,
        bot_id: UUID,
        answer_id: UUID,
    ) -> Optional[ModerationAlert]:
        """Create moderation alert if harmful feedback crosses threshold in 24h."""
        window_start = datetime.utcnow() - timedelta(hours=24)
        harmful_count = await db.scalar(
            select(func.count(Feedback.id)).where(
                Feedback.bot_id == bot_id,
                Feedback.answer_id == answer_id,
                Feedback.type == FeedbackType.NEGATIVE,
                Feedback.reason == FeedbackReason.HARMFUL,
                Feedback.created_at >= window_start,
            )
        )

        if (harmful_count or 0) < FeedbackService.HARMFUL_ALERT_THRESHOLD:
            return None

        # Gather user ids for context
        users_result = await db.scalars(
            select(Feedback.user_id).where(
                Feedback.bot_id == bot_id,
                Feedback.answer_id == answer_id,
                Feedback.reason == FeedbackReason.HARMFUL,
                Feedback.created_at >= window_start,
            )
        )
        user_ids = {str(uid) for uid in users_result}

        alert = ModerationAlert(
            tenant_id=tenant_id,
            bot_id=bot_id,
            answer_id=answer_id,
            feedback_count=harmful_count or 0,
            user_ids=",".join(sorted(user_ids)),
        )
        db.add(alert)
        await db.flush()
        
        # Send notification asynchronously (don't wait for it)
        try:
            await ModerationNotificationService.notify_moderation_alert(db, alert)
        except Exception:
            # Don't fail feedback submission if notification fails
            pass
        
        return alert

    @staticmethod
    async def _maybe_flag_user_abuse(
        db: AsyncSession,
        *,
        tenant_id: UUID,
        bot_id: UUID,
        user_id: UUID,
        ip_address: Optional[str],
    ) -> Optional[UserAbuseSuspicion]:
        """Flag user if they submit 5+ harmful feedbacks in 1 hour."""
        window_start = datetime.utcnow() - timedelta(hours=FeedbackService.ABUSE_WINDOW_HOURS)
        harmful_feedbacks = await db.scalars(
            select(Feedback).where(
                Feedback.user_id == user_id,
                Feedback.bot_id == bot_id,
                Feedback.type == FeedbackType.NEGATIVE,
                Feedback.reason == FeedbackReason.HARMFUL,
                Feedback.created_at >= window_start,
            )
        )
        feedback_list = list(harmful_feedbacks)
        if len(feedback_list) < FeedbackService.ABUSE_THRESHOLD:
            return None

        suspicion = UserAbuseSuspicion(
            tenant_id=tenant_id,
            user_id=user_id,
            bot_id=bot_id,
            ip_address=ip_address,
            feedback_ids=",".join(sorted(str(f.id) for f in feedback_list)),
            window_start=window_start,
        )
        db.add(suspicion)
        await db.flush()
        
        # Send notification asynchronously (don't wait for it)
        try:
            await ModerationNotificationService.notify_user_abuse(db, suspicion)
        except Exception:
            # Don't fail feedback submission if notification fails
            pass
        
        return suspicion