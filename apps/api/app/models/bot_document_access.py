from sqlalchemy import Column, Uuid, ForeignKey, DateTime, Boolean, Index, UniqueConstraint, CheckConstraint
from datetime import datetime
from .base import Base


class BotDocumentAccess(Base):
    __tablename__ = "bot_document_access"

    id = Column(Uuid, primary_key=True, default=lambda: __import__('uuid').uuid4())
    tenant_id = Column(Uuid, ForeignKey("tenants.id"), nullable=False)
    group_id = Column(Uuid, ForeignKey("groups.id", ondelete="CASCADE"), nullable=False)
    bot_id = Column(Uuid, ForeignKey("bots.id", ondelete="CASCADE"), nullable=False)
    document_id = Column(Uuid, ForeignKey("documents.id", ondelete="CASCADE"), nullable=True)
    folder_id = Column(Uuid, ForeignKey("folders.id", ondelete="CASCADE"), nullable=True)
    is_allowed = Column(Boolean, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index('ix_bot_document_access_tenant_id', 'tenant_id'),
        Index('ix_bot_document_access_group_id', 'group_id'),
        Index('ix_bot_document_access_tenant_group', 'tenant_id', 'group_id'),
        Index('ix_bot_document_access_bot_document', 'bot_id', 'document_id'),
        Index('ix_bot_document_access_bot_folder', 'bot_id', 'folder_id'),
        UniqueConstraint('bot_id', 'document_id', name='uq_bot_document_access_bot_document'),
        UniqueConstraint('bot_id', 'folder_id', name='uq_bot_document_access_bot_folder'),
        CheckConstraint(
            '(document_id IS NOT NULL AND folder_id IS NULL) OR (document_id IS NULL AND folder_id IS NOT NULL)',
            name='chk_bot_document_access_one_target'
        ),
    )
