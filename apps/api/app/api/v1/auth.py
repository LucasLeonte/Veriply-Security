from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.api.v1.schemas import UserRegister
from app.services.user_service import register_user_and_tenant, get_user_by_email
from app.services.auth_service import verify_password
from app.services.email_service import EmailService
from app.core.database import get_db
from app.core.settings import settings
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.user import User
import jwt
from datetime import datetime, timedelta
from uuid import UUID
import secrets
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])
security = HTTPBearer()

JWT_ALGORITHM = "HS256"

def get_jwt_secret() -> str:
    """Get JWT secret from settings."""
    return settings.JWT_SECRET

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
        payload = jwt.decode(token, get_jwt_secret(), algorithms=[JWT_ALGORITHM])
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
    except Exception:
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
        payload = jwt.decode(token, get_jwt_secret(), algorithms=[JWT_ALGORITHM])
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
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid tenant ID format",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

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
    token = jwt.encode(token_payload, get_jwt_secret(), algorithm=JWT_ALGORITHM)
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "user_id": result["user_id"],
        "tenant_id": result["tenant_id"]
    }

@router.post("/login", response_model=dict)
async def login(req: UserRegister):
    """Login an existing user."""
    user = await get_user_by_email(req.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Verify password
    if not verify_password(req.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Generate JWT token
    token_payload = {
        "sub": str(user.id),
        "tenant_id": str(user.tenant_id),
        "role": user.role,
        "exp": datetime.utcnow() + timedelta(hours=24)
    }
    token = jwt.encode(token_payload, get_jwt_secret(), algorithm=JWT_ALGORITHM)
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "user_id": str(user.id),
        "tenant_id": str(user.tenant_id)
    }


class ForgotPasswordRequest(BaseModel):
    """Request schema for forgot password."""
    email: str


class ResetPasswordRequest(BaseModel):
    """Request schema for reset password."""
    token: str
    new_password: str


class AcceptTeamInviteRequest(BaseModel):
    """Request schema to accept a cross-tenant team invite."""
    token: str


@router.post("/forgot-password")
async def forgot_password(req: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)):
    """Request a password reset link."""
    # Find user by email
    result = await db.execute(select(User).where(User.email == req.email))
    user = result.scalar_one_or_none()
    
    if not user:
        # For security, don't reveal if email exists
        return {"message": "If an account with this email exists, a password reset link will be sent."}
    
    # Generate reset token (valid for 1 hour)
    reset_token = secrets.token_urlsafe(32)
    user.password_reset_token = reset_token
    user.password_reset_expires = datetime.utcnow() + timedelta(hours=1)
    
    await db.commit()
    
    # Send password reset email
    await EmailService.send_password_reset_email(req.email, reset_token)
    
    return {"message": "If an account with this email exists, a password reset link will be sent."}


@router.post("/reset-password")
async def reset_password(req: ResetPasswordRequest, db: AsyncSession = Depends(get_db)):
    """Reset password using a valid reset token."""
    # Find user by reset token
    result = await db.execute(
        select(User).where(User.password_reset_token == req.token)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )
    
    # Check if token is expired
    if user.password_reset_expires is None or user.password_reset_expires < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password reset token has expired. Please request a new one."
        )
    
    # Validate new password
    if len(req.new_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters"
        )
    
    # Import hash_password from auth_service
    from app.services.auth_service import hash_password
    
    # Update password and clear reset token
    user.password_hash = hash_password(req.new_password)
    user.password_reset_token = None
    user.password_reset_expires = None
    user_email = user.email  # Store email for confirmation email
    
    await db.commit()
    
    # Send confirmation email
    await EmailService.send_password_reset_confirmation(user_email)
    
    return {"message": "Password reset successfully"}


@router.post("/accept-invite")
async def accept_team_invite(req: AcceptTeamInviteRequest, db: AsyncSession = Depends(get_db)):
    """Accept a team invitation by token; transfers user to pending tenant and role."""
    # 1) Try cross-tenant invite token
    result = await db.execute(select(User).where(User.tenant_invite_token == req.token))
    user = result.scalar_one_or_none()

    if user:
        # Check expiry
        if user.tenant_invite_expires is None or user.tenant_invite_expires < datetime.utcnow():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invite token has expired. Please request a new invitation."
            )

        if not user.pending_tenant_id or not user.pending_role:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invite is not properly configured."
            )

        # Transfer user to new tenant
        user.tenant_id = user.pending_tenant_id
        user.role = user.pending_role
        user.is_active = True
        user.tenant_invite_token = None
        user.tenant_invite_expires = None
        user.pending_tenant_id = None
        user.pending_role = None

        # Clear invite token after acceptance; no additional password setup step
        user.password_reset_token = None
        user.password_reset_expires = None

        await db.commit()

        return {"message": "Invitation accepted."}

    # 2) Fallback: intra-tenant invite uses password_reset_token
    result = await db.execute(select(User).where(User.password_reset_token == req.token))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired invite token"
        )

    # Check expiry
    if user.password_reset_expires is None or user.password_reset_expires < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invite token has expired. Please request a new invitation."
        )

    # Activate user in the same tenant
    user.is_active = True

    # Clear invite token after acceptance; no additional password setup step
    user.password_reset_token = None
    user.password_reset_expires = None

    await db.commit()

    return {"message": "Invitation accepted."}


@router.post("/accept-group-invite")
async def accept_group_invite(req: AcceptTeamInviteRequest, db: AsyncSession = Depends(get_db)):
    """Accept a group invitation by verified token; adds user to group with specified role."""
    # Import here to avoid circular imports
    from app.models import GroupMember, GroupRole, Group
    from app.services.group_service import GroupService

    try:
        # Decode the signed JWT token
        payload = jwt.decode(req.token, get_jwt_secret(), algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invite token has expired. Please request a new invitation."
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid invite token."
        )

    # Extract token data
    group_id = UUID(payload["group_id"])
    user_id = UUID(payload["user_id"])
    invited_by_id = UUID(payload["invited_by_id"])
    role_str = payload["role"]
    role = GroupRole(role_str)

    # Check if group exists
    group = await db.scalar(select(Group).where(Group.id == group_id))
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found."
        )

    # Check if user exists
    user = await db.scalar(select(User).where(User.id == user_id))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found."
        )

    # Add user to group
    try:
        member = await GroupService.add_member(
            db=db,
            group_id=group_id,
            user_id=user_id,
            role=role,
            invited_by_id=invited_by_id,
        )
        await db.commit()
        logger.info(
            f"User {user_id} accepted group invite to group {group_id} with role {role.value}"
        )
        return {"message": "Successfully joined the group."}
    except ValueError as e:
        await db.rollback()
        logger.error(f"Error adding member to group: {str(e)}")
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        await db.rollback()
        logger.exception(f"Unexpected error in accept_group_invite: {e}")
        raise HTTPException(status_code=500, detail="Failed to accept group invite")
