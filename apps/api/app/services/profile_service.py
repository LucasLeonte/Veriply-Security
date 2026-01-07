import uuid
import json
import secrets
import logging
from datetime import datetime, timedelta
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.models.group import Group
from app.models.group_member import GroupMember, GroupRole
from app.models.audit_log import AuditLog
from app.services.email_service import EmailService
from app.services.auth_service import hash_password
from fastapi import HTTPException, status

logger = logging.getLogger(__name__)


async def get_user_profile(user_id: str, session: AsyncSession) -> User:
    """Get user profile by ID."""
    try:
        user_uuid = uuid.UUID(user_id)
    except (ValueError, TypeError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid user ID format: {str(e)}"
        )
    
    stmt = select(User).where(User.id == user_uuid)
    result = await session.execute(stmt)
    user = result.scalars().first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user


async def update_user_profile(
    user_id: str,
    name: str | None = None,
    notification_frequency: str | None = None,
    session: AsyncSession = None
) -> User:
    """Update user profile (name, notification preferences)."""
    user = await get_user_profile(user_id, session)
    
    # Validate name length
    if name is not None:
        if len(name) < 2 or len(name) > 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Name must be between 2 and 100 characters"
            )
        user.name = name
    
    # Validate notification frequency
    if notification_frequency is not None:
        if notification_frequency not in ["daily", "weekly", "never"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Notification frequency must be 'daily', 'weekly', or 'never'"
            )
        user.notification_frequency = notification_frequency
    
    user.updated_at = datetime.utcnow()
    session.add(user)
    await session.commit()
    await session.refresh(user)
    
    # Log audit trail
    await log_audit_action(
        tenant_id=user.tenant_id,
        actor_id=uuid.UUID(user_id),
        target_user_id=uuid.UUID(user_id),
        action="profile_update",
        details=json.dumps({"name": name, "notification_frequency": notification_frequency}),
        session=session
    )
    
    return user


async def upload_avatar_url(
    user_id: str,
    avatar_url: str,
    session: AsyncSession
) -> User:
    """Update user avatar URL."""
    if not avatar_url or len(avatar_url) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Avatar URL cannot be empty"
        )
    
    user = await get_user_profile(user_id, session)
    user.avatar_url = avatar_url
    user.updated_at = datetime.utcnow()
    session.add(user)
    await session.commit()
    await session.refresh(user)
    
    await log_audit_action(
        tenant_id=user.tenant_id,
        actor_id=uuid.UUID(user_id),
        target_user_id=uuid.UUID(user_id),
        action="avatar_update",
        details=json.dumps({"avatar_url": avatar_url}),
        session=session
    )
    
    return user


async def get_team_members(tenant_id: str, session: AsyncSession) -> list[User]:
    """Get all active team members for a tenant."""
    stmt = select(User).where(
        and_(
            User.tenant_id == uuid.UUID(tenant_id),
            User.is_active.is_(True)
        )
    ).order_by(User.name)
    
    result = await session.execute(stmt)
    return result.scalars().all()


async def remove_team_member(
    actor_id: str,
    target_user_id: str,
    tenant_id: str,
    session: AsyncSession
) -> None:
    """Remove a team member (soft delete, mark as inactive)."""
    actor = await get_user_profile(actor_id, session)
    target = await get_user_profile(target_user_id, session)
    
    # Authorization: only Owner/Admin can remove
    if actor.role not in ["owner", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only Owner or Admin can remove team members"
        )
    
    # Prevent self-removal
    if actor_id == target_user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot remove yourself"
        )
    
    # Prevent removal of last owner
    owner_count = await count_owners_in_tenant(tenant_id, session)
    if target.role == "owner" and owner_count <= 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot remove the last Owner from the organization"
        )
    
    # Mark as inactive
    target.is_active = False
    target.updated_at = datetime.utcnow()
    session.add(target)
    await session.commit()
    
    await log_audit_action(
        tenant_id=uuid.UUID(tenant_id),
        actor_id=uuid.UUID(actor_id),
        target_user_id=uuid.UUID(target_user_id),
        action="user_removed",
        details=json.dumps({"removed_user_email": target.email, "removed_user_role": target.role}),
        session=session
    )


async def change_team_member_role(
    actor_id: str,
    target_user_id: str,
    new_role: str,
    tenant_id: str,
    session: AsyncSession
) -> User:
    """Change a team member's role."""
    actor = await get_user_profile(actor_id, session)
    target = await get_user_profile(target_user_id, session)
    
    # Authorization: only Owner can change roles
    if actor.role != "owner":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only Owner can change team member roles"
        )
    
    # Validate new role
    valid_roles = ["owner", "admin", "manager", "agent", "viewer"]
    if new_role not in valid_roles:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Role must be one of: {', '.join(valid_roles)}"
        )
    
    # Prevent role change of last owner
    if target.role == "owner" and new_role != "owner":
        owner_count = await count_owners_in_tenant(tenant_id, session)
        if owner_count <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot change role of the last Owner"
            )
    
    old_role = target.role
    target.role = new_role
    target.updated_at = datetime.utcnow()
    session.add(target)
    await session.commit()
    await session.refresh(target)
    
    await log_audit_action(
        tenant_id=uuid.UUID(tenant_id),
        actor_id=uuid.UUID(actor_id),
        target_user_id=uuid.UUID(target_user_id),
        action="role_change",
        details=json.dumps({"old_role": old_role, "new_role": new_role}),
        session=session
    )
    
    return target


async def count_owners_in_tenant(tenant_id: str, session: AsyncSession) -> int:
    """Count active owner-role users in a tenant."""
    stmt = select(User).where(
        and_(
            User.tenant_id == uuid.UUID(tenant_id),
            User.role == "owner",
            User.is_active.is_(True)
        )
    )
    result = await session.execute(stmt)
    return len(result.scalars().all())


async def invite_team_member(
    actor_id: str,
    email: str,
    role: str,
    tenant_id: str,
    session: AsyncSession
) -> User:
    """
    Invite a new team member via email.
    
    Creates or updates a user with the given email in the tenant.
    Authorization: only Owner/Admin can invite
    """
    actor = await get_user_profile(actor_id, session)
    
    # Authorization: only Owner/Admin can invite
    if actor.role not in ["owner", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only Owner or Admin can invite team members"
        )
    
    # Validate email format
    if not email or "@" not in email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid email address"
        )
    
    # Validate role
    valid_roles = ["owner", "admin", "manager", "agent", "viewer"]
    if role not in valid_roles:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Role must be one of: {', '.join(valid_roles)}"
        )
    
    # Role-based authorization: only owners can create other owners
    if role == "owner" and actor.role != "owner":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only owners can invite other owners"
        )
    
    # Check if user with this email already exists in this tenant
    stmt = select(User).where(
        and_(
            User.email == email,
            User.tenant_id == uuid.UUID(tenant_id)
        )
    )
    result = await session.execute(stmt)
    existing_user = result.scalars().first()
    
    if existing_user:
        # User already exists in this tenant
        if existing_user.is_active == False:
            # Generate new token for reinvitation
            reset_token = secrets.token_urlsafe(32)
            existing_user.role = role
            existing_user.password_reset_token = reset_token
            existing_user.password_reset_expires = datetime.utcnow() + timedelta(hours=48)
            existing_user.updated_at = datetime.utcnow()
            session.add(existing_user)
            await session.commit()
            await session.refresh(existing_user)
            
            # Send team invite email with new token
            try:
                await EmailService.send_team_invite_email(email, reset_token)
            except Exception:
                pass
            
            await log_audit_action(
                tenant_id=uuid.UUID(tenant_id),
                actor_id=uuid.UUID(actor_id),
                target_user_id=existing_user.id,
                action="team_member_reinvited",
                details=json.dumps({"email": email, "role": role}),
                session=session
            )
            return existing_user
        else:
            # User is already active in this tenant
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"User with email {email} is already a member of this group"
            )

    # Check if user exists globally (any tenant)
    other_stmt = select(User).where(User.email == email)
    other_result = await session.execute(other_stmt)
    existing_user_global = other_result.scalars().first()
    
    if not existing_user_global:
        # User doesn't exist anywhere - they need to sign up first
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with email {email} not found. They must sign up first."
        )
    
    # User exists in another tenant - add them via GroupMember (cross-tenant membership)
    # Find or create the default group for this tenant
    tenant_uuid = uuid.UUID(tenant_id)
    group_stmt = select(Group).where(Group.tenant_id == tenant_uuid)
    group_result = await session.execute(group_stmt)
    tenant_group = group_result.scalars().first()
    
    if not tenant_group:
        # Create default group for this tenant
        tenant_group = Group(
            id=uuid.uuid4(),
            tenant_id=tenant_uuid,
            name="Main Group",
            description="Default group for organization members",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        session.add(tenant_group)
        await session.flush()  # Get the group ID
    
    # Check if already a member of this tenant's group
    member_check = await session.execute(
        select(GroupMember).where(
            and_(
                GroupMember.group_id == tenant_group.id,
                GroupMember.user_id == existing_user_global.id
            )
        )
    )
    if member_check.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"User is already a member of this group"
        )
    
    # Add user to tenant's group via GroupMember
    role_enum = GroupRole[role.upper()] if hasattr(GroupRole, role.upper()) else GroupRole.VIEWER
    new_member = GroupMember(
        id=uuid.uuid4(),
        group_id=tenant_group.id,
        user_id=existing_user_global.id,
        role=role_enum,
        invited_at=datetime.utcnow(),
        invited_by_id=uuid.UUID(actor_id),
    )
    session.add(new_member)
    await session.commit()
    
    # Send notification email (not an invite token, just notification)
    try:
        await EmailService.send_team_invite_email(email, None)  # TODO: Update email template for cross-tenant
    except Exception:
        pass
    
    await log_audit_action(
        tenant_id=tenant_uuid,
        actor_id=uuid.UUID(actor_id),
        target_user_id=existing_user_global.id,
        action="team_member_added_cross_tenant",
        details=json.dumps({"email": email, "role": role}),
        session=session
    )
    
    return existing_user_global


async def log_audit_action(
    tenant_id: uuid.UUID,
    actor_id: uuid.UUID,
    action: str,
    details: str | None = None,
    target_user_id: uuid.UUID | None = None,
    session: AsyncSession = None
) -> AuditLog:
    """Log an action to the audit_logs table."""
    audit_entry = AuditLog(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        actor_id=actor_id,
        target_user_id=target_user_id,
        action=action,
        details=details,
        created_at=datetime.utcnow()
    )
    session.add(audit_entry)
    await session.commit()
    return audit_entry

async def cleanup_inactive_users(session: AsyncSession, days: int = 30) -> int:
    """
    Hard-delete users who have been inactive (is_active=False) for X days.
    
    Args:
        session: AsyncSession for database operations
        days: Number of days before soft-deleted users are permanently deleted (default 30)
    
    Returns:
        Number of users deleted
    """
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    # Find inactive users older than cutoff date
    stmt = select(User).where(
        and_(
            User.is_active.is_(False),
            User.updated_at < cutoff_date
        )
    )
    
    result = await session.execute(stmt)
    users_to_delete = result.scalars().all()
    
    # Delete them
    for user in users_to_delete:
        await session.delete(user)
    
    if users_to_delete:
        await session.commit()
        logger.info(f"Cleaned up {len(users_to_delete)} inactive users older than {days} days")
    
    return len(users_to_delete)