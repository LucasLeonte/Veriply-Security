from sqlalchemy import Column, String, Uuid, ForeignKey
from .base import Base

class Document(Base):
    __tablename__ = "documents"
    id = Column(Uuid, primary_key=True)
    title = Column(String, nullable=False)
    tenant_id = Column(Uuid, ForeignKey("tenants.id"), nullable=False)
    status = Column(String, nullable=False)
