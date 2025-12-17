"""Pydantic schemas for confidence scoring and routing.

Story 3.4: Confidence Scoring & Routing
"""

from decimal import Decimal
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class RoutingDecisionEnum(str, Enum):
    """Routing decision outcomes for API responses."""
    AUTO_SEND = "auto_send"
    HITL = "hitl"


class ConfidenceComponents(BaseModel):
    """Individual confidence score components."""
    
    retrieval_confidence: float = Field(
        ..., 
        ge=0, 
        le=1,
        description="Max similarity from vector search (0-1)"
    )
    context_coverage: float = Field(
        ..., 
        ge=0,
        le=1,
        description="Coverage of the answer supported by retrieved context (0-1)"
    )
    source_consistency: Optional[float] = Field(
        None,
        ge=0,
        le=1,
        description="Agreement between retrieved sources (0-1)"
    )
    generation_confidence: Optional[float] = Field(
        None,
        ge=0,
        le=1,
        description="LLM generation confidence from logprobs (0-1)"
    )


class ConfidenceScore(BaseModel):
    """Confidence score with components and reasoning."""
    
    overall_score: int = Field(
        ...,
        ge=0,
        le=100,
        description="Overall confidence score (0-100%)"
    )
    components: ConfidenceComponents = Field(
        ...,
        description="Individual confidence components"
    )
    reasoning: str = Field(
        ...,
        description="Human-readable explanation of the score"
    )


class RoutingInfo(BaseModel):
    """Routing decision information."""
    
    decision: RoutingDecisionEnum = Field(
        ...,
        description="Whether to auto-send or route to HITL"
    )
    reason: str = Field(
        ...,
        description="Explanation for routing decision"
    )
    end_user_message: Optional[str] = Field(
        None,
        description="Message to show end-user if routed to HITL"
    )


class QueryWithConfidenceRequest(BaseModel):
    """Request for query with confidence calculation."""
    
    query: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="User's question"
    )
    calculate_confidence: bool = Field(
        default=True,
        description="Whether to calculate and return confidence"
    )
    auto_send_threshold: Optional[int] = Field(
        None,
        ge=0,
        le=100,
        description="Override bot's default threshold (0-100)"
    )


class QueryWithConfidenceResponse(BaseModel):
    """Response from query with confidence scoring."""
    
    answer: str = Field(
        ...,
        description="Generated answer text"
    )
    confidence: ConfidenceScore = Field(
        ...,
        description="Confidence score details"
    )
    routing: RoutingInfo = Field(
        ...,
        description="Routing decision details"
    )
    source: str = Field(
        ...,
        description="Answer source: 'rag' or 'verified_kb'"
    )
    query_id: UUID = Field(
        ...,
        description="Unique identifier for this query"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "answer": "The refund policy allows returns within 30 days.",
                "confidence": {
                    "overall_score": 85,
                    "components": {
                        "retrieval_confidence": 0.89,
                        "context_coverage": 0.87,
                        "source_consistency": 0.87,
                        "generation_confidence": None
                    },
                    "reasoning": "Excellent retrieval match, high agreement between sources. Score (85%) exceeds threshold (80%)."
                },
                "routing": {
                    "decision": "auto_send",
                    "reason": "Overall confidence (85%) exceeds threshold (80%)",
                    "end_user_message": None
                },
                "source": "rag",
                "query_id": "550e8400-e29b-41d4-a716-446655440000"
            }
        }


class HITLPendingResponse(BaseModel):
    """Response when query is routed to HITL."""
    
    message: str = Field(
        ...,
        description="Message to display to end-user"
    )
    confidence: ConfidenceScore = Field(
        ...,
        description="Confidence score details"
    )
    routing: RoutingInfo = Field(
        ...,
        description="Routing decision details"
    )
    query_id: UUID = Field(
        ...,
        description="Query ID for tracking in HITL queue"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "message": "I'm checking with the team for the best answer. You'll hear from us shortly.",
                "confidence": {
                    "overall_score": 35,
                    "components": {
                        "retrieval_confidence": 0.42,
                        "context_coverage": 0.35,
                        "source_consistency": 0.35,
                        "generation_confidence": None
                    },
                    "reasoning": "Poor retrieval match, sources may be contradictory. Score (35%) below threshold (80%) - routing to human review."
                },
                "routing": {
                    "decision": "hitl",
                    "reason": "Low confidence (35%) below threshold (80%)",
                    "end_user_message": "I'm checking with the team for the best answer. You'll hear from us shortly."
                },
                "query_id": "550e8400-e29b-41d4-a716-446655440001"
            }
        }
