from sqlalchemy import Column, String, Integer, Uuid, ForeignKey, DateTime, Text, Index
from datetime import datetime
from .base import Base


class Document(Base):
    __tablename__ = "documents"

    id = Column(Uuid, primary_key=True, default=lambda: __import__('uuid').uuid4())
    tenant_id = Column(Uuid, ForeignKey("tenants.id"), nullable=False)
    bot_id = Column(Uuid, ForeignKey("bots.id"), nullable=True)
    title = Column(String(255), nullable=True)
    filename = Column(String(255), nullable=True)
    mime = Column(String(100), nullable=True)
    size = Column(Integer, nullable=True)
    storage_path = Column(Text, nullable=True)
    status = Column(String(50), nullable=False, default="uploaded")
    uploaded_by = Column(Uuid, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index('ix_documents_tenant_id', 'tenant_id'),
        Index('ix_documents_bot_id', 'bot_id'),
    )
