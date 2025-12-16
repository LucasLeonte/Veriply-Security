from pydantic import BaseModel, field_validator, ConfigDict, field_serializer
from typing import Optional
from datetime import datetime
from uuid import UUID

class TenantCreate(BaseModel):
    name: str

class UserRegister(BaseModel):
    email: str
    password: str
    tenant_name: str

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        if "@" not in v or "." not in v.split("@")[1]:
            raise ValueError("Invalid email format")
        return v

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        return v

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


# Group Schemas
class GroupCreate(BaseModel):
    name: str = field_validator("name")(lambda v: v if 2 <= len(v) <= 50 else ValueError("Name must be 2-50 characters"))
    description: Optional[str] = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not (2 <= len(v) <= 50):
            raise ValueError("Name must be 2-50 characters long")
        return v


class GroupUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not (2 <= len(v) <= 50):
            raise ValueError("Name must be 2-50 characters long")
        return v


class GroupResponse(BaseModel):
    id: str | UUID
    tenant_id: str | UUID
    name: str
    description: Optional[str] = None
    created_by: str | UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @field_serializer('id', 'tenant_id', 'created_by')
    def serialize_uuid(self, value: UUID | str) -> str:
        """Convert UUID objects to strings."""
        if isinstance(value, UUID):
            return str(value)
        return value


# GroupMember Schemas
class GroupMemberInvite(BaseModel):
    email: str  # Email string, validated by backend
    role: str

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        if "@" not in v or "." not in v.split("@")[1]:
            raise ValueError("Invalid email format")
        return v

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        if v not in ["group_admin", "manager", "operator"]:
            raise ValueError("Invalid role. Must be one of: group_admin, manager, operator")
        return v


class GroupMemberResponse(BaseModel):
    id: str | UUID
    group_id: str | UUID
    user_id: str | UUID
    role: str
    invited_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @field_serializer('id', 'group_id', 'user_id')
    def serialize_uuid(self, value: UUID | str) -> str:
        """Convert UUID objects to strings."""
        if isinstance(value, UUID):
            return str(value)
        return value


# Bot Schemas (UPDATED)
class BotCreate(BaseModel):
    group_id: str | UUID
    name: str
    description: Optional[str] = None
    confidence_threshold: int = 80

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not (2 <= len(v) <= 50):
            raise ValueError("Name must be 2-50 characters long")
        return v

    @field_validator("confidence_threshold")
    @classmethod
    def validate_threshold(cls, v: int) -> int:
        if not (0 <= v <= 100):
            raise ValueError("Confidence threshold must be between 0 and 100")
        return v


class BotUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    confidence_threshold: Optional[int] = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not (2 <= len(v) <= 50):
            raise ValueError("Name must be 2-50 characters long")
        return v

    @field_validator("confidence_threshold")
    @classmethod
    def validate_threshold(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and not (0 <= v <= 100):
            raise ValueError("Confidence threshold must be between 0 and 100")
        return v


class BotResponse(BaseModel):
    id: str | UUID
    tenant_id: str | UUID
    group_id: str | UUID
    name: str
    description: Optional[str] = None
    confidence_threshold: int
    status: str
    created_by: str | UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @field_serializer('id', 'tenant_id', 'group_id', 'created_by')
    def serialize_uuid(self, value: UUID | str) -> str:
        """Convert UUID objects to strings."""
        if isinstance(value, UUID):
            return str(value)
        return value


# Document Schemas (UPDATED)
class DocumentUpload(BaseModel):
    group_id: str | UUID
    bot_id: Optional[str | UUID] = None
    title: Optional[str] = None


class DocumentResponse(BaseModel):
    id: str | UUID
    tenant_id: str | UUID
    group_id: str | UUID
    bot_id: Optional[str | UUID] = None
    filename: str
    status: str
    uploader_id: str | UUID
    mime: Optional[str] = None
    size: Optional[int] = 0
    storage_path: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

    @field_serializer('id', 'tenant_id', 'group_id', 'bot_id', 'uploader_id')
    def serialize_uuid(self, value: UUID | str | None) -> str | None:
        """Convert UUID objects to strings."""
        if isinstance(value, UUID):
            return str(value)
        return value


# Chunk Response Schema (NEW)
class ChunkResponse(BaseModel):
    id: str | UUID
    document_id: str | UUID
    chunk_index: int
    content: str
    source_metadata: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @field_serializer('id', 'document_id')
    def serialize_uuid(self, value: UUID | str) -> str:
        """Convert UUID objects to strings."""
        if isinstance(value, UUID):
            return str(value)
        return value

