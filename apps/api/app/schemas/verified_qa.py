"""Pydantic schemas for VerifiedQA API endpoints.

These schemas handle validation and serialization for verified Q&A pair operations,
including creation from HITL approvals, updates, and query responses.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Any, Union
from uuid import UUID
from datetime import datetime


class VerifiedQACreate(BaseModel):
    """Schema for creating a new verified Q&A entry.
    
    Used when HITL approval creates a verified entry or when manually
    adding Q&A pairs through the API.
    """
    
    question_text: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="The verified question text"
    )
    answer_text: str = Field(
        ...,
        min_length=1,
        description="The approved answer text"
    )
    group_id: UUID = Field(
        ...,
        description="Group ID this Q&A belongs to (shared across all bots in the group)"
    )
    source_citations: Optional[Union[List[Any], dict]] = Field(
        default=None,
        description="Optional source document citations in JSONB format"
    )
    
    @field_validator("question_text")
    @classmethod
    def validate_question_text(cls, v: str) -> str:
        """Validate and clean question text."""
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("Question text cannot be empty or whitespace only")
        return cleaned
    
    @field_validator("answer_text")
    @classmethod
    def validate_answer_text(cls, v: str) -> str:
        """Validate and clean answer text."""
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("Answer text cannot be empty or whitespace only")
        return cleaned
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "question_text": "What is the return policy for defective products?",
                "answer_text": "We offer a 30-day return policy for defective products. Please contact support@example.com with your order number and photos of the defect.",
                "group_id": "550e8400-e29b-41d4-a716-446655440000",
                "source_citations": {
                    "documents": [
                        {
                            "title": "Return Policy Guide",
                            "page": 3,
                            "section": "Defective Products"
                        }
                    ]
                }
            }
        }
    }


class VerifiedQAResponse(BaseModel):
    """Schema for verified Q&A responses.
    
    Returned from API endpoints when querying or listing verified entries.
    Q&A entries are group-scoped (shared across all bots in the group).
    """
    
    id: UUID = Field(..., description="Unique identifier")
    tenant_id: UUID = Field(..., description="Tenant ID")
    group_id: UUID = Field(..., description="Group ID")
    bot_id: Optional[UUID] = Field(None, description="Bot ID (optional, Q&A is now group-scoped)")
    
    question_text: str = Field(..., description="The verified question")
    answer_text: str = Field(..., description="The approved answer")
    source_citations: Optional[Union[List[Any], dict]] = Field(None, description="Source citations")
    
    approved_by_user_id: Optional[UUID] = Field(None, description="User who approved this")
    approved_at: datetime = Field(..., description="When this was approved")
    
    created_at: datetime = Field(..., description="Record creation time")
    updated_at: datetime = Field(..., description="Last update time")
    
    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "tenant_id": "550e8400-e29b-41d4-a716-446655440000",
                "group_id": "660e8400-e29b-41d4-a716-446655440000",
                "bot_id": None,
                "question_text": "What is the return policy for defective products?",
                "answer_text": "We offer a 30-day return policy for defective products. Contact support@example.com.",
                "source_citations": {
                    "documents": [{"title": "Return Policy Guide", "page": 3}]
                },
                "approved_by_user_id": "880e8400-e29b-41d4-a716-446655440000",
                "approved_at": "2026-01-06T10:30:00Z",
                "created_at": "2026-01-06T10:30:00Z",
                "updated_at": "2026-01-06T10:30:00Z"
            }
        }
    }


class VerifiedQAUpdate(BaseModel):
    """Schema for updating a verified Q&A entry.
    
    All fields optional to support partial updates. Used in Story 7.4
    for editing existing verified entries.
    """
    
    question_text: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=2000,
        description="Updated question text"
    )
    answer_text: Optional[str] = Field(
        default=None,
        min_length=1,
        description="Updated answer text"
    )
    source_citations: Optional[dict] = Field(
        default=None,
        description="Updated source citations"
    )
    
    @field_validator("question_text")
    @classmethod
    def validate_question_text(cls, v: Optional[str]) -> Optional[str]:
        """Validate and clean question text if provided."""
        if v is not None:
            cleaned = v.strip()
            if not cleaned:
                raise ValueError("Question text cannot be empty or whitespace only")
            return cleaned
        return v
    
    @field_validator("answer_text")
    @classmethod
    def validate_answer_text(cls, v: Optional[str]) -> Optional[str]:
        """Validate and clean answer text if provided."""
        if v is not None:
            cleaned = v.strip()
            if not cleaned:
                raise ValueError("Answer text cannot be empty or whitespace only")
            return cleaned
        return v
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "answer_text": "Updated: We offer a 45-day return policy for defective products (extended from 30 days)."
            }
        }
    }


class VerifiedQAListResponse(BaseModel):
    """Paginated list of verified Q&A entries."""
    
    items: list[VerifiedQAResponse] = Field(..., description="List of verified Q&A entries")
    total: int = Field(..., description="Total count of entries (before pagination)")
    limit: int = Field(..., description="Items per page")
    offset: int = Field(..., description="Current page offset")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "items": [],
                "total": 42,
                "limit": 20,
                "offset": 0
            }
        }
    }
