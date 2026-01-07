from sqlalchemy import Column, String, Uuid, ForeignKey, DateTime
from datetime import datetime
from .base import Base


class EmailProcessingQueue(Base):
    __tablename__ = "email_processing_queue"

    id = Column(Uuid, primary_key=True)
    tenant_id = Column(Uuid, ForeignKey("tenants.id"), nullable=False)
    integration_id = Column(Uuid, ForeignKey("email_integrations.id"), nullable=False)
    rule_id = Column(Uuid, ForeignKey("email_monitoring_rules.id"), nullable=True)

    provider_message_id = Column(String, nullable=False)
    status = Column(String, nullable=False, default="queued")

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
