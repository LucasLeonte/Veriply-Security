from sqlalchemy import Column, String, Uuid, ForeignKey
from .base import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Uuid, primary_key=True)
    email = Column(String, nullable=False, unique=True)
    password_hash = Column(String, nullable=False)
    tenant_id = Column(Uuid, ForeignKey("tenants.id"), nullable=False)
    role = Column(String, nullable=False)
