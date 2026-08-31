import jwt
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer
from app.core.security_logger import SecurityEvent, log_security_event, extract_request_context

# Cache for JWT secret
_jwt_secret_cache = None


def get_jwt_secret() -> str:
    """
    Get JWT secret from settings module (lazy-loaded).
    CRITICAL: Fail fast if not configured to prevent security vulnerabilities.
    """
    global _jwt_secret_cache

    if _jwt_secret_cache is not None:
        return _jwt_secret_cache

    # Import here to avoid circular imports at module load time
    from app.core.settings import settings

    secret_val = settings.JWT_SECRET
    if not secret_val:
        raise RuntimeError(
            "CRITICAL SECURITY ERROR: JWT_SECRET not configured in .env file. "
            "This is required for production security. "
            "Run `python scripts/secrets.py generate` to create one."
        )

    # Unwrap SecretValue to get the raw string for PyJWT
    secret = secret_val.get_secret_value()

    if len(secret) < 32:
        raise RuntimeError(
            f"CRITICAL SECURITY ERROR: JWT_SECRET is too short (length: {len(secret)}). "
            "Minimum required length is 32 characters. "
            "A weak secret exposes the application to token forgery attacks. "
            "Use a cryptographically secure random secret."
        )

    _jwt_secret_cache = secret
    return _jwt_secret_cache



JWT_ALGORITHM = "HS256"

security = HTTPBearer(auto_error=False)


def decode_jwt(token: str) -> dict | None:
    """
    Decode JWT token without raising exceptions.
    Returns payload dict if valid, None if invalid/expired.
    Used for optional authentication checks.
    """
    try:
        payload = jwt.decode(
            token,
            get_jwt_secret(),
            algorithms=[JWT_ALGORITHM],
            options={"require": ["exp", "sub"], "verify_exp": True, "verify_signature": True},
        )
        return payload
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None


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
    ctx = extract_request_context(request)

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
        payload = jwt.decode(
            token,
            get_jwt_secret(),
            algorithms=[JWT_ALGORITHM],
            options={"require": ["exp", "sub"], "verify_exp": True, "verify_signature": True},
        )
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
        await log_security_event(
            SecurityEvent.AUTH_TOKEN_EXPIRED,
            status=401,
            detail="JWT token has expired",
            **ctx,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired"
        )
    except jwt.InvalidTokenError:
        await log_security_event(
            SecurityEvent.AUTH_TOKEN_INVALID,
            status=401,
            detail="Invalid JWT token presented",
            **ctx,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
