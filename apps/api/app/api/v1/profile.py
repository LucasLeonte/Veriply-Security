from fastapi import APIRouter, Depends, HTTPException, status
from app.api.v1.schemas import (
    ProfileUpdateRequest,
    UserResponse,
    TeamMemberResponse,
    RoleChangeRequest,
    AuditLogResponse
)
from app.services.profile_service import (
    get_user_profile,
    update_user_profile,
    upload_avatar_url,
    get_team_members,
    remove_team_member,
    change_team_member_role
)
from app.core.database import get_db
from app.core.auth import get_current_user
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/api/v1/profile", tags=["profile"])


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    """Get current logged-in user's profile."""
    user = await get_user_profile(current_user["sub"], session)
    return user


@router.get("/{user_id}", response_model=UserResponse)
async def get_user_profile_by_id(
    user_id: str,
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    """Get user profile by ID (admin/owner only)."""
    # Authorization check: only owners and admins can view other users' profiles
    if current_user["role"] not in ["owner", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only owners and admins can view other users' profiles"
        )
    
    user = await get_user_profile(user_id, session)
    return user


@router.put("/me", response_model=UserResponse)
async def update_current_user_profile(
    update_req: ProfileUpdateRequest,
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    """Update current user's profile."""
    user = await update_user_profile(
        user_id=current_user["sub"],
        name=update_req.name,
        notification_frequency=update_req.notification_frequency,
        session=session
    )
    return user


@router.post("/avatar")
async def upload_avatar(
    avatar_url: str,
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    """Upload/set user avatar URL."""
    user = await upload_avatar_url(
        user_id=current_user["sub"],
        avatar_url=avatar_url,
        session=session
    )
    return {"avatar_url": user.avatar_url, "message": "Avatar updated successfully"}


@router.get("/team/members", response_model=list[TeamMemberResponse])
async def list_team_members(
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    """Get all team members in current user's tenant."""
    members = await get_team_members(
        tenant_id=current_user["tenant_id"],
        session=session
    )
    return members


@router.delete("/team/members/{user_id}")
async def remove_team_member_endpoint(
    user_id: str,
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    """Remove a team member from the organization."""
    await remove_team_member(
        actor_id=current_user["sub"],
        target_user_id=user_id,
        tenant_id=current_user["tenant_id"],
        session=session
    )
    return {"message": "Team member removed successfully"}


@router.put("/team/members/{user_id}/role", response_model=TeamMemberResponse)
async def change_team_member_role_endpoint(
    user_id: str,
    role_req: RoleChangeRequest,
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    """Change a team member's role."""
    user = await change_team_member_role(
        actor_id=current_user["sub"],
        target_user_id=user_id,
        new_role=role_req.role,
        tenant_id=current_user["tenant_id"],
        session=session
    )
    return user
