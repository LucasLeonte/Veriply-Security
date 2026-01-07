from sqlalchemy import Column, String, Uuid, ForeignKey, DateTime, Boolean
from datetime import datetime
from .base import Base


class EmailIntegration(Base):
    __tablename__ = "email_integrations"
    id = Column(Uuid, primary_key=True)
    tenant_id = Column(Uuid, ForeignKey("tenants.id"), nullable=False)
    user_id = Column(Uuid, ForeignKey("users.id"), nullable=False)
    provider = Column(String, nullable=False)  # gmail | outlook
    encrypted_refresh_token = Column(String, nullable=True)
    scope = Column(String, nullable=True)
    status = Column(String, default="connected")
    last_sync_time = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
