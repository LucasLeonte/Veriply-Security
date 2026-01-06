from datetime import datetime
from typing import Optional, Dict
from uuid import UUID

from pydantic import BaseModel, Field


class FeedbackCreateRequest(BaseModel):
    answer_id: UUID = Field(..., description="Identifier of the AI answer")
    message_id: str = Field(..., min_length=1, max_length=255)
    type: str = Field(..., pattern="^(positive|negative)$")
    reason: Optional[str] = Field(
        default=None,
        pattern="^(incorrect|not_helpful|incomplete|harmful|other)$",
        description="Required when type is negative",
    )
    additional_notes: Optional[str] = Field(default=None, max_length=500)
    session_id: Optional[str] = Field(default=None, max_length=255)


class FeedbackCreateResponse(BaseModel):
    success: bool
    feedback_id: UUID
    moderation_alert_id: Optional[UUID] = None
    abuse_suspicion_id: Optional[UUID] = None
    message: str


class FeedbackStatsResponse(BaseModel):
    total: int
    positive_count: int
    negative_count: int
    negative_reasons: Dict[str, int]
    harmful_count: int
    window_hours: int


class ModerationAlertResponse(BaseModel):
    id: UUID
    bot_id: UUID
    answer_id: UUID
    feedback_count: int
    user_ids: str
    created_at: datetime