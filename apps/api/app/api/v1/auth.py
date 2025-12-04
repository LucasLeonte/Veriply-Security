from fastapi import APIRouter, HTTPException, status, Depends
from app.api.v1.schemas import UserRegister, UserResponse
from app.services.user_service import register_user_and_tenant, get_user_by_email
from app.core.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
import jwt
import os
from datetime import datetime, timedelta
from uuid import UUID

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

JWT_SECRET = os.getenv("JWT_SECRET", "please-change-me")
JWT_ALGORITHM = "HS256"

async def get_current_user(
    token: str | None = None,
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Dependency to extract and validate JWT token and return current user.
    For now, returns a mock user. Will be implemented with proper JWT validation.
    """
    # TODO: Implement full JWT validation with token from Authorization header
    # For now, this is a placeholder
    raise HTTPException(status_code=401, detail="Not implemented yet")

async def get_current_tenant() -> UUID:
    """
    Dependency to extract tenant_id from current user context.
    """
    # TODO: Extract from JWT token or session
    raise HTTPException(status_code=401, detail="Not implemented yet")

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
