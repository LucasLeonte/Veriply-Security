from pydantic import BaseModel, Field, field_validator
from typing import Optional
from uuid import UUID
from datetime import datetime
from enum import Enum

class BotStatus(str, Enum):
    EMPTY = "Empty"
    PROCESSING = "Processing"
    READY = "Ready"

class BotCreateRequest(BaseModel):
    """Request schema for creating a new bot"""
    name: str = Field(..., min_length=2, max_length=50, description="Bot name (2-50 chars)")
    description: Optional[str] = Field(None, max_length=500, description="Bot description (optional, max 500 chars)")
    confidence_threshold: int = Field(default=80, ge=0, le=100, description="Confidence threshold (0-100, default 80)")

    @field_validator('name')
    @classmethod
    def name_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Name cannot be empty or whitespace')
        return v.strip()

    @field_validator('description')
    @classmethod
    def description_not_empty(cls, v):
        if v is not None:
            return v.strip() if v else None
        return v

class BotUpdateRequest(BaseModel):
    """Request schema for updating a bot"""
    name: Optional[str] = Field(None, min_length=2, max_length=50, description="Bot name (2-50 chars)")
    description: Optional[str] = Field(None, max_length=500, description="Bot description (optional, max 500 chars)")
    confidence_threshold: Optional[int] = Field(None, ge=0, le=100, description="Confidence threshold (0-100)")
    avatar_url: Optional[str] = Field(None, description="Bot avatar URL")
    is_public: Optional[bool] = Field(None, description="Whether bot is publicly accessible")
    is_active: Optional[bool] = Field(None, description="Whether bot is active/enabled")

    @field_validator('name')
    @classmethod
    def name_not_empty(cls, v):
        if v is not None and (not v or not v.strip()):
            raise ValueError('Name cannot be empty or whitespace')
        return v.strip() if v else None

    @field_validator('description')
    @classmethod
    def description_not_empty(cls, v):
        if v is not None:
            return v.strip() if v else None
        return v

class BotDuplicateRequest(BaseModel):
    """Request schema for duplicating a bot"""
    name: Optional[str] = Field(None, min_length=2, max_length=50, description="New bot name (2-50 chars, optional)")

    @field_validator('name')
    @classmethod
    def name_not_empty(cls, v):
        if v is not None and (not v or not v.strip()):
            raise ValueError('Name cannot be empty or whitespace')
        return v.strip() if v else None

class BotResponse(BaseModel):
    """Response schema for bot operations"""
    id: UUID
    name: str
    description: Optional[str] = None
    confidence_threshold: int
    avatar_url: Optional[str] = None
    is_public: bool = False
    is_active: bool = True
    status: BotStatus
    created_by: UUID
    created_at: datetime
    updated_at: datetime
    tenant_id: UUID
    doc_count: int = 0  # Count of allowed documents for this bot

    model_config = {"from_attributes": True}

class BotListResponse(BaseModel):
    """Response schema for bot list (paginated)"""
    bots: list[BotResponse]
    total_count: int
    limit: int
    offset: int

    model_config = {"from_attributes": True}

class BotLimitExceededError(BaseModel):
    """Error response when bot limit reached"""
    error: str
    limit: int
    current: int
