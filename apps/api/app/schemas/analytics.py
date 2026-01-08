"""Analytics schemas for metrics and responses."""

from typing import List, Optional
from pydantic import BaseModel, Field


class ChartDataPoint(BaseModel):
    """Data point for chart visualization."""
    period: str = Field(..., description="Time period label (e.g., 'Mon', 'Tue')")
    interventionRate: int = Field(..., ge=0, le=100, description="HITL intervention rate percentage")


class RejectionReason(BaseModel):
    """Rejection reason with count and percentage."""
    reason: str = Field(..., description="Reason for rejection")
    count: int = Field(..., ge=0, description="Count of rejections")
    percent: int = Field(..., ge=0, le=100, description="Percentage of rejections")


class KnowledgeGap(BaseModel):
    """Unanswered question or knowledge gap."""
    question: str = Field(..., description="The question asked")
    askCount: int = Field(..., ge=0, description="Number of times asked")


class AnalyticsMetricsResponse(BaseModel):
    """Complete analytics metrics response."""
    totalQueries: int = Field(..., ge=0, description="Total number of queries")
    autoResolved: int = Field(..., ge=0, description="Number of auto-resolved queries")
    autoResolvedPercent: int = Field(..., ge=0, le=100, description="Percentage of auto-resolved queries")
    avgResponseTime: float = Field(..., ge=0, description="Average response time in seconds")
    trustScore: int = Field(..., ge=0, le=100, description="Overall trust/quality score")
    hitlInterventionRate: int = Field(..., ge=0, le=100, description="HITL intervention rate percentage")
    chartData: List[ChartDataPoint] = Field(..., description="Chart data points over time")
    rejectionReasons: List[RejectionReason] = Field(..., description="Breakdown of rejection reasons")
    knowledgeGaps: List[KnowledgeGap] = Field(..., description="Most common unanswered questions")

    class Config:
        """Pydantic config."""
        json_schema_extra = {
            "example": {
                "totalQueries": 2847,
                "autoResolved": 1935,
                "autoResolvedPercent": 68,
                "avgResponseTime": 1.2,
                "trustScore": 97,
                "hitlInterventionRate": 32,
                "chartData": [
                    {"period": "Mon", "interventionRate": 80},
                    {"period": "Tue", "interventionRate": 72},
                ],
                "rejectionReasons": [
                    {"reason": "Incomplete Answer", "count": 15, "percent": 45},
                ],
                "knowledgeGaps": [
                    {"question": "Do you offer student discounts?", "askCount": 12},
                ],
            }
        }
