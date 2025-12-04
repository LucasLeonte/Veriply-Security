from fastapi import APIRouter, HTTPException, status
from app.api.v1.schemas import UserRegister, UserResponse
from app.services.user_service import register_user_and_tenant, get_user_by_email
import jwt
import os
from datetime import datetime, timedelta

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


def _get_jwt_secret() -> str:
    """
    Get JWT secret from environment variable.
    CRITICAL: Fail fast if not configured to prevent security vulnerabilities.
    """
    secret = os.getenv("JWT_SECRET")
    if not secret:
        raise RuntimeError(
            "CRITICAL SECURITY ERROR: JWT_SECRET environment variable is not set. "
            "This is required for production security. "
            "Set JWT_SECRET to a strong, random value (minimum 32 characters). "
            "Example: export JWT_SECRET=$(python -c 'import secrets; print(secrets.token_urlsafe(32))')"
        )
    
    # Warn if using default/weak secret (but allow for development only with strict conditions)
    if len(secret) < 32:
        raise RuntimeError(
            f"CRITICAL SECURITY ERROR: JWT_SECRET is too short (length: {len(secret)}). "
            "Minimum required length is 32 characters. "
            "A weak secret exposes the application to token forgery attacks. "
            "Use a cryptographically secure random secret."
        )
    
    return secret


JWT_SECRET = _get_jwt_secret()
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
