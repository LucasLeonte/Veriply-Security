from sqlalchemy import Column, String, Uuid, ForeignKey, DateTime, Index
from datetime import datetime
from .base import Base

class Document(Base):
    __tablename__ = "documents"
    id = Column(Uuid, primary_key=True)
    bot_id = Column(Uuid, ForeignKey("bots.id", ondelete="CASCADE"), nullable=False)
    tenant_id = Column(Uuid, ForeignKey("tenants.id"), nullable=False)
    title = Column(String, nullable=False)
    status = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Indexes for bot_id and tenant_id to optimize queries
    __table_args__ = (
        Index("idx_documents_bot_id", "bot_id"),
        Index("idx_documents_tenant_id", "tenant_id"),
        Index("idx_documents_bot_tenant_id", "bot_id", "tenant_id"),
    )
