"""ConfidenceLog model for tracking query confidence scores and routing decisions.

Stores confidence calculation components and routing decisions for analytics,
debugging, and calibration of the confidence scoring system.
"""

from datetime import datetime
import enum
from sqlalchemy import (
    Column,
    String,
    Uuid,
    ForeignKey,
    DateTime,
    Enum as SQLEnum,
    Index,
    Numeric,
    Boolean,
    JSON,
)
from sqlalchemy.orm import relationship
from .base import Base


class RoutingDecision(str, enum.Enum):
    """Routing decision outcomes."""
    auto_send = "auto_send"
    hitl = "hitl"


class ConfidenceLog(Base):
    """Model for tracking confidence scores and routing decisions.
    
    Attributes:
        id: Unique identifier
        bot_id: Bot that processed the query
        tenant_id: Tenant for RLS
        query_id: Unique identifier for the query/interaction
        query_text: Original query text (truncated for storage)
        
        # Confidence Components (0.00-1.00)
        retrieval_confidence: Max similarity score from vector search
        source_consistency: Agreement between retrieved chunks
        generation_confidence: LLM's self-reported confidence
        
        # Result
        overall_confidence: Weighted combination of components
        threshold_used: Bot's confidence threshold at time of query
        routing_decision: auto_send or hitl
        is_verified_kb: Whether answer came from verified KB
        
        # Metadata
        created_at: Timestamp of calculation
    """
    __tablename__ = "confidence_logs"
    
    id = Column(Uuid, primary_key=True, default=lambda: __import__('uuid').uuid4())
    bot_id = Column(Uuid, ForeignKey("bots.id", ondelete="CASCADE"), nullable=False)
    tenant_id = Column(Uuid, ForeignKey("tenants.id"), nullable=False)
    group_id = Column(Uuid, ForeignKey("groups.id", ondelete="CASCADE"), nullable=True)
    user_id = Column(Uuid, ForeignKey("users.id"), nullable=True)
    query_id = Column(Uuid, nullable=False)  # Links to interaction/chat session
    query_text = Column(String(500), nullable=True)  # Truncated for storage
    
    # Confidence Components (stored as decimal 0.00-1.00)
    retrieval_confidence = Column(Numeric(4, 3), nullable=False)  # 0.000-1.000
    source_consistency = Column(Numeric(4, 3), nullable=True)  # Placeholder for future
    generation_confidence = Column(Numeric(4, 3), nullable=True)  # Placeholder for logprobs
    
    # Result
    overall_confidence = Column(Numeric(4, 3), nullable=False)
    threshold_used = Column(Numeric(4, 3), nullable=False)  # Bot threshold at query time
    routing_decision = Column(SQLEnum(RoutingDecision, values_callable=lambda x: [e.value for e in x]), nullable=False)
    is_verified_kb = Column(Boolean, default=False, nullable=False)
    
    # HITL Review
    hitl_resolved = Column(Boolean, default=False, nullable=False)
    resolution_user_id = Column(Uuid, ForeignKey("users.id"), nullable=True)
    resolution_timestamp = Column(DateTime, nullable=True)
    metadata_json = Column(JSON, nullable=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    bot = relationship("Bot", lazy="joined")
    
    # Indexes for common queries
    __table_args__ = (
        Index('ix_confidence_logs_bot_id', 'bot_id'),
        Index('ix_confidence_logs_tenant_id', 'tenant_id'),
        Index('ix_confidence_logs_group_id', 'group_id'),
        Index('ix_confidence_logs_routing', 'bot_id', 'routing_decision'),
        Index('ix_confidence_logs_created', 'bot_id', 'created_at'),
        Index('ix_confidence_logs_confidence', 'overall_confidence'),
        Index('ix_confidence_logs_hitl_open', 'tenant_id', 'group_id', 'hitl_resolved'),
    )
