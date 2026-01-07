from datetime import datetime

from sqlalchemy import Column, String, Uuid, DateTime, ForeignKey

from .base import Base


class IntegrationCredentials(Base):
    __tablename__ = "integration_credentials"

    id = Column(Uuid, primary_key=True)
    tenant_id = Column(Uuid, ForeignKey("tenants.id"), nullable=True)  # null => global default
    provider = Column(String, nullable=False)  # gmail | outlook
    client_id = Column(String, nullable=False)
    encrypted_client_secret = Column(String, nullable=False)
    redirect_uri = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)