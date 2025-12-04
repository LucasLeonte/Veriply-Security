from pydantic import BaseModel, EmailStr
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

