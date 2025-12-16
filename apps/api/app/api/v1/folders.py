"""Folders API routes for group-scoped folder management."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import List, Optional
import logging

from app.core.auth import get_current_user
from app.core.database import get_db
from app.services.folder_service import FolderService
from app.services.group_service import GroupService
from app.services.audit_service import AuditService
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/groups/{group_id}/folders", tags=["folders"])


# Pydantic schemas
class FolderCreate(BaseModel):
    name: str


class FolderUpdate(BaseModel):
    name: str


class FolderStats(BaseModel):
    document_count: int


class FolderResponse(BaseModel):
    id: str
    tenant_id: str
    group_id: str
    name: str
    created_by: str
    created_at: str
    updated_at: str
    stats: Optional[FolderStats] = None

    class Config:
        from_attributes = True


@router.post("", response_model=FolderResponse, status_code=status.HTTP_201_CREATED)
async def create_folder(
    group_id: UUID,
    folder_data: FolderCreate,
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    """Create a new folder in a group.
    
    Required permissions: group member (any role)
    """
    try:
        tenant_id = UUID(current_user["tenant_id"])
        user_id = UUID(current_user["sub"])
        
        # Verify user is group member
        role = await GroupService.get_member_role(session, group_id, user_id)
        if not role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You must be a group member to create folders"
            )
        
        # Create folder
        folder = await FolderService.create_folder(
            db=session,
            tenant_id=tenant_id,
            group_id=group_id,
            name=folder_data.name,
            created_by=user_id
        )
        
        # Audit log
        await AuditService.log_action(
            db=session,
            actor_id=user_id,
            action="folder_created",
            details={
                "folder_id": str(folder.id),
                "folder_name": folder.name,
                "group_id": str(group_id)
            }
        )
        
        await session.commit()
        
        # Get stats
        stats = await FolderService.get_folder_stats(
            session, folder.id, tenant_id, group_id
        )
        
        response_data = {
            "id": str(folder.id),
            "tenant_id": str(folder.tenant_id),
            "group_id": str(folder.group_id),
            "name": folder.name,
            "created_by": str(folder.created_by),
            "created_at": folder.created_at.isoformat(),
            "updated_at": folder.updated_at.isoformat(),
            "stats": FolderStats(**stats)
        }
        
        return FolderResponse(**response_data)
        
    except ValueError as e:
        await session.rollback()
        if "already exists" in str(e):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=str(e)
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        await session.rollback()
        logger.error(f"Error creating folder: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create folder"
        )


@router.get("", response_model=List[FolderResponse])
async def list_folders(
    group_id: UUID,
    include_deleted: bool = False,
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    """List all folders in a group.
    
    Required permissions: group member (any role)
    """
    try:
        tenant_id = UUID(current_user["tenant_id"])
        user_id = UUID(current_user["sub"])
        
        # Verify user is group member
        role = await GroupService.get_member_role(session, group_id, user_id)
        if not role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You must be a group member to view folders"
            )
        
        # List folders
        folders = await FolderService.list_group_folders(
            db=session,
            tenant_id=tenant_id,
            group_id=group_id,
            include_deleted=include_deleted
        )
        
        # Build response with stats
        response = []
        for folder in folders:
            stats = await FolderService.get_folder_stats(
                db=session, folder_id=folder.id, tenant_id=tenant_id, group_id=group_id
            )
            response.append(FolderResponse(
                id=str(folder.id),
                tenant_id=str(folder.tenant_id),
                group_id=str(folder.group_id),
                name=folder.name,
                created_by=str(folder.created_by),
                created_at=folder.created_at.isoformat(),
                updated_at=folder.updated_at.isoformat(),
                stats=FolderStats(**stats)
            ))
        
        return response
        
    except Exception as e:
        logger.error(f"Error listing folders: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list folders"
        )


@router.get("/{folder_id}", response_model=FolderResponse)
async def get_folder(
    group_id: UUID,
    folder_id: UUID,
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    """Get folder details.
    
    Required permissions: group member (any role)
    """
    try:
        tenant_id = UUID(current_user["tenant_id"])
        user_id = UUID(current_user["sub"])
        
        # Verify user is group member
        role = await GroupService.get_member_role(session, group_id, user_id)
        if not role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You must be a group member to view folders"
            )
        
        # Get folder
        folder = await FolderService.get_folder(
            db=session,
            folder_id=folder_id,
            tenant_id=tenant_id,
            group_id=group_id
        )
        
        # Get stats
        stats = await FolderService.get_folder_stats(
            db=session, folder_id=folder.id, tenant_id=tenant_id, group_id=group_id
        )
        
        return FolderResponse(
            id=str(folder.id),
            tenant_id=str(folder.tenant_id),
            group_id=str(folder.group_id),
            name=folder.name,
            created_by=str(folder.created_by),
            created_at=folder.created_at.isoformat(),
            updated_at=folder.updated_at.isoformat(),
            stats=FolderStats(**stats)
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error getting folder: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get folder"
        )


@router.patch("/{folder_id}", response_model=FolderResponse)
async def update_folder(
    group_id: UUID,
    folder_id: UUID,
    folder_data: FolderUpdate,
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    """Update folder name.
    
    Required permissions: group member (any role)
    """
    try:
        tenant_id = UUID(current_user["tenant_id"])
        user_id = UUID(current_user["sub"])
        
        # Verify user is group member
        role = await GroupService.get_member_role(session, group_id, user_id)
        if not role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You must be a group member to update folders"
            )
        
        # Update folder
        folder = await FolderService.update_folder(
            db=session,
            folder_id=folder_id,
            tenant_id=tenant_id,
            group_id=group_id,
            name=folder_data.name
        )
        
        # Audit log
        await AuditService.log_action(
            db=session,
            actor_id=user_id,
            action="folder_updated",
            details={
                "folder_id": str(folder.id),
                "folder_name": folder.name,
                "group_id": str(group_id)
            }
        )
        
        await session.commit()
        
        # Get stats
        stats = await FolderService.get_folder_stats(
            db=session, folder_id=folder.id, tenant_id=tenant_id, group_id=group_id
        )
        
        return FolderResponse(
            id=str(folder.id),
            tenant_id=str(folder.tenant_id),
            group_id=str(folder.group_id),
            name=folder.name,
            created_by=str(folder.created_by),
            created_at=folder.created_at.isoformat(),
            updated_at=folder.updated_at.isoformat(),
            stats=FolderStats(**stats)
        )
        
    except ValueError as e:
        await session.rollback()
        if "already exists" in str(e):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=str(e)
            )
        elif "not found" in str(e):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        await session.rollback()
        logger.error(f"Error updating folder: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update folder"
        )


@router.delete("/{folder_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_folder(
    group_id: UUID,
    folder_id: UUID,
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    """Soft-delete a folder. Documents in folder have folder_id set to NULL.
    
    Required permissions: group member (any role)
    """
    try:
        tenant_id = UUID(current_user["tenant_id"])
        user_id = UUID(current_user["sub"])
        
        # Verify user is group member
        role = await GroupService.get_member_role(session, group_id, user_id)
        if not role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You must be a group member to delete folders"
            )
        
        # Delete folder
        folder = await FolderService.soft_delete_folder(
            db=session,
            folder_id=folder_id,
            tenant_id=tenant_id,
            group_id=group_id
        )
        
        # Audit log
        await AuditService.log_action(
            db=session,
            actor_id=user_id,
            action="folder_deleted",
            details={
                "folder_id": str(folder.id),
                "folder_name": folder.name,
                "group_id": str(group_id)
            }
        )
        
        await session.commit()
        return None
        
    except ValueError as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        await session.rollback()
        logger.error(f"Error deleting folder: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete folder"
        )
