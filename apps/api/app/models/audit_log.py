from sqlalchemy import Column, String, Uuid, ForeignKey, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from datetime import datetime
from uuid import uuid4
from .base import Base

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(PGUUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    actor_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    target_user_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    action = Column(String, nullable=False)  # profile_update, role_change, user_removed, etc.
    details = Column(Text, nullable=True)  # JSON string with change details
    created_at = Column(DateTime, default=datetime.utcnow)
