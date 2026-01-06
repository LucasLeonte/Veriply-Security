import uuid
import json
import secrets
from datetime import datetime, timedelta
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.models.audit_log import AuditLog
from app.services.email_service import EmailService
from app.services.auth_service import hash_password
from fastapi import HTTPException, status


async def get_user_profile(user_id: str, session: AsyncSession) -> User:
    """Get user profile by ID."""
    stmt = select(User).where(User.id == uuid.UUID(user_id))
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
            User.is_active == "active"
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
    target.is_active = "inactive"
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
            User.is_active == "active"
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
    
    # Check if user with this email already exists
    # First check in this tenant
    stmt = select(User).where(
        and_(
            User.email == email,
            User.tenant_id == uuid.UUID(tenant_id)
        )
    )
    result = await session.execute(stmt)
    existing_user = result.scalars().first()
    
    if existing_user:
        # User already exists, update their role if they're inactive
        if existing_user.is_active == "inactive":
            existing_user.is_active = "active"
            existing_user.role = role
            existing_user.updated_at = datetime.utcnow()
            session.add(existing_user)
            await session.commit()
            await session.refresh(existing_user)
            
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
            # User is already active
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"User with email {email} is already a team member"
            )

    # If user exists in another tenant, block to avoid unique email conflict
    other_stmt = select(User).where(User.email == email)
    other_result = await session.execute(other_stmt)
    other_user = other_result.scalars().first()
    if other_user:
        # Send cross-tenant invite that, upon acceptance, transfers the user to this tenant
        transfer_token = secrets.token_urlsafe(32)
        other_user.tenant_invite_token = transfer_token
        other_user.tenant_invite_expires = datetime.utcnow() + timedelta(hours=48)
        other_user.pending_tenant_id = uuid.UUID(tenant_id)
        other_user.pending_role = role
        other_user.updated_at = datetime.utcnow()
        session.add(other_user)
        await session.commit()
        await session.refresh(other_user)

        # Send invite email
        try:
            await EmailService.send_team_invite_email(email, transfer_token)
        except Exception:
            pass

        await log_audit_action(
            tenant_id=uuid.UUID(tenant_id),
            actor_id=uuid.UUID(actor_id),
            target_user_id=other_user.id,
            action="cross_tenant_invite_sent",
            details=json.dumps({"email": email, "role": role}),
            session=session
        )
        return other_user
    
    # Create new user with invited role
    # Generate a secure temporary password to satisfy NOT NULL constraint
    temp_password = secrets.token_urlsafe(24)
    reset_token = secrets.token_urlsafe(32)

    new_user = User(
        id=uuid.uuid4(),
        email=email,
        tenant_id=uuid.UUID(tenant_id),
        role=role,
        is_active="active",
        password_hash=hash_password(temp_password),
        password_reset_token=reset_token,
        password_reset_expires=datetime.utcnow() + timedelta(hours=48),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    session.add(new_user)
    await session.commit()
    await session.refresh(new_user)

    # Send initial password set email
    try:
        await EmailService.send_password_reset_email(email, reset_token)
    except Exception:
        pass
    
    # Log invitation
    await log_audit_action(
        tenant_id=uuid.UUID(tenant_id),
        actor_id=uuid.UUID(actor_id),
        target_user_id=new_user.id,
        action="team_member_invited",
        details=json.dumps({"email": email, "role": role}),
        session=session
    )
    
    return new_user


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
