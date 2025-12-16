"""Data models and schemas for citations."""

from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum


class ConfidenceLevel(str, Enum):
    """Citation confidence levels based on similarity."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Citation(BaseModel):
    """Citation metadata linking answer text to source chunk."""

    id: str = Field(..., description="Unique citation ID (c1, c2, etc)")
    chunk_id: str = Field(..., description="Source chunk ID")
    document_id: str = Field(..., description="Source document ID")
    document_name: str = Field(..., description="Human-readable document name")
    section: Optional[str] = Field(None, description="Document section/chapter")
    page_number: Optional[int] = Field(None, description="Page number (if PDF)")
    similarity_score: float = Field(..., ge=0.0, le=1.0, description="Similarity score 0-1")
    chunk_position: int = Field(0, description="Position in document")
    confidence: ConfidenceLevel = Field(..., description="Confidence level")
    text_snippet: str = Field("", description="Chunk text snippet (truncated)")


class AnnotatedAnswer(BaseModel):
    """Answer with inline citations."""

    answer: str = Field(..., description="Raw answer text")
    answer_html: str = Field(
        ..., description="HTML with embedded citation spans (data-citation-id)"
    )
    citations: List[Citation] = Field(default_factory=list, description="Citation metadata")
    missing_citations: List[str] = Field(
        default_factory=list,
        description="Sentences without citations (error case)",
    )


class QueryWithCitationsRequest(BaseModel):
    """Request for query with citation post-processing."""

    query: str = Field(..., min_length=1, max_length=2000, description="User's question")
    stream: bool = Field(
        default=False, description="Stream response tokens (citations only work with non-streaming)"
    )
    conversation_history: Optional[List[dict]] = Field(
        default=None, description="Previous messages for context"
    )
    k: int = Field(
        default=5, ge=1, le=20, description="Number of context chunks to retrieve"
    )


class QueryWithCitationsResponse(BaseModel):
    """Response from query with citations endpoint."""

    annotated_answer: AnnotatedAnswer = Field(..., description="Answer with citations")
    metadata: dict = Field(..., description="Query execution metadata")
