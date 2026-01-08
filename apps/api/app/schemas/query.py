"""Schemas for query/chat endpoints."""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from uuid import UUID


class QueryRequest(BaseModel):
    """Request schema for answering a question."""

    query: str = Field(..., min_length=1, max_length=2000, description="User's question")
    stream: bool = Field(
        default=True, description="Stream response tokens (SSE) or return complete JSON"
    )
    conversation_history: Optional[List[Dict[str, str]]] = Field(
        default=None,
        description="Previous messages for context (role/content dicts)",
    )
    k: int = Field(
        default=5, ge=1, le=20, description="Number of context chunks to retrieve"
    )


class QueryMetadata(BaseModel):
    """Metadata about the query execution.
    
    Story 7.2: Extended with verified KB provenance fields.
    """

    query: str
    bot_id: str
    tenant_id: str
    k: int
    context_chunks: int
    search_latency_ms: int
    tokens_generated: int
    generation_latency_s: float
    model: str
    search_results: Optional[List[Dict[str, Any]]] = None
    # Story 7.2: Verified KB metadata
    verified: bool = Field(
        default=False,
        description="True if answer came from Verified KB (Story 7.2)"
    )
    verified_id: Optional[UUID] = Field(
        default=None,
        description="VerifiedQA entry ID if answer is verified"
    )
    verified_confidence: Optional[float] = Field(
        default=None,
        description="Similarity score of verified match (0-1)"
    )
    verified_citations: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Source citations from verified entry"
    )


class QueryResponse(BaseModel):
    """Response schema for non-streaming queries."""

    answer: str
    metadata: QueryMetadata


class StreamingToken(BaseModel):
    """A single token from streaming response."""

    token: str
    position: int


class StreamingComplete(BaseModel):
    """Final event when streaming is complete."""

    metadata: QueryMetadata
