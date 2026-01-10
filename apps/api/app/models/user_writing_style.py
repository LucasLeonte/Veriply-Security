from sqlalchemy import Column, String, Uuid, ForeignKey, DateTime, Boolean, Integer, Enum, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from datetime import datetime
from enum import Enum as PyEnum
from .base import Base


class ToneEnum(str, PyEnum):
    """Tone category enum."""
    FORMAL = "formal"
    SEMI_FORMAL = "semi_formal"
    CASUAL = "casual"
    FRIENDLY = "friendly"


class UserWritingStyle(Base):
    __tablename__ = "user_writing_styles"

    id = Column(Uuid, primary_key=True, server_default=func.gen_random_uuid())
    tenant_id = Column(Uuid, ForeignKey("tenants.id"), nullable=False)
    user_id = Column(Uuid, ForeignKey("users.id"), nullable=False)
    integration_id = Column(Uuid, ForeignKey("email_integrations.id"), nullable=False)
    
    # Auto-detected style
    tone = Column(String(20), nullable=False, default="semi_formal")  # formal, semi_formal, casual, friendly
    greeting_pattern = Column(String(100), nullable=True)
    closing_pattern = Column(String(100), nullable=True)
    avg_sentence_length = Column(Integer, nullable=True)
    avg_email_length = Column(Integer, nullable=True)
    uses_emojis = Column(Boolean, default=False)
    formality_score = Column(Integer, nullable=False, default=65)  # 0-100
    
    # Manual overrides
    custom_preferences = Column(JSONB, nullable=True, default={})  # JSON object with user overrides
    is_manual_override = Column(Boolean, default=False)
    
    # Analysis tracking
    sample_count = Column(Integer, default=0)  # Number of emails analyzed
    last_analyzed_at = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint('user_id', 'integration_id', 'tenant_id', 
                        name='uq_style_per_integration'),
    )
