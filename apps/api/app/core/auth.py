import os
import jwt
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer


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

security = HTTPBearer(auto_error=False)


async def get_current_user(
    request: Request,
    credentials = Depends(security)
) -> dict:
    """
    Validate JWT token from secure httpOnly cookie or Bearer token.
    
    Priority order:
    1. httpOnly cookie (preferred - not accessible to JavaScript)
    2. Authorization Bearer token (fallback for testing/mobile apps)
    
    Returns user info or raises 401/403 error.
    """
    token = None
    
    # First try to get token from secure httpOnly cookie
    token = request.cookies.get("access_token")
    
    # Fallback to Bearer token if no cookie (for testing and mobile clients)
    if not token and credentials:
        token = credentials.credentials
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated. Missing credentials.",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id: str = payload.get("sub")
        tenant_id: str = payload.get("tenant_id")
        role: str = payload.get("role")
        
        if user_id is None or tenant_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token claims"
            )
        
        return {
            "sub": user_id,
            "tenant_id": tenant_id,
            "role": role
        }
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired"
        )
    except jwt.InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
