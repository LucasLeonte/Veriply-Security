from sqlalchemy import Column, String, Uuid, Enum as SQLEnum
import enum
from .base import Base

class SubscriptionTier(str, enum.Enum):
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"

class Tenant(Base):
    __tablename__ = "tenants"
    id = Column(Uuid, primary_key=True)
    name = Column(String, nullable=False)
    plan = Column(String, nullable=False)
    subscription_tier = Column(SQLEnum(SubscriptionTier), default=SubscriptionTier.FREE, nullable=False)
