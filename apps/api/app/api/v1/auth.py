from fastapi import APIRouter, HTTPException, status, Depends, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.api.v1.schemas import UserRegister, UserResponse
from app.services.user_service import register_user_and_tenant, get_user_by_email
from app.core.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.user import User
import jwt
import os
from datetime import datetime, timedelta
from uuid import UUID

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])
security = HTTPBearer()


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

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Dependency to extract and validate JWT token and return current user.
    Extracts token from Authorization: Bearer <token> header.
    """
    token = credentials.credentials
    
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Fetch user from database
    result = await db.execute(select(User).where(User.id == UUID(user_id)))
    user = result.scalar_one_or_none()
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user

async def get_current_tenant(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> UUID:
    """
    Dependency to extract tenant_id from JWT token.
    """
    token = credentials.credentials
    
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        tenant_id: str = payload.get("tenant_id")
        if tenant_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Tenant ID not found in token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return UUID(tenant_id)
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid tenant ID format",
            headers={"WWW-Authenticate": "Bearer"},
        )

@router.post("/register", response_model=dict)
async def register(req: UserRegister):
    """
    Register a new user and create tenant.
    Sets secure httpOnly cookie with JWT token to prevent XSS attacks.
    """
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
    
    # Create response with secure httpOnly cookie
    response = JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content={
            "message": "Registration successful",
            "user_id": result["user_id"],
            "tenant_id": result["tenant_id"]
        }
    )
    
    # Set secure httpOnly cookie (prevents JavaScript access, mitigates XSS)
    response.set_cookie(
        key="access_token",
        value=token,
        max_age=86400,  # 24 hours
        secure=True,  # HTTPS only in production
        httponly=True,  # Not accessible to JavaScript
        samesite="lax",  # CSRF protection
        path="/"
    )
    
    return response


@router.post("/logout")
async def logout():
    """
    Logout user by clearing the secure httpOnly cookie.
    """
    response = JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"message": "Logged out successfully"}
    )
    
    # Clear the secure httpOnly cookie
    response.delete_cookie(
        key="access_token",
        path="/",
        domain=None,
        secure=True,
        httponly=True,
        samesite="lax"
    )
    
    return response
