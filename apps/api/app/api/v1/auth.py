from fastapi import APIRouter, HTTPException, status
from app.api.v1.schemas import UserRegister, UserResponse
from app.services.user_service import register_user_and_tenant, get_user_by_email
import jwt
import os
from datetime import datetime, timedelta

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

JWT_SECRET = os.getenv("JWT_SECRET", "please-change-me")
JWT_ALGORITHM = "HS256"

@router.post("/register", response_model=dict)
async def register(req: UserRegister):
    """Register a new user and create tenant."""
    existing_user = await get_user_by_email(req.email)
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    
    result = await register_user_and_tenant(req.email, req.password, req.tenant_name)
    
    # Generate JWT token
    token_payload = {
        "sub": result["user_id"],
        "tenant_id": result["tenant_id"],
        "role": "owner",
        "exp": datetime.utcnow() + timedelta(hours=24)
    }
    token = jwt.encode(token_payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "user_id": result["user_id"],
        "tenant_id": result["tenant_id"]
    }
