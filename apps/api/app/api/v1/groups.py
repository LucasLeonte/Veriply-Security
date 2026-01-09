"""Groups API routes for CRUD operations and membership management."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from uuid import UUID
import logging
import jwt
from datetime import datetime, timedelta

from app.models import GroupMember, GroupRole, User, Tenant
from app.core.auth import get_current_user
from app.core.database import get_db, set_tenant_context
from app.core.settings import settings
from app.services.email_service import EmailService
from app.api.v1.schemas import (
    GroupCreate,
    GroupUpdate,
    GroupResponse,
    GroupMemberInvite,
    GroupMemberResponse,
    GroupMemberInviteResponse,
)
from app.services.group_service import GroupService
from app.services.audit_service import AuditService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/groups", tags=["groups"])


@router.post("", response_model=GroupResponse, status_code=status.HTTP_201_CREATED)
async def create_group(
    group_data: GroupCreate,
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    """
    Create a new group within the current tenant.
    
    The creator becomes the group_admin by default.
    
    Required permissions: Any authenticated user (tenant member)
    """
    # DEBUG: Log request entry
    logger.info("=" * 80)
    logger.info("CREATE GROUP REQUEST RECEIVED")
    logger.info(f"current_user dict: {current_user}")
    logger.info(f"group_data: name={group_data.name}, description={group_data.description}")
    logger.info("=" * 80)
    
    try:
        # Verify tenant exists and user belongs to it
        logger.info(f"Converting tenant_id: {current_user.get('tenant_id')} (type: {type(current_user.get('tenant_id'))})")
        logger.info(f"Converting user_id: {current_user.get('sub')} (type: {type(current_user.get('sub'))})")
        
        tenant_id = UUID(current_user["tenant_id"])
        user_id = UUID(current_user["sub"])
        
        logger.info(f"UUID conversion successful: tenant_id={tenant_id}, user_id={user_id}")
        
        tenant = await session.scalar(
            select(Tenant).where(Tenant.id == tenant_id)
        )
        logger.info(f"Tenant lookup result: {tenant}")
        
        if not tenant:
            logger.error(f"Tenant not found for tenant_id={tenant_id}")
            raise HTTPException(status_code=403, detail="Tenant not found")

        # Create the group using GroupService
        logger.info(f"Calling GroupService.create_group with tenant_id={tenant_id}, user_id={user_id}, name={group_data.name}")
        new_group = await GroupService.create_group(
            db=session,
            tenant_id=tenant_id,
            user_id=user_id,
            name=group_data.name,
            description=group_data.description,
        )
        logger.info(f"Group created successfully: id={new_group.id}, name={new_group.name}")

        # Log to audit trail
        logger.info(f"Logging to audit trail: group_id={new_group.id}")
        await AuditService.log_group_created(
            db=session,
            actor_id=user_id,
            tenant_id=tenant_id,
            group_id=new_group.id,
            group_name=new_group.name,
        )

        logger.info("Committing transaction...")
        await session.commit()
        logger.info(f"Group creation complete: {new_group.id}")
        return new_group

    except ValueError as e:
        await session.rollback()
        error_msg = str(e)
        logger.error(f"ValueError creating group: {error_msg}")
        if "already exists" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=error_msg,
            )
        raise HTTPException(status_code=400, detail=error_msg)
    except HTTPException:
        await session.rollback()
        raise
    except Exception as e:
        await session.rollback()
        logger.exception(f"UNEXPECTED ERROR creating group - Type: {type(e).__name__}, Message: {e}")
        logger.error("Full traceback:", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to create group: {str(e)}")


@router.get("/{group_id}", response_model=GroupResponse)
async def get_group(
    group_id: UUID,
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    """
    Get group details.
    
    User must be a member of the group.
    """
    try:
        # SECURITY: Set RLS context for tenant isolation
        await set_tenant_context(session, UUID(current_user['tenant_id']))

        # Get group with RLS isolation
        group = await GroupService.get_group(
            db=session,
            group_id=group_id,
            tenant_id=UUID(current_user["tenant_id"]),
        )

        # Verify membership
        member = await session.scalar(
            select(GroupMember).where(
                (GroupMember.group_id == group_id) 
                & (GroupMember.user_id == UUID(current_user["sub"]))
            )
        )
        if not member:
            raise HTTPException(status_code=403, detail="Not a member of this group")

        return group
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.exception(f"Error retrieving group: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve group")


@router.get("", response_model=list[GroupResponse])
async def list_groups(
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    """
    List all groups the user is a member of, including their role in each group.
    """
    logger.info(f"LIST GROUPS REQUEST - user_id={current_user.get('sub')}, tenant_id={current_user.get('tenant_id')}")
    try:
        user_id = UUID(current_user["sub"])
        tenant_id = UUID(current_user["tenant_id"])
        logger.info(f"Calling GroupService.list_groups_for_user - user_id={user_id}, tenant_id={tenant_id}")
        
        groups = await GroupService.list_groups_for_user(
            db=session,
            user_id=user_id,
        )
        
        # Fetch all user's memberships for their groups at once (avoid N+1 query)
        group_ids = [group.id for group in groups]
        memberships_result = await session.execute(
            select(GroupMember.group_id, GroupMember.role).where(
                (GroupMember.group_id.in_(group_ids)) &
                (GroupMember.user_id == user_id)
            )
        )
        roles_map = {m.group_id: m.role.value for m in memberships_result}
        
        # Build response with roles from the map
        group_responses = []
        for group in groups:
            group_dict = {
                "id": str(group.id),
                "tenant_id": str(group.tenant_id),
                "name": group.name,
                "description": group.description,
                "created_by": str(group.created_by),
                "created_at": group.created_at,
                "current_user_role": roles_map.get(group.id)
            }
            group_responses.append(group_dict)
        
        logger.info(f"Successfully retrieved {len(group_responses)} groups for user")
        return group_responses
    except Exception as e:
        logger.exception(f"Error listing groups: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve groups")


@router.patch("/{group_id}", response_model=GroupResponse)
async def update_group(
    group_id: UUID,
    group_data: GroupUpdate,
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    """
    Update group details.
    
    Required permissions: owner or admin
    """
    try:
        # SECURITY: Set RLS context for tenant isolation
        await set_tenant_context(session, UUID(current_user['tenant_id']))

        # Verify current user is owner/admin
        member = await session.scalar(
            select(GroupMember).where(
                (GroupMember.group_id == group_id)
                & (GroupMember.user_id == UUID(current_user["sub"]))
            )
        )
        if not member or member.role not in [GroupRole.OWNER.value, GroupRole.ADMIN.value]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only group owners or admins can update group settings",
            )

        # Update group
        group = await GroupService.update_group(
            db=session,
            group_id=group_id,
            tenant_id=UUID(current_user["tenant_id"]),
            name=group_data.name,
            description=group_data.description,
        )

        await session.commit()
        return group

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
        logger.exception(f"Error updating group: {e}")
        raise HTTPException(status_code=500, detail="Failed to update group")


@router.delete("/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_group(
    group_id: UUID,
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    """
    Delete a group and all associated members.
    
    This does NOT delete documents or chunks (KB preserved for audit).
    
    Required permissions: owner or admin
    """
    try:
        # SECURITY: Set RLS context for tenant isolation
        await set_tenant_context(session, UUID(current_user['tenant_id']))

        # Verify group exists and user is owner/admin
        member = await session.scalar(
            select(GroupMember).where(
                (GroupMember.group_id == group_id)
                & (GroupMember.user_id == UUID(current_user["sub"]))
            )
        )
        if not member or member.role not in [GroupRole.OWNER.value, GroupRole.ADMIN.value]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only group owners or admins can delete groups",
            )

        # Delete group
        await GroupService.delete_group(
            db=session,
            group_id=group_id,
            tenant_id=UUID(current_user["tenant_id"]),
        )

        # Log to audit trail
        await AuditService.log_action(
            db=session,
            actor_id=UUID(current_user["sub"]),
            action="group_deleted",
            tenant_id=UUID(current_user["tenant_id"]),
            group_id=group_id,
            target_type="Group",
            target_id=group_id,
            details={"group_id": str(group_id)},
        )

        await session.commit()

    except ValueError as e:
        await session.rollback()
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        await session.rollback()
        logger.exception(f"Error deleting group: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete group")


# Group Membership Management
@router.post(
    "/{group_id}/members",
    response_model=GroupMemberInviteResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def invite_member(
    group_id: UUID,
    invite: GroupMemberInvite,
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    """
    Invite a user to the group.
    
    Required permissions: owner or admin
    """
    try:
        # SECURITY: Set RLS context for tenant isolation
        await set_tenant_context(session, UUID(current_user['tenant_id']))

        # Verify current user is owner or admin
        member = await session.scalar(
            select(GroupMember).where(
                (GroupMember.group_id == group_id)
                & (GroupMember.user_id == UUID(current_user["sub"]))
            )
        )
        if not member or member.role not in [GroupRole.OWNER.value, GroupRole.ADMIN.value]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only owners and admins can invite members",
            )

        # Find user by email (cross-organization support)
        # Users from different organizations can be invited to groups
        user = await session.scalar(select(User).where(User.email == invite.email))
        if not user:
            raise HTTPException(
                status_code=404,
                detail="User not found. Invitations are limited to existing users.",
            )

        # Normalize role to enum for storage/validation
        try:
            GroupRole(invite.role)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid role. Must be one of: owner, admin, manager, agent, viewer",
            )

        # Do not add the user yet; membership is created when they accept the invite link
        # Prevent inviting users who are already members
        existing_member = await session.scalar(
            select(GroupMember).where(
                (GroupMember.group_id == group_id) & (GroupMember.user_id == user.id)
            )
        )
        if existing_member:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User is already a member of this group.",
            )

        # Generate signed invite token containing group_id, user_id, role, and invited_by_id
        payload = {
            "group_id": str(group_id),
            "user_id": str(user.id),
            "role": invite.role,
            "invited_by_id": str(UUID(current_user["sub"])),
            "exp": datetime.utcnow() + timedelta(hours=48),
        }
        invite_token = jwt.encode(
            payload,
            settings.JWT_SECRET,
            algorithm=settings.JWT_ALGORITHM,
        )

        # Send invite email (required)
        try:
            email_sent = await EmailService.send_group_invite_email(
                email=invite.email,
                invite_token=invite_token,
                group_id=str(group_id),
            )
            if not email_sent:
                logger.error(
                    "Group invite email did not send (EmailService returned False)",
                    extra={
                        "smtp_host": settings.SMTP_HOST,
                        "smtp_port": settings.SMTP_PORT,
                        "smtp_user": settings.SMTP_USER,
                        "email_from": settings.EMAIL_FROM or settings.SMTP_USER,
                    },
                )
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=(
                        "Failed to send invite email. Please check SMTP_HOST/SMTP_PORT/"
                        "SMTP_USER/SMTP_PASSWORD/EMAIL_FROM configuration and try again."
                    ),
                )
        except HTTPException:
            # Re-raise HTTP errors we just created
            raise
        except Exception as e:
            logger.error(
                f"Failed to send group invite email: {e}",
                exc_info=True,
                extra={
                    "smtp_host": settings.SMTP_HOST,
                    "smtp_port": settings.SMTP_PORT,
                    "smtp_user": settings.SMTP_USER,
                    "email_from": settings.EMAIL_FROM or settings.SMTP_USER,
                },
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send invite email. Check SMTP credentials and logs for details.",
            )

        # Log to audit trail
        await AuditService.log_member_invited(
            db=session,
            actor_id=UUID(current_user["sub"]),
            tenant_id=UUID(current_user["tenant_id"]),
            group_id=group_id,
            invited_user_id=user.id,
            role=invite.role,
        )

        await session.commit()

        return {
            "message": "Invite sent successfully",
            "user_id": str(user.id),
        }

    except ValueError as e:
        await session.rollback()
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        await session.rollback()
        logger.exception(f"Error inviting member: {e}")
        raise HTTPException(status_code=500, detail="Failed to invite member")


@router.get("/{group_id}/members", response_model=list[GroupMemberResponse])
async def list_group_members(
    group_id: UUID,
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    """
    List all members of a group.
    
    User must be a member of the group.
    """
    try:
        # SECURITY: Set RLS context for tenant isolation
        await set_tenant_context(session, UUID(current_user['tenant_id']))

        # Verify membership
        member = await session.scalar(
            select(GroupMember).where(
                (GroupMember.group_id == group_id)
                & (GroupMember.user_id == UUID(current_user["sub"]))
            )
        )
        if not member:
            raise HTTPException(status_code=403, detail="Not a member of this group")

        # List members
        members = await GroupService.list_group_members(
            db=session,
            group_id=group_id,
        )
        return members
    except Exception as e:
        logger.exception(f"Error listing group members: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve members")


@router.patch("/{group_id}/members/{user_id}", response_model=GroupMemberResponse)
async def update_member_role(
    group_id: UUID,
    user_id: UUID,
    new_role: dict,
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    """
    Update a member's role.
    
    Required permissions: owner or admin
    """
    try:
        # SECURITY: Set RLS context for tenant isolation
        await set_tenant_context(session, UUID(current_user['tenant_id']))

        # Verify current user is owner/admin
        admin_member = await session.scalar(
            select(GroupMember).where(
                (GroupMember.group_id == group_id)
                & (GroupMember.user_id == UUID(current_user["sub"]))
            )
        )
        if not admin_member or admin_member.role not in [GroupRole.OWNER.value, GroupRole.ADMIN.value]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only group owners or admins can change member roles",
            )

        # Owners cannot change their own role (prevent self-demotion/escalation)
        if user_id == UUID(current_user["sub"]) and admin_member.role == GroupRole.OWNER.value:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Owners cannot change their own role",
            )

        # Update member role using service
        member = await GroupService.update_member_role(
            db=session,
            group_id=group_id,
            user_id=user_id,
            new_role=new_role.get("role"),
        )

        # Log to audit trail
        await AuditService.log_action(
            db=session,
            actor_id=UUID(current_user["sub"]),
            action="member_role_updated",
            tenant_id=UUID(current_user["tenant_id"]),
            group_id=group_id,
            target_type="GroupMember",
            target_id=user_id,
            details={"new_role": new_role.get("role")},
        )

        await session.commit()
        return member

    except ValueError as e:
        await session.rollback()
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        await session.rollback()
        logger.exception(f"Error updating member role: {e}")
        raise HTTPException(status_code=500, detail="Failed to update member role")


@router.delete("/{group_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_member(
    group_id: UUID,
    user_id: UUID,
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    """
    Remove a member from the group.
    
    Required permissions: owner or admin
    """
    try:
        # SECURITY: Set RLS context for tenant isolation
        await set_tenant_context(session, UUID(current_user['tenant_id']))

        # Verify current user is owner/admin
        admin_member = await session.scalar(
            select(GroupMember).where(
                (GroupMember.group_id == group_id)
                & (GroupMember.user_id == UUID(current_user["sub"]))
            )
        )
        if not admin_member or admin_member.role not in [GroupRole.OWNER.value, GroupRole.ADMIN.value]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only group owners or admins can remove members",
            )

        # Remove member using service
        await GroupService.remove_member(
            db=session,
            group_id=group_id,
            user_id=user_id,
        )

        # Log to audit trail
        await AuditService.log_action(
            db=session,
            actor_id=UUID(current_user["sub"]),
            action="member_removed",
            tenant_id=UUID(current_user["tenant_id"]),
            group_id=group_id,
            target_type="GroupMember",
            target_id=user_id,
            details={"removed_user_id": str(user_id)},
        )

        await session.commit()

    except ValueError as e:
        await session.rollback()
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        await session.rollback()
        logger.exception(f"Error removing member: {e}")
        raise HTTPException(status_code=500, detail="Failed to remove member")
