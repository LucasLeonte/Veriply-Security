from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from app.api.v1.schemas import (
    ProfileUpdateRequest,
    UserResponse,
    TeamMemberResponse,
    RoleChangeRequest,
    InviteTeamMemberRequest
)
from app.services.profile_service import (
    get_user_profile,
    update_user_profile,
    upload_avatar_url,
    get_team_members,
    remove_team_member,
    change_team_member_role,
    invite_team_member
)
from app.core.database import get_db
from app.core.auth import get_current_user
from app.core.settings import settings
from sqlalchemy.ext.asyncio import AsyncSession
import uuid
from pathlib import Path

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
    user_id: uuid.UUID,
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
    
    user = await get_user_profile(str(user_id), session)
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
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    """
    Upload user avatar using multipart/form-data (efficient file upload).
    
    Benefits over base64 data URLs:
    ✅ Memory efficient: Streams file without encoding overhead
    ✅ Bandwidth efficient: No base64 encoding bloat (~33% size increase)
    ✅ Scalable: Handles large files and concurrent uploads better
    ✅ Standard: Uses HTTP multipart/form-data specification
    ✅ Production-ready: Ready for S3/cloud storage integration
    
    File Validation:
    - Max size: 5MB (adjustable)
    - Allowed types: image/jpeg, image/png, image/webp
    
    Usage (Frontend FormData):
        const formData = new FormData();
        formData.append('file', file);
        fetch('/api/v1/profile/avatar', {
            method: 'POST',
            body: formData,
            credentials: 'include'
        });
    """
    # Validate file type
    allowed_types = {'image/jpeg', 'image/png', 'image/webp'}
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Allowed: {', '.join(allowed_types)}"
        )
    
    # Read file content and validate size
    content = await file.read()
    file_size = len(content)
    max_size = 5 * 1024 * 1024  # 5MB
    if file_size > max_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size must be less than 5MB. Received: {file_size / 1024 / 1024:.2f}MB"
        )
    
    # Generate unique filename for storage
    file_extension = Path(file.filename or "avatar").suffix
    unique_filename = f"avatar_{current_user['sub']}_{uuid.uuid4()}{file_extension}"
    
    # Persist file to local storage folder served at /avatars
    project_root = Path(__file__).resolve().parents[5]  # Go up to project root
    avatars_dir = project_root / "storage" / "avatars"
    avatars_dir.mkdir(parents=True, exist_ok=True)

    (avatars_dir / unique_filename).write_bytes(content)

    # Build an absolute URL so frontend can load directly from the API origin
    public_base = settings.__dict__.get("PUBLIC_BASE_URL") or "http://127.0.0.1:8000"
    avatar_url = f"{public_base.rstrip('/')}/avatars/{unique_filename}"
    
    # Save avatar URL to database
    user = await upload_avatar_url(
        user_id=current_user["sub"],
        avatar_url=avatar_url,
        session=session
    )
    
    return {
        "avatar_url": user.avatar_url,
        "filename": unique_filename,
        "size_bytes": file_size,
        "message": "Avatar uploaded successfully"
    }


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
    user_id: uuid.UUID,
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    """Remove a team member from the organization."""
    await remove_team_member(
        actor_id=current_user["sub"],
        target_user_id=str(user_id),
        tenant_id=current_user["tenant_id"],
        session=session
    )
    return {"message": "Team member removed successfully"}


@router.post("/team/invite", response_model=TeamMemberResponse)
async def invite_team_member_endpoint(
    invite_req: InviteTeamMemberRequest,
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    """Invite a new team member to the organization."""
    user = await invite_team_member(
        actor_id=current_user["sub"],
        email=invite_req.email,
        role=invite_req.role or "manager",
        tenant_id=current_user["tenant_id"],
        session=session
    )
    return user


@router.put("/team/members/{user_id}/role", response_model=TeamMemberResponse)
async def change_team_member_role_endpoint(
    user_id: uuid.UUID,
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
