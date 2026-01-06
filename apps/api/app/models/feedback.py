from datetime import datetime, timedelta
from uuid import uuid4
from enum import Enum as PyEnum

from sqlalchemy import Column, String, DateTime, Enum as SAEnum, ForeignKey, Index, UniqueConstraint, Integer
from sqlalchemy.dialects.postgresql import UUID as PGUUID

from .base import Base


class FeedbackType(str, PyEnum):
    POSITIVE = "positive"
    NEGATIVE = "negative"


class FeedbackReason(str, PyEnum):
    INCORRECT = "incorrect"
    NOT_HELPFUL = "not_helpful"
    INCOMPLETE = "incomplete"
    HARMFUL = "harmful"
    OTHER = "other"


class Feedback(Base):
    __tablename__ = "feedback"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(PGUUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    bot_id = Column(PGUUID(as_uuid=True), ForeignKey("bots.id"), nullable=False)
    user_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    answer_id = Column(PGUUID(as_uuid=True), nullable=False)
    message_id = Column(String(255), nullable=False)
    type = Column(SAEnum(FeedbackType), nullable=False)
    reason = Column(SAEnum(FeedbackReason), nullable=True)
    additional_notes = Column(String(500), nullable=True)
    session_id = Column(String(255), nullable=True)
    ip_address = Column(String(45), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint("user_id", "answer_id", name="uq_feedback_user_answer"),
        Index("ix_feedback_bot_answer", "bot_id", "answer_id"),
        Index("ix_feedback_user_recent", "user_id", "created_at"),
        Index("ix_feedback_session_recent", "session_id", "created_at"),
    )


class ModerationAlert(Base):
    __tablename__ = "moderation_alerts"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(PGUUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    bot_id = Column(PGUUID(as_uuid=True), ForeignKey("bots.id"), nullable=False)
    answer_id = Column(PGUUID(as_uuid=True), nullable=False)
    feedback_count = Column(Integer, nullable=False, default=0)
    user_ids = Column(String, nullable=False)  # comma-separated list for quick review
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("ix_moderation_alert_answer", "bot_id", "answer_id"),
    )


class UserAbuseSuspicion(Base):
    __tablename__ = "user_abuse_suspicions"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(PGUUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    user_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    bot_id = Column(PGUUID(as_uuid=True), ForeignKey("bots.id"), nullable=False)
    ip_address = Column(String(45), nullable=True)
    feedback_ids = Column(String, nullable=False)  # comma-separated list of feedback IDs in window
    window_start = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("ix_user_abuse_user_window", "user_id", "created_at"),
    )