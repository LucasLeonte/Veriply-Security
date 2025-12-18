from datetime import datetime
from uuid import uuid4

from sqlalchemy import Column, String, DateTime, Index, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB

from .base import Base


class ChatMessageLog(Base):
    __tablename__ = "chat_messages"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(PGUUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    bot_id = Column(PGUUID(as_uuid=True), ForeignKey("bots.id"), nullable=False)
    user_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    session_id = Column(String(255), nullable=True)
    client_message_id = Column(String(255), nullable=True)
    answer_id = Column(PGUUID(as_uuid=True), nullable=True)
    role = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    citations = Column(JSONB, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("ix_chat_messages_bot_created", "bot_id", "created_at"),
        Index("ix_chat_messages_bot_session", "bot_id", "session_id", "created_at"),
        Index("ix_chat_messages_bot_answer", "bot_id", "answer_id"),
    )
