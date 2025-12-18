"""Schemas for chat endpoints."""

from pydantic import BaseModel, Field
from typing import Optional


class ChatQueryRequest(BaseModel):
    """Request body for chat query endpoint."""

    query: str = Field(..., min_length=1, max_length=5000)
    conversation_history: Optional[list[dict]] = Field(default=None)


class ChatMessage(BaseModel):
    """Single chat message."""

    role: str = Field(..., pattern="^(user|assistant)$")
    content: str


class PublicBotInfo(BaseModel):
    """Public bot information (no authentication required)."""

    id: str
    name: str
    avatar_url: Optional[str] = None
    welcome_message: str
    is_public: bool
    confidence_threshold: int
