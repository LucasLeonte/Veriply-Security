from sqlalchemy import Column, String, Uuid, ForeignKey, DateTime, Text, Index
from datetime import datetime
from .base import Base


class Group(Base):
    """Group model representing a logical grouping of bots within a tenant.
    
    A group owns a single shared knowledge base used by all bots in the group.
    Multiple bots can be part of the same group, sharing indexed documents/chunks.
    
    Fields:
      - id: UUID primary key
      - tenant_id: FK -> tenants.id (tenant owner)
      - name: group name (unique per tenant)
      - description: optional group description
      - created_by: FK -> users.id (user who created the group)
      - created_at / updated_at: timestamps
    """

    __tablename__ = "groups"

    id = Column(Uuid, primary_key=True, default=lambda: __import__('uuid').uuid4())
    tenant_id = Column(Uuid, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(50), nullable=False)
    description = Column(Text, nullable=True)
    created_by = Column(Uuid, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index('ix_groups_tenant_id', 'tenant_id'),
        Index('ix_groups_tenant_name', 'tenant_id', 'name'),
        __import__('sqlalchemy').UniqueConstraint('tenant_id', 'name', name='uq_groups_tenant_name'),
    )
