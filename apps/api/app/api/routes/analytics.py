"""Analytics endpoints for dashboard metrics."""

import logging
from datetime import datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user
from app.core.database import get_db
from app.models import (
    Feedback,
    FeedbackType,
    FeedbackReason,
    ConfidenceLog,
    RoutingDecision,
)
from app.schemas.analytics import AnalyticsMetricsResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/metrics", response_model=AnalyticsMetricsResponse)
async def get_analytics_metrics(
    period: int = Query(7, description="Number of days to look back"),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get analytics metrics for the authenticated user's bots."""
    try:
        # Get user's tenant_id from current_user
        tenant_id = current_user.get("tenant_id")
        if not tenant_id:
            raise HTTPException(status_code=403, detail="User has no tenant")

        # Parse tenant_id to UUID if it's a string
        if isinstance(tenant_id, str):
            try:
                tenant_id = UUID(tenant_id)
            except (ValueError, AttributeError):
                raise HTTPException(status_code=403, detail="Invalid tenant")

        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=period)

        # Fetch confidence logs for the period
        confidence_logs = await db.execute(
            select(ConfidenceLog).where(
                and_(
                    ConfidenceLog.tenant_id == tenant_id,
                    ConfidenceLog.created_at >= start_date,
                    ConfidenceLog.created_at <= end_date,
                )
            )
        )
        confidence_logs = confidence_logs.scalars().all()

        # Fetch feedback data
        feedback_data = await db.execute(
            select(Feedback).where(
                and_(
                    Feedback.tenant_id == tenant_id,
                    Feedback.created_at >= start_date,
                    Feedback.created_at <= end_date,
                )
            )
        )
        feedback_data = feedback_data.scalars().all()

        # Calculate metrics
        total_queries = len(confidence_logs)

        # Auto-resolved = queries that went to auto_send
        auto_resolved = sum(
            1 for log in confidence_logs 
            if log.routing_decision == RoutingDecision.auto_send
        )
        auto_resolved_percent = (
            int((auto_resolved / total_queries * 100) if total_queries > 0 else 0)
        )

        # HITL intervention rate
        hitl_count = sum(
            1 for log in confidence_logs 
            if log.routing_decision == RoutingDecision.hitl
        )
        hitl_intervention_rate = (
            int((hitl_count / total_queries * 100) if total_queries > 0 else 0)
        )

        # Average response time from confidence log metadata (ms -> seconds)
        response_times_ms = []
        for log in confidence_logs:
            metadata = getattr(log, "metadata_json", None) or {}
            if isinstance(metadata, dict) and "response_time_ms" in metadata:
                try:
                    response_times_ms.append(float(metadata["response_time_ms"]))
                except (TypeError, ValueError):
                    continue
        avg_response_time = round(
            sum(response_times_ms) / len(response_times_ms) / 1000, 2
        ) if response_times_ms else 0.0

        # Trust score based on feedback
        negative_feedback = sum(
            1 for f in feedback_data 
            if f.type == FeedbackType.NEGATIVE
        )
        positive_feedback = sum(
            1 for f in feedback_data 
            if f.type == FeedbackType.POSITIVE
        )
        total_feedback = len(feedback_data)
        trust_score = int((positive_feedback / total_feedback * 100)) if total_feedback > 0 else 0

        # Rejection reasons from feedback
        rejection_reasons = []
        for reason in FeedbackReason:
            count = sum(
                1 for f in feedback_data 
                if f.type == FeedbackType.NEGATIVE and f.reason == reason
            )
            if count > 0:
                percent = int((count / negative_feedback * 100) if negative_feedback > 0 else 0)
                rejection_reasons.append({
                    "reason": reason.value.replace("_", " ").title(),
                    "count": count,
                    "percent": percent,
                })

        # Sort by count descending
        rejection_reasons.sort(key=lambda x: x["count"], reverse=True)

        # Generate chart data for HITL intervention rate over time
        chart_data = []
        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        for i in range(min(7, period)):
            day_start = end_date - timedelta(days=6 - i)
            day_end = day_start + timedelta(days=1)
            day_logs = [
                log for log in confidence_logs
                if day_start <= log.created_at <= day_end
            ]
            day_hitl = sum(
                1 for log in day_logs 
                if log.routing_decision == RoutingDecision.hitl
            )
            rate = int((day_hitl / len(day_logs) * 100) if day_logs else 0)
            chart_data.append({
                "period": days[i % 7],
                "interventionRate": rate,
            })

        # Knowledge gaps (unanswered questions) - from low confidence queries
        knowledge_gaps = []
        low_confidence_logs = [
            log for log in confidence_logs
            if log.overall_confidence < 0.5
        ]
        # Group by query text and count
        gap_counts = {}
        for log in low_confidence_logs:
            if log.query_text:
                gap_counts[log.query_text] = gap_counts.get(log.query_text, 0) + 1

        for question, count in sorted(gap_counts.items(), key=lambda x: x[1], reverse=True)[:5]:
            knowledge_gaps.append({
                "question": question,
                "askCount": count,
            })

        return AnalyticsMetricsResponse(
            totalQueries=total_queries,
            autoResolved=auto_resolved,
            autoResolvedPercent=auto_resolved_percent,
            avgResponseTime=avg_response_time,
            trustScore=trust_score,
            hitlInterventionRate=hitl_intervention_rate,
            chartData=chart_data,
            rejectionReasons=rejection_reasons,
            knowledgeGaps=knowledge_gaps,
        )

    except Exception as e:
        logger.error(f"Error fetching analytics metrics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch analytics metrics")
