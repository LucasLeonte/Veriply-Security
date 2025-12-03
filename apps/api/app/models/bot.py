from sqlalchemy import Column, String, Uuid, ForeignKey, JSON
from .base import Base

class Bot(Base):
    __tablename__ = "bots"
    id = Column(Uuid, primary_key=True)
    name = Column(String, nullable=False)
    tenant_id = Column(Uuid, ForeignKey("tenants.id"), nullable=False)
    config = Column(JSON, nullable=True)
