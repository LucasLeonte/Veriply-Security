from sqlalchemy import Column, String, Uuid
from .base import Base

class Tenant(Base):
    __tablename__ = "tenants"
    id = Column(Uuid, primary_key=True)
    name = Column(String, nullable=False)
    plan = Column(String, nullable=False)
