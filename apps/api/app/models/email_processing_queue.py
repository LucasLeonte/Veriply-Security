from sqlalchemy import Column, String, Uuid, ForeignKey, DateTime, Integer, Text, Index
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime
from .base import Base


class EmailProcessingQueue(Base):
    """Queue for email processing pipeline.
    
    Stores email IDs to be processed through the draft generation pipeline.
    Statuses: queued -> processing -> completed/failed
    """
    __tablename__ = "email_processing_queue"

    id = Column(Uuid, primary_key=True)
    tenant_id = Column(Uuid, ForeignKey("tenants.id"), nullable=False)
    user_id = Column(Uuid, ForeignKey("users.id"), nullable=False)  # Who initiated processing
    integration_id = Column(Uuid, ForeignKey("email_integrations.id"), nullable=False)
    rule_id = Column(Uuid, ForeignKey("email_monitoring_rules.id"), nullable=True)
    bot_id = Column(Uuid, ForeignKey("bots.id"), nullable=True)  # Resolved from rule

    provider_message_id = Column(String, nullable=False)  # Gmail thread ID or Outlook message ID
    email_subject = Column(String, nullable=True)
    email_body = Column(Text, nullable=True)
    sender_email = Column(String, nullable=True)
    thread_id = Column(String, nullable=True)  # For threading support
    
    status = Column(String, nullable=False, default="queued")  # queued, processing, completed, failed
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, nullable=False, default=0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    processed_at = Column(DateTime, nullable=True)

    # Indexes for FIFO queue processing and RLS
    __table_args__ = (
        Index("ix_email_queue_tenant_status_created", "tenant_id", "status", "created_at"),
        Index("ix_email_queue_integration_status", "integration_id", "status"),
    )
