"""Schemas for query/chat endpoints."""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


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
    """Metadata about the query execution."""

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
