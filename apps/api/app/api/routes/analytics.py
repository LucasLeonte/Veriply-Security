"""Analytics endpoints for dashboard metrics."""

import logging
from datetime import datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from collections import defaultdict

from app.core.auth import get_current_user
from app.core.database import get_db, set_tenant_context
from app.models import (
    Feedback,
    FeedbackType,
    FeedbackReason,
    ConfidenceLog,
    RoutingDecision,
    Bot,
    GroupMember,
)
from app.schemas.analytics import AnalyticsMetricsResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/metrics", response_model=AnalyticsMetricsResponse)
async def get_analytics_metrics(
    period: int = Query(7, description="Number of days to look back"),
    group_id: UUID | None = Query(None, description="Optional group to scope analytics"),
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

        # SECURITY: Validate group membership if group_id is provided
        if group_id:
            member = await db.scalar(
                select(GroupMember).where(
                    (GroupMember.group_id == group_id)
                    & (GroupMember.user_id == UUID(current_user["sub"]))
                )
            )
            if not member:
                raise HTTPException(status_code=403, detail="Not a member of this group")
        
        # SECURITY: Set RLS context for tenant and optional group isolation
        await set_tenant_context(
            db,
            tenant_id,
            group_id if isinstance(group_id, UUID) else None,
        )

        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=period)
        
        # Fetch confidence logs for the period
        if group_id:
            # Get bot IDs in this group only
            bot_ids_result = await db.execute(
                select(Bot.id).where(Bot.group_id == group_id)
            )
            bot_ids = [row[0] for row in bot_ids_result.all()]
            
            # Get logs from those bots
            # NOTE: Logs may have NULL group_id if created before group_id was added
            # So we join back to bots to find the group via bot->group relationship
            if bot_ids:
                confidence_logs = await db.execute(
                    select(ConfidenceLog).where(and_(
                        ConfidenceLog.tenant_id == tenant_id,
                        ConfidenceLog.created_at >= start_date,
                        ConfidenceLog.created_at <= end_date,
                        ConfidenceLog.bot_id.in_(bot_ids)
                    ))
                )
            else:
                confidence_logs = []
            
            confidence_logs = confidence_logs.scalars().all() if bot_ids else []
        else:
            confidence_logs = await db.execute(
                select(ConfidenceLog).where(and_(
                    ConfidenceLog.tenant_id == tenant_id,
                    ConfidenceLog.created_at >= start_date,
                    ConfidenceLog.created_at <= end_date
                ))
            )
            confidence_logs = confidence_logs.scalars().all()

        # Fetch feedback data (scope to group via bot->group if provided)
        if group_id:
            # Include feedback where bot.group_id matches the group
            feedback_query = select(Feedback).join(Bot, Feedback.bot_id == Bot.id).where(
                and_(
                    Bot.group_id == group_id,
                    Feedback.tenant_id == tenant_id,
                    Feedback.created_at >= start_date,
                    Feedback.created_at <= end_date,
                )
            )
            feedback_data = await db.execute(feedback_query)
            feedback_data = feedback_data.scalars().all()
        else:
            feedback_query = select(Feedback).where(
                and_(
                    Feedback.tenant_id == tenant_id,
                    Feedback.created_at >= start_date,
                    Feedback.created_at <= end_date,
                )
            )
            feedback_data = await db.execute(feedback_query)
            feedback_data = feedback_data.scalars().all()

        # Calculate metrics in a single pass
        total_queries = len(confidence_logs)

        auto_resolved = 0
        hitl_count = 0
        response_time_sum_ms = 0.0
        response_time_count = 0

        # For chart aggregation (7-day window max)
        chart_data = []
        num_chart_days = min(period, 7)
        chart_start_date = (end_date - timedelta(days=num_chart_days - 1)).date() if num_chart_days > 0 else None
        daily_stats = defaultdict(lambda: {"total": 0, "hitl": 0}) if num_chart_days > 0 else None

        # For knowledge gaps
        gap_counts: dict[str, int] = {}

        for log in confidence_logs:
            # Auto/HITL counts
            if log.routing_decision == RoutingDecision.auto_send:
                auto_resolved += 1
            elif log.routing_decision == RoutingDecision.hitl:
                hitl_count += 1

            # Response time (ms)
            metadata = getattr(log, "metadata_json", None) or {}
            if isinstance(metadata, dict) and "response_time_ms" in metadata:
                try:
                    response_time_sum_ms += float(metadata["response_time_ms"])
                    response_time_count += 1
                except (TypeError, ValueError):
                    pass

            # Chart per-day stats
            if num_chart_days > 0 and daily_stats is not None and chart_start_date is not None:
                log_date = log.created_at.date()
                if log_date >= chart_start_date:
                    daily_stats[log_date]["total"] += 1
                    if log.routing_decision == RoutingDecision.hitl:
                        daily_stats[log_date]["hitl"] += 1

            # Knowledge gaps (low confidence)
            try:
                if (log.overall_confidence is not None) and (float(log.overall_confidence) < 0.5):
                    if log.query_text:
                        gap_counts[log.query_text] = gap_counts.get(log.query_text, 0) + 1
            except (TypeError, ValueError):
                # If overall_confidence is not numeric, skip
                pass

        auto_resolved_percent = int((auto_resolved / total_queries * 100) if total_queries > 0 else 0)
        hitl_intervention_rate = int((hitl_count / total_queries * 100) if total_queries > 0 else 0)
        avg_response_time = round((response_time_sum_ms / response_time_count) / 1000, 2) if response_time_count > 0 else 0.0

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

        # Finalize chart series from aggregated daily_stats
        if num_chart_days > 0 and daily_stats is not None:
            for i in range(num_chart_days):
                day = (end_date - timedelta(days=num_chart_days - 1 - i)).date()
                stats = daily_stats[day]
                rate = int((stats["hitl"] / stats["total"] * 100) if stats["total"] > 0 else 0)
                chart_data.append({
                    "period": day.strftime("%a"),
                    "interventionRate": rate,
                })

        # Knowledge gaps (unanswered questions) - top N from aggregated gap_counts
        knowledge_gaps = []
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
