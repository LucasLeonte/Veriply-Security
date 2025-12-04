from sqlalchemy import Column, String, Integer, Uuid, ForeignKey, DateTime, Enum as SQLEnum, Text, Index
from datetime import datetime
import enum
from .base import Base

class BotStatus(str, enum.Enum):
    EMPTY = "Empty"
    PROCESSING = "Processing"
    READY = "Ready"

class Bot(Base):
    __tablename__ = "bots"
    
    id = Column(Uuid, primary_key=True, default=lambda: __import__('uuid').uuid4())
    tenant_id = Column(Uuid, ForeignKey("tenants.id"), nullable=False, index=True)
    name = Column(String(50), nullable=False)
    description = Column(Text, nullable=True)
    confidence_threshold = Column(Integer, default=80, nullable=False)
    status = Column(SQLEnum(BotStatus), default=BotStatus.EMPTY, nullable=False)
    created_by = Column(Uuid, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Indexes
    __table_args__ = (
        Index('ix_bots_tenant_id', 'tenant_id'),
        Index('ix_bots_tenant_created', 'tenant_id', 'created_at'),
        # Unique constraint on tenant_id + name
        __import__('sqlalchemy').UniqueConstraint('tenant_id', 'name', name='uq_bots_tenant_name'),
    )
