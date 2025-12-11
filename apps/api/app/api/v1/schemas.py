from pydantic import BaseModel, EmailStr, field_validator, ConfigDict, field_serializer
from typing import Optional
from datetime import datetime
from uuid import UUID

class TenantCreate(BaseModel):
    name: str

class UserRegister(BaseModel):
    email: EmailStr
    password: str
    tenant_name: str

class UserResponse(BaseModel):
    id: str | UUID
    email: str
    tenant_id: str | UUID
    role: str
    name: Optional[str] = None
    avatar_url: Optional[str] = None
    notification_frequency: str = "weekly"
    last_active: Optional[datetime] = None
    is_active: str = "active"

    model_config = ConfigDict(from_attributes=True)

    @field_serializer('id', 'tenant_id')
    def serialize_uuid(self, value: UUID | str) -> str:
        """Convert UUID objects to strings."""
        if isinstance(value, UUID):
            return str(value)
        return value

class TenantResponse(BaseModel):
    id: str
    name: str
    plan: str

class ProfileUpdateRequest(BaseModel):
    name: Optional[str] = None
    notification_frequency: Optional[str] = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and len(v) < 2:
            raise ValueError("Name must be at least 2 characters long")
        return v

    @field_validator("notification_frequency")
    @classmethod
    def validate_frequency(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in ["daily", "weekly", "monthly"]:
            raise ValueError("Invalid notification frequency")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "name": "John Doe",
                "notification_frequency": "daily"
            }
        }

class TeamMemberResponse(BaseModel):
    id: str | UUID
    email: str
    name: Optional[str] = None
    role: str
    last_active: Optional[datetime] = None
    is_active: str

    model_config = ConfigDict(from_attributes=True)

    @field_serializer('id')
    def serialize_uuid(self, value: UUID | str) -> str:
        """Convert UUID objects to strings."""
        if isinstance(value, UUID):
            return str(value)
        return value

class RoleChangeRequest(BaseModel):
    role: str

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        if v not in ["owner", "admin", "manager", "agent", "viewer"]:
            raise ValueError("Invalid role")
        return v

    class Config:
        json_schema_extra = {
            "example": {"role": "admin"}
        }

class AuditLogResponse(BaseModel):
    id: str | UUID
    actor_id: str | UUID
    target_user_id: Optional[str | UUID] = None
    action: str
    details: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @field_serializer('id', 'actor_id', 'target_user_id')
    def serialize_uuid(self, value: UUID | str | None) -> str | None:
        """Convert UUID objects to strings."""
        if isinstance(value, UUID):
            return str(value)
        return value

