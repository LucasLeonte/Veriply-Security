"""VerifiedQA model for human-validated Q&A pairs.

This model stores verified Q&A pairs from HITL approvals, forming the "golden dataset"
that takes precedence over RAG-generated answers. Each entry includes the question text,
its semantic embedding, the approved answer, and full audit metadata.
"""

from sqlalchemy import Column, Text, DateTime, ForeignKey, Index, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector
from datetime import datetime
from uuid import uuid4

from .base import Base


class VerifiedQA(Base):
    """Verified Q&A pairs from human approval.
    
    Represents human-validated question-answer pairs that have been approved
    through the HITL workflow. These entries form a "golden dataset" that
    takes priority over RAG-generated responses in query-time retrieval.
    
    Attributes:
        id: Primary key UUID
        tenant_id: Tenant isolation (FK to tenants)
        group_id: Group-level scoping (FK to groups)
        bot_id: Bot association (FK to bots)
        question_text: The verified question (max 2000 chars)
        question_embedding: 768-dim vector embedding for semantic search
        answer_text: The approved answer text
        source_citations: JSONB with document references/citations
        approved_by_user_id: User who approved this entry (FK to users)
        approved_at: Timestamp of approval
        created_at: Record creation timestamp
        updated_at: Last update timestamp
    """
    
    __tablename__ = "verified_qa"
    
    # Primary key
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4, nullable=False)
    
    # Multi-tenant scoping
    tenant_id = Column(PGUUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    group_id = Column(PGUUID(as_uuid=True), ForeignKey("groups.id", ondelete="CASCADE"), nullable=False)
    bot_id = Column(PGUUID(as_uuid=True), ForeignKey("bots.id", ondelete="CASCADE"), nullable=False)
    
    # Q&A content
    question_text = Column(Text, nullable=False)
    question_embedding = Column(Vector(768), nullable=True)  # nomic-embed-text produces 768-dim vectors
    answer_text = Column(Text, nullable=False)
    source_citations = Column(JSONB, nullable=True)
    
    # Audit metadata
    approved_by_user_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    # Note: These will be lazy-loaded by default for performance
    # Use joinedload in queries when relationships are needed
    bot = relationship("Bot", foreign_keys=[bot_id], lazy="select")
    group = relationship("Group", foreign_keys=[group_id], lazy="select")
    tenant = relationship("Tenant", foreign_keys=[tenant_id], lazy="select")
    approved_by = relationship("User", foreign_keys=[approved_by_user_id], lazy="select")
    
    # Table args: indexes, constraints, RLS
    __table_args__ = (
        # Composite indexes for scoped queries
        Index("idx_verified_qa_scope", "tenant_id", "group_id", "bot_id"),
        Index("idx_verified_qa_tenant_group", "tenant_id", "group_id"),
        
        # Individual foreign key indexes
        Index("idx_verified_qa_tenant_id", "tenant_id"),
        Index("idx_verified_qa_group_id", "group_id"),
        Index("idx_verified_qa_bot_id", "bot_id"),
        Index("idx_verified_qa_approved_by", "approved_by_user_id"),
        Index("idx_verified_qa_approved_at", "approved_at"),
        
        # Question text length constraint
        CheckConstraint("length(question_text) <= 2000", name="ck_verified_qa_question_length"),
        
        # Vector index is created in migration (cannot be defined here)
        # See migration: 012_add_verified_qa_table.py
    )
    
    def __repr__(self) -> str:
        """String representation for debugging."""
        return (
            f"<VerifiedQA(id={self.id}, bot_id={self.bot_id}, "
            f"question='{self.question_text[:50]}...', "
            f"approved_at={self.approved_at})>"
        )
