from sqlalchemy import Column, String, Uuid, ForeignKey, DateTime, Boolean, Text
from sqlalchemy.sql import func
from datetime import datetime
from .base import Base


class UserEmailHistory(Base):
    __tablename__ = "user_email_history"

    id = Column(Uuid, primary_key=True, server_default=func.gen_random_uuid())
    tenant_id = Column(Uuid, ForeignKey("tenants.id"), nullable=False)
    user_id = Column(Uuid, ForeignKey("users.id"), nullable=False)
    integration_id = Column(Uuid, ForeignKey("email_integrations.id"), nullable=False)
    
    email_id = Column(String, nullable=False)  # Gmail message ID or Outlook message ID
    subject = Column(String, nullable=True)
    body = Column(Text, nullable=True)
    sent_at = Column(DateTime, nullable=True)
    
    analyzed = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        # Unique constraint: one entry per email per integration
        # (to prevent duplicates from periodic syncs)
    )
