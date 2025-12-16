"""Bot document access API routes for bot-level access control."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import List, Optional
import logging

from app.core.auth import get_current_user
from app.core.database import get_db
from app.services.bot_access_service import BotAccessService
from app.services.bot_group_service import BotGroupService
from app.services.group_service import GroupService
from app.services.audit_service import AuditService
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/bots/{bot_id}/access", tags=["bot-access"])


# Pydantic schemas
class SetAccessRequest(BaseModel):
    is_allowed: bool


class BulkSetAccessRequest(BaseModel):
    document_ids: Optional[List[str]] = None
    folder_ids: Optional[List[str]] = None
    is_allowed: bool


class FolderAccessItem(BaseModel):
    id: str
    name: str
    allowed: bool
    has_explicit_access: bool
    has_doc_overrides: bool


class DocumentAccessItem(BaseModel):
    id: str
    name: str
    folder_id: Optional[str]
    allowed: bool
    has_explicit_access: bool
    explicit_allowed: Optional[bool]


class AccessSummaryResponse(BaseModel):
    folders: List[FolderAccessItem]
    documents: List[DocumentAccessItem]


@router.get("", response_model=AccessSummaryResponse)
async def get_bot_access(
    bot_id: UUID,
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    """Get access summary for a bot showing all folders and documents with their access states.
    
    Required permissions: group member (any role)
    """
    try:
        tenant_id = UUID(current_user["tenant_id"])
        user_id = UUID(current_user["sub"])
        
        # Get bot to verify it exists and get group_id
        bot = await BotGroupService.get_bot(session, bot_id, tenant_id)
        group_id = bot.group_id
        
        # Verify user is group member
        role = await GroupService.get_member_role(session, group_id, user_id)
        if not role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You must be a group member to view bot access"
            )
        
        # Get access summary
        summary = await BotAccessService.get_access_summary(
            db=session,
            bot_id=bot_id,
            tenant_id=tenant_id,
            group_id=group_id
        )
        
        return AccessSummaryResponse(
            folders=[FolderAccessItem(**f) for f in summary["folders"]],
            documents=[DocumentAccessItem(**d) for d in summary["documents"]]
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error getting bot access: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get bot access"
        )


@router.post("/documents/{document_id}")
async def set_document_access(
    bot_id: UUID,
    document_id: UUID,
    access_data: SetAccessRequest,
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    """Set explicit document access for a bot.
    
    Required permissions: group member (any role)
    """
    try:
        tenant_id = UUID(current_user["tenant_id"])
        user_id = UUID(current_user["sub"])
        
        # Get bot to verify it exists and get group_id
        bot = await BotGroupService.get_bot(session, bot_id, tenant_id)
        group_id = bot.group_id
        
        # Verify user is group member
        role = await GroupService.get_member_role(session, group_id, user_id)
        if not role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You must be a group member to modify bot access"
            )
        
        # Set document access
        await BotAccessService.set_document_access(
            db=session,
            bot_id=bot_id,
            document_id=document_id,
            is_allowed=access_data.is_allowed,
            tenant_id=tenant_id,
            group_id=group_id
        )
        
        # Audit log
        await AuditService.log_action(
            db=session,
            actor_id=user_id,
            action="bot_document_access_updated",
            details={
                "bot_id": str(bot_id),
                "document_id": str(document_id),
                "is_allowed": access_data.is_allowed
            }
        )
        
        await session.commit()
        
        return {"message": "Document access updated successfully"}
        
    except ValueError as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        await session.rollback()
        logger.error(f"Error setting document access: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to set document access"
        )


@router.post("/folders/{folder_id}")
async def set_folder_access(
    bot_id: UUID,
    folder_id: UUID,
    access_data: SetAccessRequest,
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    """Set folder access for a bot.
    
    Required permissions: group member (any role)
    """
    try:
        tenant_id = UUID(current_user["tenant_id"])
        user_id = UUID(current_user["sub"])
        
        # Get bot to verify it exists and get group_id
        bot = await BotGroupService.get_bot(session, bot_id, tenant_id)
        group_id = bot.group_id
        
        # Verify user is group member
        role = await GroupService.get_member_role(session, group_id, user_id)
        if not role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You must be a group member to modify bot access"
            )
        
        # Set folder access
        await BotAccessService.set_folder_access(
            db=session,
            bot_id=bot_id,
            folder_id=folder_id,
            is_allowed=access_data.is_allowed,
            tenant_id=tenant_id,
            group_id=group_id
        )
        
        # Audit log
        await AuditService.log_action(
            db=session,
            actor_id=user_id,
            action="bot_folder_access_updated",
            details={
                "bot_id": str(bot_id),
                "folder_id": str(folder_id),
                "is_allowed": access_data.is_allowed
            }
        )
        
        await session.commit()
        
        return {"message": "Folder access updated successfully"}
        
    except ValueError as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        await session.rollback()
        logger.error(f"Error setting folder access: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to set folder access"
        )


@router.post("/bulk")
async def bulk_set_access(
    bot_id: UUID,
    access_data: BulkSetAccessRequest,
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    """Bulk set access for multiple documents/folders.
    
    Required permissions: group member (any role)
    """
    try:
        tenant_id = UUID(current_user["tenant_id"])
        user_id = UUID(current_user["sub"])
        
        # Get bot to verify it exists and get group_id
        bot = await BotGroupService.get_bot(session, bot_id, tenant_id)
        group_id = bot.group_id
        
        # Verify user is group member
        role = await GroupService.get_member_role(session, group_id, user_id)
        if not role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You must be a group member to modify bot access"
            )
        
        # Convert string IDs to UUIDs
        document_ids = [UUID(doc_id) for doc_id in access_data.document_ids] if access_data.document_ids else None
        folder_ids = [UUID(folder_id) for folder_id in access_data.folder_ids] if access_data.folder_ids else None
        
        # Bulk set access
        result = await BotAccessService.bulk_set_access(
            db=session,
            bot_id=bot_id,
            document_ids=document_ids,
            folder_ids=folder_ids,
            is_allowed=access_data.is_allowed,
            tenant_id=tenant_id,
            group_id=group_id
        )
        
        # Audit log
        await AuditService.log_action(
            db=session,
            actor_id=user_id,
            action="bot_bulk_access_updated",
            details={
                "bot_id": str(bot_id),
                "documents_updated": result["documents_updated"],
                "folders_updated": result["folders_updated"],
                "is_allowed": access_data.is_allowed
            }
        )
        
        await session.commit()
        
        return {
            "message": "Bulk access updated successfully",
            "documents_updated": result["documents_updated"],
            "folders_updated": result["folders_updated"]
        }
        
    except ValueError as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        await session.rollback()
        logger.error(f"Error bulk setting access: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to bulk set access"
        )
