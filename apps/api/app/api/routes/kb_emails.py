"""API routes for KB Email operations.

Handles email imports to knowledge base, listing, and retrieval.
"""

import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.core.database import get_db, set_tenant_context
from app.api.v1.auth import get_current_user, get_current_tenant
from app.models.user import User
from app.models.group import Group
from app.models.email_integration import EmailIntegration
from app.models.kb_email import KBEmail
from app.schemas.kb_email import KBEmailResponse, KBEmailListResponse
from app.services.kb_email import (
    list_kb_emails,
    get_kb_email_by_id,
    delete_kb_email,
    reprocess_kb_email,
)
from app import tasks

logger = logging.getLogger(__name__)

# Router for KB email endpoints
router = APIRouter(prefix="/kb-emails", tags=["kb-emails"])


@router.get("", response_model=KBEmailListResponse)
async def list_emails(
    group_id: Optional[UUID] = Query(None, description="Filter by group ID"),
    integration_id: Optional[UUID] = Query(None, description="Filter by integration ID"),
    status: Optional[str] = Query(None, description="Filter by status (uploaded, processing, ready, failed)"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Results per page"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: UUID = Depends(get_current_tenant),
):
    """List KB emails with optional filtering and pagination.
    
    **Access Control:** Only emails from user's tenant are returned
    **Filtering:** Can filter by group, integration, and status
    """
    try:
        await set_tenant_context(db, tenant_id)
        
        emails, total = await list_kb_emails(
            db=db,
            tenant_id=tenant_id,
            group_id=group_id,
            integration_id=integration_id,
            status=status,
            page=page,
            page_size=page_size,
        )
        
        return KBEmailListResponse(
            emails=[KBEmailResponse.from_orm(email) for email in emails],
            total=total,
            page=page,
            page_size=page_size,
        )
    
    except Exception as e:
        logger.error(f"Error listing KB emails: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to list KB emails",
        )


@router.get("/{email_id}", response_model=KBEmailResponse)
async def get_email(
    email_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: UUID = Depends(get_current_tenant),
):
    """Get a specific KB email by ID.
    
    **Access Control:** Email must belong to user's tenant
    """
    try:
        await set_tenant_context(db, tenant_id)
        
        kb_email = await get_kb_email_by_id(db, email_id, tenant_id)
        
        if not kb_email:
            raise HTTPException(
                status_code=404,
                detail="KB email not found",
            )
        
        return KBEmailResponse.from_orm(kb_email)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting KB email: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to get KB email",
        )


@router.delete("/{email_id}", status_code=204)
async def delete_email(
    email_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: UUID = Depends(get_current_tenant),
):
    """Delete a KB email entry.
    
    **Access Control:** Email must belong to user's tenant
    **Note:** This will also delete associated chunks and embeddings
    """
    try:
        await set_tenant_context(db, tenant_id)
        
        kb_email = await get_kb_email_by_id(db, email_id, tenant_id)
        
        if not kb_email:
            raise HTTPException(
                status_code=404,
                detail="KB email not found",
            )
        
        await delete_kb_email(db, kb_email)
        await db.commit()
        
        return None
    
    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error deleting KB email: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to delete KB email",
        )
@router.post("/{email_id}/reprocess")
async def reprocess_email(
    email_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: UUID = Depends(get_current_tenant),
):
    """Trigger reprocessing for a KB email.
    
    **Access Control:** Email must belong to user's tenant
    """
    try:
        await set_tenant_context(db, tenant_id)
        
        kb_email = await get_kb_email_by_id(db, email_id, tenant_id)
        
        if not kb_email:
            raise HTTPException(
                status_code=404,
                detail="KB email not found",
            )
        
        await reprocess_kb_email(db, kb_email)
        await db.commit()
        
        # Trigger processing task
        tasks.enqueue_kb_email_processing(str(kb_email.id))
        
        return {"message": "Email queued for reprocessing"}
    
    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error reprocessing KB email: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to trigger reprocessing",
        )
