from __future__ import annotations

from datetime import datetime
from uuid import uuid4, UUID

from sqlalchemy import Column, String, Boolean, DateTime, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class WidgetPosition(str):
    BOTTOM_RIGHT = "bottom-right"
    BOTTOM_LEFT = "bottom-left"
    TOP_RIGHT = "top-right"
    TOP_LEFT = "top-left"


class WidgetConfig(Base):
    __tablename__ = "widget_configs"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    bot_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("bots.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    position: Mapped[str] = mapped_column(String(20), default=WidgetPosition.BOTTOM_RIGHT)
    primary_color: Mapped[str] = mapped_column(String(7), default="#3B82F6")
    auto_open: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "bot_id": str(self.bot_id),
            "position": self.position,
            "primary_color": self.primary_color,
            "auto_open": self.auto_open,
        }
