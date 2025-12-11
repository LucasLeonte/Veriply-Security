"""Bots API routes for CRUD operations with group scoping."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from uuid import UUID
from datetime import datetime
import logging

from app.models import Bot, BotStatus, Group, GroupMember, GroupRole
from app.core.auth import get_current_user
from app.core.database import get_db
from app.api.v1.schemas import BotCreate, BotUpdate, BotResponse
from app.services.bot_group_service import BotGroupService
from app.services.audit_service import AuditService

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

    if required_role and member.role not in [GroupRole.GROUP_ADMIN, required_role]:
        role_names = ", ".join([r.value for r in [required_role, GroupRole.GROUP_ADMIN]])
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
            session=session,
            tenant_id=UUID(current_user["tenant_id"]),
            group_id=group_id,
            user_id=UUID(current_user["sub"]),
            name=bot_data.name,
            description=bot_data.description,
            confidence_threshold=bot_data.confidence_threshold,
        )

        # Log to audit trail
        await AuditService.log_action(
            session=session,
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
            session=session,
            bot_id=bot_id,
            group_id=group_id,
            tenant_id=UUID(current_user["tenant_id"]),
        )

        return bot
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.exception(f"Error retrieving bot: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve bot")


@router.get("", response_model=list[BotResponse])
async def list_bots(
    group_id: UUID,
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
        bots = await BotGroupService.list_group_bots(
            session=session,
            group_id=group_id,
            tenant_id=UUID(current_user["tenant_id"]),
        )

        return bots
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
            session=session,
            bot_id=bot_id,
            group_id=group_id,
            tenant_id=UUID(current_user["tenant_id"]),
            name=bot_data.name,
            description=bot_data.description,
            confidence_threshold=bot_data.confidence_threshold,
        )

        # Log to audit trail
        await AuditService.log_action(
            session=session,
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
            session=session,
            bot_id=bot_id,
            group_id=group_id,
            tenant_id=UUID(current_user["tenant_id"]),
        )

        # Log to audit trail
        await AuditService.log_action(
            session=session,
            actor_id=UUID(current_user["sub"]),
            action="bot_deleted",
            tenant_id=UUID(current_user["tenant_id"]),
            group_id=group_id,
            target_type="Bot",
            target_id=bot_id,
            details={"bot_id": str(bot_id)},
        )

        await session.commit()

    except ValueError as e:
        await session.rollback()
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        await session.rollback()
        logger.exception(f"Error deleting bot: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete bot")
