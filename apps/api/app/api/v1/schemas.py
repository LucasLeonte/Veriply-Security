from pydantic import BaseModel, EmailStr

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

class TenantResponse(BaseModel):
    id: str
    name: str
    plan: str
