"""Schemas for chat endpoints."""

from typing import List, Literal, Optional
from uuid import UUID

from pydantic import BaseModel, Field, conint


class ChatMessage(BaseModel):
    """Single chat message sent by user or assistant."""

    role: Literal["user", "assistant"]
    content: str
    citations: Optional[list[dict]] = None
    timestamp: Optional[int] = None
    trust_level: Optional[Literal["verified", "ai_generated", "pending"]] = None
    confidence_score: Optional[float] = None
    source_type: Optional[Literal["verified_kb", "rag", "hitl"]] = None
    response_id: Optional[str] = None


class ChatQueryRequest(BaseModel):
    """Request body for chat query endpoint."""

    query: str = Field(..., min_length=1, max_length=5000)
    context: Optional[List[ChatMessage]] = Field(
        default=None,
        description=(
            "Full conversation history for context injection. Older messages "
            "will be summarized server-side."
        ),
    )
    context_window: conint(gt=0, le=100) = Field(
        default=10,
        description="Number of most recent messages to keep verbatim in the prompt",
    )
    # Deprecated: kept for backward compatibility with earlier clients
    conversation_history: Optional[list[dict]] = Field(default=None)


class ChatQueryResponse(BaseModel):
    """Response for chat query with trust metadata."""

    response: str
    citations: Optional[list[dict]] = None
    trust_level: Literal["verified", "ai_generated", "pending"]
    confidence_score: float
    source_type: Literal["verified_kb", "rag", "hitl"]
    response_id: str
    chunks_used: int = 0


class MessageStatusResponse(BaseModel):
    """Response for checking message/verification status."""

    status: Literal["pending", "resolved", "error"]
    response: Optional[ChatQueryResponse] = None
    error: Optional[str] = None


class PublicBotInfo(BaseModel):
    """Public bot information (no authentication required)."""

    id: str
    name: str
    avatar_url: Optional[str] = None
    welcome_message: str
    is_public: bool
    confidence_threshold: int
