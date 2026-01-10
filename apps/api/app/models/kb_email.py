"""KBEmail model for emails imported into knowledge base.

This model stores emails that have been imported into the KB for RAG retrieval,
separate from documents. Used for both answering questions and writing style analysis.
"""

from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Index, Boolean
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector
from datetime import datetime
from uuid import uuid4

from .base import Base


class KBEmail(Base):
    """Emails imported into knowledge base.
    
    Stores emails imported from Gmail/Outlook for use in RAG retrieval and 
    writing style analysis. Emails are processed into chunks and embedded
    similar to documents.
    
    Attributes:
        id: Primary key UUID
        tenant_id: Tenant isolation (FK to tenants)
        group_id: Group-level scoping (FK to groups)
        user_id: User who imported this email (FK to users)
        integration_id: Email integration used (FK to email_integrations)
        
        email_id: Provider's message ID (Gmail/Outlook)
        thread_id: Provider's thread/conversation ID
        subject: Email subject line
        from_email: Sender email address
        to_emails: Recipient email addresses (comma-separated)
        body_text: Plain text email body
        sent_at: Original email send timestamp
        
        embedding: 768-dim vector embedding for semantic search
        email_metadata: JSONB with additional email metadata (renamed from metadata)
        
        status: Processing status (uploaded, processing, ready, failed)
        processed_at: Timestamp when processing completed
        chunk_count: Number of text chunks created from this email
        
        created_at: Record creation timestamp
        updated_at: Last update timestamp
    """
    
    __tablename__ = "kb_emails"
    
    # Primary key
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4, nullable=False)
    
    # Multi-tenant scoping
    tenant_id = Column(PGUUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    group_id = Column(PGUUID(as_uuid=True), ForeignKey("groups.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    integration_id = Column(PGUUID(as_uuid=True), ForeignKey("email_integrations.id", ondelete="CASCADE"), nullable=False)
    
    # Email identifiers
    email_id = Column(String, nullable=False)  # Gmail message ID or Outlook message ID
    thread_id = Column(String, nullable=True)  # Thread/conversation ID
    
    # Email content
    subject = Column(String(500), nullable=True)
    from_email = Column(String(255), nullable=True)
    to_emails = Column(Text, nullable=True)  # Comma-separated list
    body_text = Column(Text, nullable=True)
    sent_at = Column(DateTime, nullable=True)
    
    # Embeddings and metadata
    embedding = Column(Vector(768), nullable=True)
    email_metadata = Column(JSONB, nullable=True)  # Renamed from 'metadata' (reserved by SQLAlchemy)
    
    # Processing status
    status = Column(String(50), nullable=False, default="uploaded")  # uploaded, processing, ready, failed
    processed_at = Column(DateTime, nullable=True)
    chunk_count = Column(String, nullable=True)  # Number of chunks created
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Indexes for efficient queries
    __table_args__ = (
        Index("idx_kb_emails_tenant_group", "tenant_id", "group_id"),
        Index("idx_kb_emails_integration", "integration_id"),
        Index("idx_kb_emails_status", "status"),
        Index("idx_kb_emails_email_id", "email_id"),
        Index("idx_kb_emails_sent_at", "sent_at"),
        # Vector similarity search index
        Index(
            "idx_kb_emails_embedding",
            "embedding",
            postgresql_using="ivfflat",
            postgresql_with={"lists": 100},
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
    )
