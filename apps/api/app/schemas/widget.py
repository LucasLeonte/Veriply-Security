from pydantic import BaseModel, Field, field_validator
from typing import Optional

ALLOWED_POSITIONS = {"bottom-right", "bottom-left", "top-right", "top-left"}


class WidgetConfigResponse(BaseModel):
    bot_id: str
    position: str = "bottom-right"
    primary_color: str = "#3B82F6"
    welcome_message: Optional[str] = None
    auto_open: bool = False


class WidgetConfigUpdate(BaseModel):
    position: Optional[str] = None
    primary_color: Optional[str] = Field(
        default=None, description="Hex color like #3B82F6"
    )
    welcome_message: Optional[str] = Field(default=None, max_length=200)
    auto_open: Optional[bool] = None

    @field_validator("position")
    @classmethod
    def validate_position(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in ALLOWED_POSITIONS:
            raise ValueError("Invalid position")
        return v

    @field_validator("primary_color")
    @classmethod
    def validate_color(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            if not isinstance(v, str) or len(v) != 7 or not v.startswith("#"):
                raise ValueError("Color must be a hex like #RRGGBB")
            # Simple hex check
            hex_part = v[1:]
            try:
                int(hex_part, 16)
            except ValueError:
                raise ValueError("Color must be a hex like #RRGGBB")
        return v
