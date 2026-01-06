from sqlalchemy import Column, String, Uuid, ForeignKey, DateTime
from datetime import datetime
from .base import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Uuid, primary_key=True)
    email = Column(String, nullable=False, unique=True)
    password_hash = Column(String, nullable=False)
    tenant_id = Column(Uuid, ForeignKey("tenants.id"), nullable=False)
    role = Column(String, nullable=False, default="agent")
    # Profile fields
    name = Column(String, nullable=True)
    avatar_url = Column(String, nullable=True)
    notification_frequency = Column(String, default="weekly")  # daily, weekly, never
    last_active = Column(DateTime, nullable=True)
    is_active = Column(String, default="active")  # active, inactive
    # Password reset fields
    password_reset_token = Column(String, nullable=True)
    password_reset_expires = Column(DateTime, nullable=True)
    # Tenant invitation fields (for cross-tenant transfer on acceptance)
    tenant_invite_token = Column(String, nullable=True)
    tenant_invite_expires = Column(DateTime, nullable=True)
    pending_tenant_id = Column(Uuid, nullable=True)
    pending_role = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
