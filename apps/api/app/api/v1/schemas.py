from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional
from datetime import datetime

class TenantCreate(BaseModel):
    name: str

class UserRegister(BaseModel):
    email: EmailStr
    password: str
    tenant_name: str

class UserResponse(BaseModel):
    id: str
    email: str
    tenant_id: str
    role: str
    name: Optional[str] = None
    avatar_url: Optional[str] = None
    notification_frequency: str = "weekly"
    last_active: Optional[datetime] = None
    is_active: str = "active"

    class Config:
        from_attributes = True

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
    id: str
    email: str
    name: Optional[str] = None
    role: str
    last_active: Optional[datetime] = None
    is_active: str

    class Config:
        from_attributes = True

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
    id: str
    actor_id: str
    target_user_id: Optional[str] = None
    action: str
    details: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

