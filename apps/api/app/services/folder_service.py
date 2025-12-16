"""Folder service for group-scoped folder management."""
from typing import List, Optional
from uuid import UUID
from datetime import datetime
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.folder import Folder
from app.models.document import Document


class FolderService:
    """Service for folder CRUD operations with RLS enforcement."""

    @staticmethod
    async def create_folder(
        db: AsyncSession,
        tenant_id: UUID,
        group_id: UUID,
        name: str,
        created_by: UUID
    ) -> Folder:
        """Create a new folder in a group.
        
        Args:
            db: Database session
            tenant_id: Tenant ID (RLS)
            group_id: Group ID (RLS)
            name: Folder name (unique per group)
            created_by: User ID creating the folder
            
        Returns:
            Created folder
            
        Raises:
            ValueError: If folder name already exists in group
        """
        # Check if folder name already exists
        existing = await db.scalar(
            select(Folder).where(
                and_(
                    Folder.tenant_id == tenant_id,
                    Folder.group_id == group_id,
                    Folder.name == name,
                    Folder.deleted_at.is_(None)
                )
            )
        )
        if existing:
            raise ValueError(f"Folder '{name}' already exists in this group")

        folder = Folder(
            tenant_id=tenant_id,
            group_id=group_id,
            name=name,
            created_by=created_by
        )
        db.add(folder)
        await db.flush()
        await db.refresh(folder)
        return folder

    @staticmethod
    async def get_folder(
        db: AsyncSession,
        folder_id: UUID,
        tenant_id: UUID,
        group_id: UUID
    ) -> Folder:
        """Get folder by ID with RLS enforcement.
        
        Args:
            db: Database session
            folder_id: Folder ID
            tenant_id: Tenant ID (RLS)
            group_id: Group ID (RLS)
            
        Returns:
            Folder
            
        Raises:
            ValueError: If folder not found
        """
        folder = await db.scalar(
            select(Folder).where(
                and_(
                    Folder.id == folder_id,
                    Folder.tenant_id == tenant_id,
                    Folder.group_id == group_id,
                    Folder.deleted_at.is_(None)
                )
            )
        )
        if not folder:
            raise ValueError(f"Folder {folder_id} not found")
        return folder

    @staticmethod
    async def list_group_folders(
        db: AsyncSession,
        tenant_id: UUID,
        group_id: UUID,
        include_deleted: bool = False
    ) -> List[Folder]:
        """List all folders in a group.
        
        Args:
            db: Database session
            tenant_id: Tenant ID (RLS)
            group_id: Group ID (RLS)
            include_deleted: Include soft-deleted folders
            
        Returns:
            List of folders
        """
        query = select(Folder).where(
            and_(
                Folder.tenant_id == tenant_id,
                Folder.group_id == group_id
            )
        )
        if not include_deleted:
            query = query.where(Folder.deleted_at.is_(None))
        
        query = query.order_by(Folder.name)
        result = await db.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def update_folder(
        db: AsyncSession,
        folder_id: UUID,
        tenant_id: UUID,
        group_id: UUID,
        name: str
    ) -> Folder:
        """Update folder name.
        
        Args:
            db: Database session
            folder_id: Folder ID
            tenant_id: Tenant ID (RLS)
            group_id: Group ID (RLS)
            name: New folder name
            
        Returns:
            Updated folder
            
        Raises:
            ValueError: If folder not found or name already exists
        """
        folder = await FolderService.get_folder(db, folder_id, tenant_id, group_id)
        
        # Check if new name conflicts with existing folder
        if folder.name != name:
            existing = await db.scalar(
                select(Folder).where(
                    and_(
                        Folder.tenant_id == tenant_id,
                        Folder.group_id == group_id,
                        Folder.name == name,
                        Folder.deleted_at.is_(None),
                        Folder.id != folder_id
                    )
                )
            )
            if existing:
                raise ValueError(f"Folder '{name}' already exists in this group")
        
        folder.name = name
        folder.updated_at = datetime.utcnow()
        await db.flush()
        await db.refresh(folder)
        return folder

    @staticmethod
    async def soft_delete_folder(
        db: AsyncSession,
        folder_id: UUID,
        tenant_id: UUID,
        group_id: UUID
    ) -> Folder:
        """Soft-delete a folder. Documents in folder have folder_id set to NULL.
        
        Args:
            db: Database session
            folder_id: Folder ID
            tenant_id: Tenant ID (RLS)
            group_id: Group ID (RLS)
            
        Returns:
            Soft-deleted folder
            
        Raises:
            ValueError: If folder not found
        """
        folder = await FolderService.get_folder(db, folder_id, tenant_id, group_id)
        
        # Mark folder as deleted
        folder.deleted_at = datetime.utcnow()
        folder.updated_at = datetime.utcnow()
        
        # Documents will have folder_id set to NULL by FK constraint ON DELETE SET NULL
        # But we'll do it explicitly here for clarity
        await db.execute(
            select(Document).where(
                and_(
                    Document.folder_id == folder_id,
                    Document.tenant_id == tenant_id,
                    Document.group_id == group_id
                )
            ).update({Document.folder_id: None})
        )
        
        await db.flush()
        await db.refresh(folder)
        return folder

    @staticmethod
    async def get_folder_stats(
        db: AsyncSession,
        folder_id: UUID,
        tenant_id: UUID,
        group_id: UUID
    ) -> dict:
        """Get folder statistics (document count, chunk count).
        
        Args:
            db: Database session
            folder_id: Folder ID
            tenant_id: Tenant ID (RLS)
            group_id: Group ID (RLS)
            
        Returns:
            Dict with doc_count and chunk_count
        """
        # Verify folder exists
        await FolderService.get_folder(db, folder_id, tenant_id, group_id)
        
        # Count documents
        doc_count = await db.scalar(
            select(func.count(Document.id)).where(
                and_(
                    Document.folder_id == folder_id,
                    Document.tenant_id == tenant_id,
                    Document.group_id == group_id,
                    Document.deleted_at.is_(None)
                )
            )
        ) or 0
        
        return {
            "doc_count": doc_count
        }
