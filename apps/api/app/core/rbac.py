"""Role-Based Access Control (RBAC) utilities.

Implements a 5-tier permission system:
- Owner: Full control (tenant creation, billing, deletion)
- Admin: User management, all group operations
- Manager: Bot/document/knowledge base management
- Agent: HITL approval, conversation management
- Viewer: Read-only access
"""

from functools import wraps
from typing import Callable, List
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import GroupRole, GroupMember, User
from app.core.security_logger import SecurityEvent, log_security_event


# Role hierarchy (higher number = more permissions)
ROLE_HIERARCHY = {
    GroupRole.VIEWER: 1,
    GroupRole.AGENT: 2,
    GroupRole.MANAGER: 3,
    GroupRole.ADMIN: 4,
    GroupRole.OWNER: 5,
}


def has_permission(user_role: GroupRole, required_role: GroupRole) -> bool:
    """Check if user's role meets or exceeds required role.
    
    Args:
        user_role: The user's actual role in the group
        required_role: The minimum role required for the operation
        
    Returns:
        True if user has sufficient permissions, False otherwise
    """
    return ROLE_HIERARCHY.get(user_role, 0) >= ROLE_HIERARCHY.get(required_role, 0)


def require_role(
    required_role: GroupRole,
    group_id_param: str = "group_id",
) -> Callable:
    """Decorator to enforce RBAC on endpoint functions.
    
    Usage:
        @router.post("/groups/{group_id}/bots")
        @require_role(GroupRole.MANAGER)
        async def create_bot(group_id: UUID, current_user: User = Depends(get_current_user)):
            ...
    
    Args:
        required_role: Minimum role required to access this endpoint
        group_id_param: Name of the parameter containing the group_id (default: "group_id")
        
    Raises:
        HTTPException: 403 if user lacks required role or is not a group member
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract dependencies from kwargs
            current_user: User = kwargs.get("current_user")
            db: AsyncSession = kwargs.get("db")
            group_id = kwargs.get(group_id_param)
            
            if not current_user or not db or not group_id:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"RBAC decorator misconfigured: missing current_user, db, or {group_id_param}"
                )
            
            # Query user's role in the group
            result = await db.execute(
                select(GroupMember.role)
                .where(
                    GroupMember.group_id == group_id,
                    GroupMember.user_id == current_user.id,
                    GroupMember.is_active == True,
                )
            )
            user_role = result.scalar_one_or_none()
            
            # Check if user is a member
            if user_role is None:
                await log_security_event(
                    SecurityEvent.ACCESS_DENIED,
                    user_id=str(current_user.id) if current_user else None,
                    detail=f"Not a member of group {group_id}",
                    status=403,
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Access denied: You are not a member of this group"
                )

            # Check if user has sufficient permissions
            if not has_permission(user_role, required_role):
                await log_security_event(
                    SecurityEvent.ACCESS_DENIED,
                    user_id=str(current_user.id) if current_user else None,
                    detail=f"Group {group_id}: needs {required_role.value}, has {user_role.value}",
                    status=403,
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Access denied: {required_role.value}+ role required (you have {user_role.value})"
                )
            
            # User authorized, proceed with endpoint logic
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


async def check_group_access(
    db: AsyncSession,
    user_id: str,
    group_id: str,
    required_role: GroupRole | None = None,
) -> GroupRole:
    """Check if user has access to a group and optionally verify role.
    
    This is a helper function for cases where you need to check access
    programmatically rather than using the @require_role decorator.
    
    Args:
        db: Database session
        user_id: UUID of the user
        group_id: UUID of the group
        required_role: Optional minimum role to require
        
    Returns:
        The user's role in the group
        
    Raises:
        HTTPException: 403 if user lacks access or required role
    """
    result = await db.execute(
        select(GroupMember.role)
        .where(
            GroupMember.group_id == group_id,
            GroupMember.user_id == user_id,
            GroupMember.is_active == True,
        )
    )
    user_role = result.scalar_one_or_none()
    
    if user_role is None:
        await log_security_event(
            SecurityEvent.ACCESS_DENIED,
            user_id=str(user_id),
            detail=f"Not a member of group {group_id}",
            status=403,
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: You are not a member of this group"
        )

    if required_role and not has_permission(user_role, required_role):
        await log_security_event(
            SecurityEvent.ACCESS_DENIED,
            user_id=str(user_id),
            detail=f"Group {group_id}: needs {required_role.value}, has {user_role.value}",
            status=403,
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access denied: {required_role.value}+ role required (you have {user_role.value})"
        )
    
    return user_role


async def check_tenant_admin(db: AsyncSession, user_id: str, tenant_id: str) -> bool:
    """Check if user is an admin in ANY group within the tenant.
    
    Used for tenant-level operations (user management, billing, etc.)
    
    Args:
        db: Database session
        user_id: UUID of the user
        tenant_id: UUID of the tenant
        
    Returns:
        True if user is an Owner or Admin in any group
        
    Raises:
        HTTPException: 403 if user is not an admin
    """
    from app.models import Group
    
    result = await db.execute(
        select(GroupMember.role)
        .join(Group, GroupMember.group_id == Group.id)
        .where(
            Group.tenant_id == tenant_id,
            GroupMember.user_id == user_id,
            GroupMember.is_active == True,
            GroupMember.role.in_([GroupRole.OWNER, GroupRole.ADMIN]),
        )
        .limit(1)
    )
    admin_role = result.scalar_one_or_none()
    
    if not admin_role:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Tenant admin privileges required"
        )
    
    return True
