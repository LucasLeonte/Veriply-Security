"""Bots API routes for CRUD operations with group scoping."""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from uuid import UUID
import logging
from pathlib import Path
import uuid

from app.models import Group, GroupMember, GroupRole, WidgetConfig
from app.core.auth import get_current_user
from app.core.database import get_db
from app.api.v1.schemas import BotCreate, BotUpdate, BotResponse
from app.schemas.widget import WidgetConfigResponse, WidgetConfigUpdate
from app.services.bot_group_service import BotGroupService
from app.services.audit_service import AuditService
from app.services.domain_whitelist_service import validate_domain_list
from app.core.settings import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/groups/{group_id}/bots", tags=["bots"])


async def check_group_access(
    group_id: UUID,
    current_user: dict,
    session: AsyncSession,
    required_role: GroupRole | None = None,
) -> GroupMember:
    """Helper to verify group membership and optionally check role."""
    member = await session.scalar(
        select(GroupMember).where(
            (GroupMember.group_id == group_id)
            & (GroupMember.user_id == UUID(current_user["sub"]))
        )
    )
    if not member:
        raise HTTPException(status_code=403, detail="Not a member of this group")

    if required_role:
        required_value = required_role.value if isinstance(required_role, GroupRole) else required_role
        allowed_roles = {GroupRole.OWNER.value, GroupRole.ADMIN.value, required_value}
        if member.role not in allowed_roles:
            role_names = ", ".join(sorted(allowed_roles))
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires one of these roles: {role_names}",
            )

    return member


@router.post("", response_model=BotResponse, status_code=status.HTTP_201_CREATED)
async def create_bot(
    group_id: UUID,
    bot_data: BotCreate,
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    """
    Create a new bot in the group.
    
    Required permissions: group_admin or manager
    """
    try:
        # Verify group exists and user has permission
        await check_group_access(group_id, current_user, session, required_role=GroupRole.MANAGER)

        # Verify group_id in request matches URL parameter
        if UUID(bot_data.group_id) != group_id:
            raise HTTPException(
                status_code=400,
                detail="group_id in body must match URL parameter",
            )

        # Verify group exists
        group = await session.scalar(select(Group).where(Group.id == group_id))
        if not group:
            raise HTTPException(status_code=404, detail="Group not found")

        # Create bot using service
        new_bot = await BotGroupService.create_bot(
            db=session,
            tenant_id=UUID(current_user["tenant_id"]),
            group_id=group_id,
            user_id=UUID(current_user["sub"]),
            name=bot_data.name,
            description=bot_data.description,
            confidence_threshold=bot_data.confidence_threshold,
        )

        # Log to audit trail
        await AuditService.log_action(
            db=session,
            actor_id=UUID(current_user["sub"]),
            action="bot_created",
            tenant_id=UUID(current_user["tenant_id"]),
            group_id=group_id,
            target_type="Bot",
            target_id=new_bot.id,
            details={"bot_name": new_bot.name},
        )

        await session.commit()
        return new_bot

    except ValueError as e:
        await session.rollback()
        error_msg = str(e)
        if "already exists" in error_msg:
            raise HTTPException(status_code=409, detail=error_msg)
        raise HTTPException(status_code=400, detail=error_msg)
    except Exception as e:
        await session.rollback()
        logger.exception(f"Error creating bot: {e}")
        raise HTTPException(status_code=500, detail="Failed to create bot")


@router.get("/{bot_id}", response_model=BotResponse)
async def get_bot(
    group_id: UUID,
    bot_id: UUID,
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    """
    Get bot details.
    
    User must be a member of the group.
    """
    try:
        # Verify group membership
        await check_group_access(group_id, current_user, session)

        # Get bot using service
        bot = await BotGroupService.get_bot(
            db=session,
            bot_id=bot_id,
            group_id=group_id,
            tenant_id=UUID(current_user["tenant_id"]),
        )

        if bot is None:
            raise HTTPException(status_code=404, detail="Bot not found")
        
        return BotResponse.model_validate(bot)
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.exception(f"Error retrieving bot: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve bot")


@router.get("", response_model=dict)
async def list_bots(
    group_id: UUID,
    limit: int = 20,
    offset: int = 0,
    search: str | None = None,
    sort_by: str = "name",
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    """
    List all bots in the group.
    
    User must be a member of the group.
    """
    try:
        # Verify group membership
        await check_group_access(group_id, current_user, session)

        # List bots using service
        bots, total_count = await BotGroupService.list_group_bots(
            db=session,
            group_id=group_id,
            tenant_id=UUID(current_user["tenant_id"]),
            limit=limit,
            offset=offset,
        )

        # Convert to response format
        bot_responses = [
            BotResponse.model_validate(bot) for bot in bots
        ]

        return {
            "bots": bot_responses,
            "total_count": total_count,
            "limit": limit,
            "offset": offset,
        }
    except Exception as e:
        logger.exception(f"Error listing bots: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve bots")


@router.patch("/{bot_id}", response_model=BotResponse)
async def update_bot(
    group_id: UUID,
    bot_id: UUID,
    bot_data: BotUpdate,
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    """
    Update bot details.
    
    Required permissions: group_admin or manager
    """
    try:
        # Verify group membership and role
        await check_group_access(group_id, current_user, session, required_role=GroupRole.MANAGER)

        # Update bot using service
        bot = await BotGroupService.update_bot(
            db=session,
            bot_id=bot_id,
            group_id=group_id,
            tenant_id=UUID(current_user["tenant_id"]),
            name=bot_data.name,
            description=bot_data.description,
            confidence_threshold=bot_data.confidence_threshold,
            avatar_url=bot_data.avatar_url,
            welcome_message=bot_data.welcome_message,
            is_public=bot_data.is_public,
            is_active=bot_data.is_active,
        )

        # Log to audit trail
        await AuditService.log_action(
            db=session,
            actor_id=UUID(current_user["sub"]),
            action="bot_updated",
            tenant_id=UUID(current_user["tenant_id"]),
            group_id=group_id,
            target_type="Bot",
            target_id=bot_id,
            details={"bot_id": str(bot_id), "updated_fields": ["name", "description", "threshold"]},
        )

        await session.commit()
        return bot

    except ValueError as e:
        await session.rollback()
        error_msg = str(e)
        if "not found" in error_msg:
            raise HTTPException(status_code=404, detail=error_msg)
        elif "already exists" in error_msg:
            raise HTTPException(status_code=409, detail=error_msg)
        raise HTTPException(status_code=400, detail=error_msg)
    except Exception as e:
        await session.rollback()
        logger.exception(f"Error updating bot: {e}")
        raise HTTPException(status_code=500, detail="Failed to update bot")


@router.post("/{bot_id}/avatar")
async def upload_bot_avatar(
    group_id: UUID,
    bot_id: UUID,
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    """
    Upload or replace a bot's avatar image.

    - Allowed types: image/jpeg, image/png, image/webp
    - Max size: 5MB
    - Stores file under storage/avatars and exposes at /avatars/*
    - Updates bot.avatar_url

    Required permissions: group_admin or manager
    """
    # Verify permissions
    await check_group_access(group_id, current_user, session, required_role=GroupRole.MANAGER)

    # Validate file type
    allowed_types = {"image/jpeg", "image/png", "image/webp"}
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Allowed: {', '.join(allowed_types)}",
        )

    # Read and validate size
    content = await file.read()
    size_bytes = len(content)
    max_size = 5 * 1024 * 1024
    if size_bytes > max_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File too large. Max 5MB",
        )

    # Generate unique filename and persist under storage/avatars
    file_extension = Path(file.filename or "avatar").suffix
    unique_filename = f"bot_{bot_id}_{uuid.uuid4()}{file_extension}"

    project_root = Path(__file__).resolve().parents[5]
    avatars_dir = project_root / "storage" / "avatars"
    avatars_dir.mkdir(parents=True, exist_ok=True)
    (avatars_dir / unique_filename).write_bytes(content)

    # Build public URL using mounted /avatars
    public_base = getattr(settings, "PUBLIC_BASE_URL", None) or "http://127.0.0.1:8000"
    avatar_url = f"{public_base.rstrip('/')}/avatars/{unique_filename}"

    # Update bot record
    try:
        bot = await BotGroupService.update_bot(
            db=session,
            bot_id=bot_id,
            group_id=group_id,
            tenant_id=UUID(current_user["tenant_id"]),
            avatar_url=avatar_url,
        )

        await AuditService.log_action(
            db=session,
            actor_id=UUID(current_user["sub"]),
            action="bot_avatar_updated",
            tenant_id=UUID(current_user["tenant_id"]),
            group_id=group_id,
            target_type="Bot",
            target_id=bot_id,
            details={"avatar_url": avatar_url},
        )

        await session.commit()
        return {"avatar_url": bot.avatar_url, "size_bytes": size_bytes}

    except Exception as e:
        await session.rollback()
        logger.exception(f"Error uploading bot avatar: {e}")
        raise HTTPException(status_code=500, detail="Failed to upload avatar")


@router.delete("/{bot_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_bot(
    group_id: UUID,
    bot_id: UUID,
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    """
    Delete a bot from the group.
    
    This does NOT delete the group's KB (documents/chunks remain for audit).
    
    Required permissions: group_admin or manager
    """
    try:
        # Verify group membership and role
        await check_group_access(group_id, current_user, session, required_role=GroupRole.MANAGER)

        # Delete bot using service
        await BotGroupService.delete_bot(
            db=session,
            bot_id=bot_id,
            group_id=group_id,
            tenant_id=UUID(current_user["tenant_id"]),
        )

        # Log to audit trail
        await AuditService.log_action(
            db=session,
            actor_id=UUID(current_user["sub"]),
            action="bot_deleted",
            tenant_id=UUID(current_user["tenant_id"]),
            group_id=group_id,
            target_type="Bot",
            target_id=bot_id,
            details={"bot_id": str(bot_id)},
        )

        await session.commit()
        return None

    except ValueError as e:
        await session.rollback()
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        await session.rollback()
        logger.exception(f"Error deleting bot: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete bot")



@router.get("/{bot_id}/widget/config", response_model=WidgetConfigResponse)
async def get_widget_config(
    group_id: UUID,
    bot_id: UUID,
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    """Get widget config for a bot (owner/manager)."""
    await check_group_access(group_id, current_user, session)

    from sqlalchemy import select

    result = await session.execute(select(WidgetConfig).where(WidgetConfig.bot_id == bot_id))
    cfg = result.scalar_one_or_none()

    if cfg is None:
        # Default values
        return WidgetConfigResponse(
            bot_id=str(bot_id),
            position="bottom-right",
            primary_color="#3B82F6",
            welcome_message=None,
            auto_open=False,
            allowed_domains=[],
        )

    return WidgetConfigResponse(**cfg.to_dict())


@router.put("/{bot_id}/widget/config", response_model=WidgetConfigResponse)
async def update_widget_config(
    group_id: UUID,
    bot_id: UUID,
    payload: WidgetConfigUpdate,
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    """Update widget settings (requires manager or admin)."""
    await check_group_access(group_id, current_user, session, required_role=GroupRole.MANAGER)

    result = await session.execute(select(WidgetConfig).where(WidgetConfig.bot_id == bot_id))
    cfg = result.scalar_one_or_none()

    allowed_domains: list[str] = []
    if payload.allowed_domains is not None:
        allowed_domains = validate_domain_list(payload.allowed_domains)

    if cfg is None:
        cfg = WidgetConfig(
            bot_id=bot_id,
            position=payload.position or "bottom-right",
            primary_color=payload.primary_color or "#3B82F6",
            auto_open=bool(payload.auto_open) if payload.auto_open is not None else False,
            allowed_domains=allowed_domains,
        )
        session.add(cfg)
    else:
        if payload.position is not None:
            cfg.position = payload.position
        if payload.primary_color is not None:
            cfg.primary_color = payload.primary_color
        if payload.auto_open is not None:
            cfg.auto_open = payload.auto_open
        if payload.allowed_domains is not None:
            cfg.allowed_domains = allowed_domains

    await session.commit()
    await session.refresh(cfg)
    return WidgetConfigResponse(**cfg.to_dict())
