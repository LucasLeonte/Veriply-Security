from sqlalchemy import Column, String, Uuid, ForeignKey, DateTime, Text
from datetime import datetime
from .base import Base

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(Uuid, primary_key=True)
    tenant_id = Column(Uuid, ForeignKey("tenants.id"), nullable=False)
    actor_id = Column(Uuid, ForeignKey("users.id"), nullable=False)
    target_user_id = Column(Uuid, ForeignKey("users.id"), nullable=True)
    action = Column(String, nullable=False)  # profile_update, role_change, user_removed, etc.
    details = Column(Text, nullable=True)  # JSON string with change details
    created_at = Column(DateTime, default=datetime.utcnow)
