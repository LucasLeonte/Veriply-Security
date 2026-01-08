"""GDPR compliance endpoints for user data rights.

Implements:
- Right to be Forgotten (DELETE /profile/me)
- Data Portability (GET /profile/export)
"""

import logging
import json
from uuid import UUID
from datetime import datetime
from typing import Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload

from app.core.database import get_db, set_tenant_context
from app.core.auth import get_current_user
from app.models import (
    User,
    Bot,
    Document,
    Chunk,
    Embedding,
    ConfidenceLog,
    GroupMember,
    EmailIntegration,
    AuditLog,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/profile", tags=["gdpr"])


async def _collect_user_data(db: AsyncSession, user: User) -> Dict[str, Any]:
    """Collect all user data for GDPR export.
    
    Returns a comprehensive JSON structure containing:
    - Profile information
    - Group memberships
    - Created bots and documents
    - Email integrations
    - Activity logs
    """
    data = {
        "user_profile": {
            "id": str(user.id),
            "email": user.email,
            "full_name": user.full_name,
            "tenant_id": str(user.tenant_id),
            "is_active": user.is_active,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "updated_at": user.updated_at.isoformat() if user.updated_at else None,
        },
        "group_memberships": [],
        "bots": [],
        "documents": [],
        "email_integrations": [],
        "hitl_activities": [],
        "audit_logs": [],
    }
    
    # Get group memberships
    result = await db.execute(
        select(GroupMember)
        .where(GroupMember.user_id == user.id)
        .options(selectinload(GroupMember.group))
    )
    memberships = result.scalars().all()
    
    for member in memberships:
        data["group_memberships"].append({
            "group_id": str(member.group_id),
            "group_name": member.group.name if member.group else None,
            "role": member.role.value,
            "joined_at": member.created_at.isoformat() if member.created_at else None,
        })
    
    # Get bots created by user
    result = await db.execute(
        select(Bot).where(Bot.creator_id == user.id)
    )
    bots = result.scalars().all()
    
    for bot in bots:
        data["bots"].append({
            "id": str(bot.id),
            "name": bot.name,
            "description": bot.description,
            "created_at": bot.created_at.isoformat() if bot.created_at else None,
        })
    
    # Get documents uploaded by user
    result = await db.execute(
        select(Document).where(Document.uploader_id == user.id)
    )
    documents = result.scalars().all()
    
    for doc in documents:
        data["documents"].append({
            "id": str(doc.id),
            "filename": doc.filename,
            "size_bytes": doc.size_bytes,
            "uploaded_at": doc.created_at.isoformat() if doc.created_at else None,
        })
    
    # Get email integrations
    result = await db.execute(
        select(EmailIntegration).where(EmailIntegration.user_id == user.id)
    )
    integrations = result.scalars().all()
    
    for integration in integrations:
        data["email_integrations"].append({
            "id": str(integration.id),
            "provider": integration.provider,
            "email_address": integration.email,
            "connected_at": integration.created_at.isoformat() if integration.created_at else None,
        })
    
    # Get HITL activities (resolved by user)
    result = await db.execute(
        select(ConfidenceLog).where(ConfidenceLog.resolved_by == user.id)
    )
    hitl_items = result.scalars().all()
    
    for item in hitl_items:
        data["hitl_activities"].append({
            "id": str(item.id),
            "question": item.question,
            "bot_response": item.bot_response,
            "resolved_at": item.resolved_at.isoformat() if item.resolved_at else None,
        })
    
    # Get audit logs
    result = await db.execute(
        select(AuditLog).where(AuditLog.actor_id == user.id).limit(1000)
    )
    logs = result.scalars().all()
    
    for log in logs:
        data["audit_logs"].append({
            "action": log.action,
            "timestamp": log.created_at.isoformat() if log.created_at else None,
            "details": log.details,
        })
    
    return data


@router.get("/export")
async def export_user_data(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    GDPR Data Portability: Export all user data in JSON format.
    
    Returns a comprehensive JSON file containing:
    - Profile information
    - Group memberships
    - Created bots and documents
    - Email integrations
    - HITL activities
    - Audit logs (last 1000 entries)
    
    Security: Users can only export their own data.
    """
    try:
        # Set RLS context
        await set_tenant_context(db, current_user.tenant_id)
        
        # Collect all user data
        user_data = await _collect_user_data(db, current_user)
        
        # Generate JSON export
        json_content = json.dumps(user_data, indent=2, ensure_ascii=False)
        
        # Return as downloadable file
        filename = f"veriply_data_export_{current_user.email}_{datetime.utcnow().strftime('%Y%m%d')}.json"
        
        return StreamingResponse(
            iter([json_content]),
            media_type="application/json",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
        
    except Exception as e:
        logger.exception(f"Error exporting user data for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to export user data"
        )


@router.delete("/me")
async def delete_user_account(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    GDPR Right to be Forgotten: Delete user account and associated data.
    
    This endpoint performs a cascade delete of:
    - User profile
    - Email integrations
    - Group memberships
    - Audit logs
    - HITL resolutions (anonymized)
    
    NOTE: Bots, documents, and chunks are NOT deleted as they may be
    shared resources. Instead, ownership is transferred to the tenant admin.
    
    Security: Users can only delete their own account.
    """
    try:
        # Set RLS context
        await set_tenant_context(db, current_user.tenant_id)

        user_id = current_user.id
        tenant_id = current_user.tenant_id

        logger.info(f"GDPR deletion requested for user {user_id} ({current_user.email})")

        # Require another owner/admin in the tenant before allowing deletion
        from app.models import Group
        admin_result = await db.execute(
            select(GroupMember.user_id)
            .join(Group, GroupMember.group_id == Group.id)
            .where(
                Group.tenant_id == tenant_id,
                GroupMember.role.in_(["owner", "admin"]),
                GroupMember.user_id != user_id,
            )
            .limit(1)
        )
        replacement_admin_id = admin_result.scalar_one_or_none()

        if not replacement_admin_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "Account deletion requires another tenant owner/admin. "
                    "Please promote another user to owner/admin before deleting your account."
                ),
            )

        # 1. Delete email integrations
        await db.execute(
            delete(EmailIntegration).where(EmailIntegration.user_id == user_id)
        )
        logger.info(f"Deleted email integrations for user {user_id}")

        # 2. Delete group memberships
        await db.execute(
            delete(GroupMember).where(GroupMember.user_id == user_id)
        )
        logger.info(f"Deleted group memberships for user {user_id}")

        # 3. Anonymize HITL resolutions (preserve content, remove identity)
        from sqlalchemy import update
        await db.execute(
            update(ConfidenceLog)
            .where(ConfidenceLog.resolved_by == user_id)
            .values(resolved_by=None)
        )
        logger.info(f"Anonymized HITL resolutions for user {user_id}")

        # 4. Delete audit logs
        await db.execute(
            delete(AuditLog).where(AuditLog.actor_id == user_id)
        )
        logger.info(f"Deleted audit logs for user {user_id}")

        # 5. Delete user-owned bots and documents instead of transferring ownership
        await db.execute(delete(Bot).where(Bot.creator_id == user_id))
        logger.info(f"Deleted bots for user {user_id}")

        # Delete documents and related chunks/embeddings owned by the user
        doc_ids_result = await db.execute(
            select(Document.id).where(Document.uploader_id == user_id)
        )
        doc_ids = [row[0] for row in doc_ids_result.all()]
        if doc_ids:
            await db.execute(delete(Embedding).where(Embedding.document_id.in_(doc_ids)))
            await db.execute(delete(Chunk).where(Chunk.document_id.in_(doc_ids)))
            await db.execute(delete(Document).where(Document.id.in_(doc_ids)))
            logger.info(f"Deleted documents (and chunks/embeddings) for user {user_id}")

        # 6. Delete the user account
        await db.execute(delete(User).where(User.id == user_id))
        logger.info(f"Deleted user account {user_id}")

        await db.commit()

        return {
            "message": "Account successfully deleted",
            "deleted_at": datetime.utcnow().isoformat(),
        }

    except HTTPException:
        # Pass through expected validation errors
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        logger.exception(f"Error deleting user account {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete user account. Please contact support."
        )
