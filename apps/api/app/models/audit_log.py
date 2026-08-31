from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from datetime import datetime
from uuid import uuid4
from .base import Base


class AuditLog(Base):
    """
    Persistent record of security-relevant events.

    Written by ``app.core.security_logger.log_security_event()`` for every
    auth, access-control, and rate-limit event in the system.
    """
    __tablename__ = "audit_logs"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # ---- Who ----------------------------------------------------------------
    # actor_id is nullable: unauthenticated events (login failure, token
    # forgery attempts) must be logged even when we have no valid user.
    tenant_id = Column(PGUUID(as_uuid=True), ForeignKey("tenants.id"), nullable=True)
    actor_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    # ---- What ---------------------------------------------------------------
    action = Column(String, nullable=False)       # Legacy: profile_update, role_change, ...
    event_type = Column(String, nullable=True)    # SecurityEvent enum value
    severity = Column(String, nullable=True)      # DEBUG / INFO / WARNING / CRITICAL
    outcome = Column(String, nullable=True)       # SUCCESS / FAILURE / BLOCKED
    details = Column(Text, nullable=True)         # Free-text or JSON detail string

    # ---- Where / How --------------------------------------------------------
    ip_address = Column(String(45), nullable=True)   # IPv4 or IPv6
    user_agent = Column(String(512), nullable=True)
    http_method = Column(String(10), nullable=True)
    http_path = Column(String(512), nullable=True)
    http_status = Column(Integer, nullable=True)
    request_id = Column(String(36), nullable=True)   # UUID correlation ID

