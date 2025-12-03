from sqlalchemy import Column, String, Uuid, ForeignKey
from .base import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Uuid, primary_key=True)
    email = Column(String, nullable=False, unique=True)
    tenant_id = Column(Uuid, ForeignKey("tenants.id"), nullable=False)
    role = Column(String, nullable=False)
