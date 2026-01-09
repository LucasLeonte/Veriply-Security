"""Feedback submission and analytics endpoints."""

import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user
from app.core.database import get_db, set_tenant_context
from app.models import (
    FeedbackReason,
    FeedbackType,
    ModerationAlert,
    UserAbuseSuspicion,
)
from app.schemas.feedback import (
    FeedbackCreateRequest,
    FeedbackCreateResponse,
    FeedbackStatsResponse,
    ModerationAlertResponse,
)
from app.services.feedback_service import FeedbackService
from app.services.feedback_analytics_service import FeedbackAnalyticsService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/bots", tags=["feedback"])


@router.post("/{bot_id}/feedback", response_model=FeedbackCreateResponse)
async def submit_feedback(
    bot_id: UUID,
    payload: FeedbackCreateRequest,
    request: Request,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Submit feedback for a bot answer (authenticated)."""
    try:
        # SECURITY: Set RLS context for tenant isolation
        await set_tenant_context(db, UUID(current_user['tenant_id']))

        feedback_type = FeedbackType(payload.type)
        reason = FeedbackReason(payload.reason) if payload.reason else None
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid feedback type or reason",
        )

    feedback, moderation_alert, abuse_alert = await FeedbackService.record_feedback(
        db=db,
        user_id=UUID(current_user["sub"]),
        tenant_id=UUID(current_user["tenant_id"]),
        bot_id=bot_id,
        answer_id=payload.answer_id,
        message_id=payload.message_id,
        feedback_type=feedback_type,
        reason=reason,
        additional_notes=payload.additional_notes,
        session_id=payload.session_id,
        ip_address=_extract_client_ip(request),
    )

    # Attempt to capture IP address from request if available (optional)
    # FastAPI dependency injection for Request would be added if needed later

    await db.commit()

    return FeedbackCreateResponse(
        success=True,
        feedback_id=feedback.id,
        moderation_alert_id=moderation_alert.id if moderation_alert else None,
        abuse_suspicion_id=abuse_alert.id if abuse_alert else None,
        message="Feedback recorded",
    )


@router.get("/{bot_id}/feedback/stats", response_model=FeedbackStatsResponse)
async def get_feedback_stats(
    bot_id: UUID,
    hours: int = Query(default=24, ge=1, le=168),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get aggregate feedback statistics for a bot."""
    stats = await FeedbackAnalyticsService.aggregate_stats(
        db=db,
        bot_id=bot_id,
        tenant_id=UUID(current_user["tenant_id"]),
        hours=hours,
    )
    return FeedbackStatsResponse(**stats)


@router.get("/moderation/alerts", response_model=list[ModerationAlertResponse])
async def list_moderation_alerts(
    bot_id: Optional[UUID] = None,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List moderation alerts for the current tenant (optionally filtered by bot)."""
    query = select(ModerationAlert).where(
        ModerationAlert.tenant_id == UUID(current_user["tenant_id"])
    )
    if bot_id:
        query = query.where(ModerationAlert.bot_id == bot_id)

    result = await db.scalars(query)
    alerts = [
        ModerationAlertResponse(
            id=alert.id,
            bot_id=alert.bot_id,
            answer_id=alert.answer_id,
            feedback_count=alert.feedback_count,
            user_ids=alert.user_ids,
            created_at=alert.created_at,
        )
        for alert in result
    ]
    return alerts


@router.get("/moderation/user-abuse")
async def list_user_abuse_suspicions(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List suspected abuse patterns (admin/owner only)."""
    if current_user.get("role") not in {"owner", "admin"}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin or owner role required",
        )

    query = select(UserAbuseSuspicion).where(
        UserAbuseSuspicion.tenant_id == UUID(current_user["tenant_id"])
    )
    result = await db.scalars(query)
    return [
        {
            "id": record.id,
            "user_id": record.user_id,
            "bot_id": record.bot_id,
            "ip_address": record.ip_address,
            "feedback_ids": record.feedback_ids,
            "window_start": record.window_start,
            "created_at": record.created_at,
        }
        for record in result
    ]


def _extract_client_ip(request: Request) -> Optional[str]:
    """Best-effort extraction of client IP (supports X-Forwarded-For)."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    client = request.client
    return client.host if client else None