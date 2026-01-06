import re
from typing import Optional
from urllib.parse import urlparse

from pydantic import BaseModel, Field, field_validator

ALLOWED_POSITIONS = {"bottom-right", "bottom-left", "top-right", "top-left"}
DOMAIN_REGEX = re.compile(r"^(\*\.)?[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$")
LOCALHOST_REGEX = re.compile(r"^(localhost|127\.0\.0\.1)$")
MAX_DOMAINS = 50


class WidgetConfigResponse(BaseModel):
    bot_id: str
    position: str = "bottom-right"
    primary_color: str = "#3B82F6"
    auto_open: bool = False
    allowed_domains: list[str] = Field(default_factory=list)


class WidgetConfigUpdate(BaseModel):
    position: Optional[str] = None
    primary_color: Optional[str] = Field(
        default=None, description="Hex color like #3B82F6"
    )
    auto_open: Optional[bool] = None
    allowed_domains: Optional[list[str]] = Field(default=None, description="List of allowed domains for widget embedding")

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

    @field_validator("allowed_domains")
    @classmethod
    def validate_allowed_domains(cls, v: Optional[list[str]]) -> Optional[list[str]]:
        if v is None:
            return v

        if not isinstance(v, list):
            raise ValueError("allowed_domains must be a list")
        if len(v) > MAX_DOMAINS:
            raise ValueError(f"Maximum {MAX_DOMAINS} domains allowed")

        normalized: list[str] = []
        seen: set[str] = set()

        for raw in v:
            if not isinstance(raw, str):
                raise ValueError("Domain must be a string")

            candidate = raw.strip().lower()
            if candidate.startswith("http://") or candidate.startswith("https://"):
                parsed = urlparse(candidate)
                candidate = parsed.netloc.lower()
            candidate = candidate.rstrip("/")

            # Remove port if present
            if ":" in candidate:
                candidate = candidate.split(":", 1)[0]

            if not candidate:
                raise ValueError("Invalid domain format")

            if not DOMAIN_REGEX.match(candidate) and not LOCALHOST_REGEX.match(candidate):
                raise ValueError("Invalid domain format")

            if candidate in seen:
                raise ValueError("Domain already in whitelist")

            seen.add(candidate)
            normalized.append(candidate)

        return normalized
