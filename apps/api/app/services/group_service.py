"""Group service for group-scoped operations with provenance tracking."""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete
from uuid import UUID
from datetime import datetime
import logging

from app.models import Group, GroupMember, GroupRole, Bot, Document, Chunk

logger = logging.getLogger(__name__)


class GroupService:
    """Service for group management and membership operations."""

    @staticmethod
    async def create_group(
        db: AsyncSession,
        tenant_id: UUID,
        user_id: UUID,
        name: str,
        description: str | None = None,
    ) -> Group:
        """
        Create a new group and add creator as group_admin.
        
        Args:
            db: Database session
            tenant_id: Tenant ID
            user_id: User ID (creator)
            name: Group name (unique per tenant)
            description: Optional description
            
        Returns:
            Created Group object
            
        Raises:
            ValueError: If group name already exists in tenant
        """
        # Check for duplicate name in tenant
        existing = await db.scalar(
            select(Group).where(
                (Group.tenant_id == tenant_id) & (Group.name == name)
            )
        )
        if existing:
            raise ValueError(f"Group name '{name}' already exists in this tenant")

        # Create group
        new_group = Group(
            tenant_id=tenant_id,
            name=name,
            description=description,
            created_by=user_id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(new_group)
        await db.flush()

        # Add creator as owner (highest privilege)
        member = GroupMember(
            group_id=new_group.id,
            user_id=user_id,
            role=GroupRole.OWNER.value,
            invited_by_id=user_id,
            invited_at=datetime.utcnow(),
        )
        db.add(member)
        await db.flush()

        # Safety net: ensure no stray memberships on freshly created group
        # (should be none, but protects against legacy rows or seeds)
        await db.execute(
            delete(GroupMember).where(
                (GroupMember.group_id == new_group.id)
                & (GroupMember.user_id != user_id)
            )
        )
        await db.flush()

        logger.info(f"Group created: id={new_group.id}, tenant_id={tenant_id}, name={name}")
        return new_group

    @staticmethod
    async def get_group(
        db: AsyncSession, group_id: UUID, tenant_id: UUID
    ) -> Group | None:
        """Get group with tenant isolation."""
        return await db.scalar(
            select(Group).where(
                (Group.id == group_id) & (Group.tenant_id == tenant_id)
            )
        )

    @staticmethod
    async def list_groups_for_user(
        db: AsyncSession, user_id: UUID, tenant_id: UUID
    ) -> list[Group]:
        """List all groups the user is a member of."""
        stmt = (
            select(Group)
            .join(GroupMember, Group.id == GroupMember.group_id)
            .where(
                (Group.tenant_id == tenant_id)
                & (GroupMember.user_id == user_id)
            )
            .order_by(Group.created_at.desc())
        )
        return list(await db.scalars(stmt))

    @staticmethod
    async def update_group(
        db: AsyncSession,
        group_id: UUID,
        tenant_id: UUID,
        name: str | None = None,
        description: str | None = None,
    ) -> Group:
        """Update group details."""
        group = await GroupService.get_group(db, group_id, tenant_id)
        if not group:
            raise ValueError(f"Group {group_id} not found")

        if name:
            # Check for duplicate name
            existing = await db.scalar(
                select(Group).where(
                    (Group.tenant_id == tenant_id)
                    & (Group.name == name)
                    & (Group.id != group_id)
                )
            )
            if existing:
                raise ValueError(f"Group name '{name}' already exists")
            group.name = name

        if description is not None:
            group.description = description

        group.updated_at = datetime.utcnow()
        await db.flush()
        logger.info(f"Group updated: id={group_id}, tenant_id={tenant_id}")
        return group

    @staticmethod
    async def delete_group(
        db: AsyncSession, group_id: UUID, tenant_id: UUID
    ) -> bool:
        """
        Delete a group and all members.
        Note: Documents and chunks are NOT deleted (KB preserved for audit).
        """
        group = await GroupService.get_group(db, group_id, tenant_id)
        if not group:
            raise ValueError(f"Group {group_id} not found")

        await db.delete(group)
        await db.flush()
        logger.info(f"Group deleted: id={group_id}, tenant_id={tenant_id}")
        return True

    @staticmethod
    async def add_member(
        db: AsyncSession,
        group_id: UUID,
        user_id: UUID,
        role: GroupRole,
        invited_by_id: UUID,
    ) -> GroupMember:
        """Add a member to a group."""
        # Check if already a member
        existing = await db.scalar(
            select(GroupMember).where(
                (GroupMember.group_id == group_id) & (GroupMember.user_id == user_id)
            )
        )
        if existing:
            raise ValueError("User already a member of this group")

        member = GroupMember(
            group_id=group_id,
            user_id=user_id,
            role=role,
            invited_by_id=invited_by_id,
            invited_at=datetime.utcnow(),
        )
        db.add(member)
        await db.flush()
        logger.info(f"Member added: group_id={group_id}, user_id={user_id}, role={role.value}")
        return member

    @staticmethod
    async def get_member_role(
        db: AsyncSession, group_id: UUID, user_id: UUID
    ) -> GroupRole | None:
        """Get a user's role in a group."""
        member = await db.scalar(
            select(GroupMember).where(
                (GroupMember.group_id == group_id) & (GroupMember.user_id == user_id)
            )
        )
        return member.role if member else None

    @staticmethod
    async def update_member_role(
        db: AsyncSession, group_id: UUID, user_id: UUID, new_role: GroupRole
    ) -> GroupMember:
        """Update a member's role."""
        member = await db.scalar(
            select(GroupMember).where(
                (GroupMember.group_id == group_id) & (GroupMember.user_id == user_id)
            )
        )
        if not member:
            raise ValueError("Member not found in this group")

        member.role = new_role
        await db.flush()
        logger.info(f"Member role updated: group_id={group_id}, user_id={user_id}, role={new_role.value}")
        return member

    @staticmethod
    async def remove_member(
        db: AsyncSession, group_id: UUID, user_id: UUID
    ) -> bool:
        """Remove a member from a group."""
        member = await db.scalar(
            select(GroupMember).where(
                (GroupMember.group_id == group_id) & (GroupMember.user_id == user_id)
            )
        )
        if not member:
            raise ValueError("Member not found in this group")

        await db.delete(member)
        await db.flush()
        logger.info(f"Member removed: group_id={group_id}, user_id={user_id}")
        return True

    @staticmethod
    async def list_group_members(db: AsyncSession, group_id: UUID) -> list[GroupMember]:
        """List all members of a group."""
        return list(
            await db.scalars(
                select(GroupMember)
                .where(GroupMember.group_id == group_id)
                .order_by(GroupMember.invited_at)
            )
        )

    @staticmethod
    async def get_group_kb_stats(
        db: AsyncSession, group_id: UUID, tenant_id: UUID
    ) -> dict:
        """Get knowledge base statistics for a group."""
        # Count documents
        doc_count = await db.scalar(
            select(func.count(Document.id)).where(
                (Document.group_id == group_id)
                & (Document.tenant_id == tenant_id)
                & (Document.deleted_at.is_(None))
            )
        )

        # Count chunks
        chunk_count = await db.scalar(
            select(func.count(Chunk.id)).where(
                (Chunk.group_id == group_id)
                & (Chunk.tenant_id == tenant_id)
            )
        )

        # Count bots
        bot_count = await db.scalar(
            select(func.count(Bot.id)).where(
                (Bot.group_id == group_id) & (Bot.tenant_id == tenant_id)
            )
        )

        return {
            "documents": doc_count or 0,
            "chunks": chunk_count or 0,
            "bots": bot_count or 0,
        }
