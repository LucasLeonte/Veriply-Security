from sqlalchemy import Column, String, Uuid, ForeignKey, DateTime, Boolean, Integer
from sqlalchemy.dialects.postgresql import JSONB, ARRAY
from datetime import datetime
from .base import Base


class EmailMonitoringRule(Base):
    __tablename__ = "email_monitoring_rules"

    id = Column(Uuid, primary_key=True)
    tenant_id = Column(Uuid, ForeignKey("tenants.id"), nullable=False)
    user_id = Column(Uuid, ForeignKey("users.id"), nullable=False)
    integration_id = Column(Uuid, ForeignKey("email_integrations.id"), nullable=False)
    bot_id = Column(Uuid, ForeignKey("bots.id"), nullable=False)

    folder_labels = Column(JSONB, nullable=True)  # list[str]
    include_keywords = Column(ARRAY(String), nullable=True)
    exclude_keywords = Column(ARRAY(String), nullable=True)

    priority = Column(Integer, nullable=False, default=100)
    is_active = Column(Boolean, nullable=False, default=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
