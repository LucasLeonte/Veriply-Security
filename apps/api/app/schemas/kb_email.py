"""Pydantic schemas for KB Email operations."""

from datetime import datetime
from typing import Optional, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field


class KBEmailCreate(BaseModel):
    """Schema for creating a KB email entry."""
    group_id: UUID = Field(..., description="Group ID for scoping")
    email_id: str = Field(..., description="Provider's message ID")
    thread_id: Optional[str] = Field(None, description="Thread/conversation ID")
    subject: Optional[str] = Field(None, max_length=500)
    from_email: Optional[str] = Field(None, max_length=255)
    to_emails: Optional[str] = Field(None, description="Comma-separated list of recipients")
    body_text: Optional[str] = Field(None, description="Plain text email body")
    sent_at: Optional[datetime] = Field(None, description="Email send timestamp")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class KBEmailResponse(BaseModel):
    """Schema for KB email response."""
    id: UUID
    tenant_id: UUID
    group_id: UUID
    user_id: UUID
    integration_id: UUID
    
    email_id: str
    thread_id: Optional[str]
    
    subject: Optional[str]
    from_email: Optional[str]
    to_emails: Optional[str]
    body_text: Optional[str]
    sent_at: Optional[datetime]
    
    metadata: Optional[Dict[str, Any]] = Field(None, alias="email_metadata")
    
    status: str
    processed_at: Optional[datetime]
    chunk_count: Optional[str]
    
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class KBEmailListResponse(BaseModel):
    """Schema for paginated KB email list."""
    emails: list[KBEmailResponse]
    total: int
    page: int
    page_size: int
