from sqlalchemy import Column, String, Uuid, ForeignKey, DateTime, Index, UniqueConstraint
from datetime import datetime
from .base import Base


class Folder(Base):
    __tablename__ = "folders"

    id = Column(Uuid, primary_key=True, default=lambda: __import__('uuid').uuid4())
    tenant_id = Column(Uuid, ForeignKey("tenants.id"), nullable=False)
    group_id = Column(Uuid, ForeignKey("groups.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    created_by = Column(Uuid, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    deleted_at = Column(DateTime, nullable=True)

    __table_args__ = (
        Index('ix_folders_tenant_id', 'tenant_id'),
        Index('ix_folders_group_id', 'group_id'),
        Index('ix_folders_tenant_group', 'tenant_id', 'group_id'),
        Index('ix_folders_deleted', 'deleted_at'),
        UniqueConstraint('tenant_id', 'group_id', 'name', name='uq_folders_tenant_group_name'),
    )
