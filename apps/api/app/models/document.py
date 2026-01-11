from sqlalchemy import Column, String, Integer, Uuid, ForeignKey, DateTime, Text, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import Base


class Document(Base):
    __tablename__ = "documents"

    id = Column(Uuid, primary_key=True, default=lambda: __import__('uuid').uuid4())
    tenant_id = Column(Uuid, ForeignKey("tenants.id"), nullable=False)
    group_id = Column(Uuid, ForeignKey("groups.id", ondelete="CASCADE"), nullable=False)
    folder_id = Column(Uuid, ForeignKey("folders.id", ondelete="SET NULL"), nullable=True)
    title = Column(String(255), nullable=False)  # Database column is 'title'
    mime = Column(String(100), nullable=True)
    size = Column(Integer, nullable=True)
    storage_path = Column(Text, nullable=True)
    status = Column(String(50), nullable=False, default="uploaded")
    uploader_id = Column(Uuid, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    deleted_at = Column(DateTime, nullable=True)

    __table_args__ = (
        Index('ix_documents_tenant_id', 'tenant_id'),
        Index('ix_documents_group_id', 'group_id'),
        Index('ix_documents_folder_id', 'folder_id'),
        Index('ix_documents_tenant_group', 'tenant_id', 'group_id'),
        Index('ix_documents_status', 'status'),
        Index('ix_documents_deleted', 'deleted_at'),
    )

    uploader = relationship("User", foreign_keys=[uploader_id], lazy="joined")
    
    @property
    def filename(self):
        """Alias for title - API expects 'filename' but DB column is 'title'"""
        return self.title

    @property
    def uploader_name(self):
        """Get the name or email of the uploader."""
        if self.uploader:
            return self.uploader.name or self.uploader.email
        return str(self.uploader_id)
