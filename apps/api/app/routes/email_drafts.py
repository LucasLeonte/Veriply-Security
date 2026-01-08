"""API routes for email draft management and retry."""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.api.dependencies import get_current_user, get_db
from app.models.email_processing_queue import EmailProcessingQueue
from app.models.email_draft import EmailDraft
from app.models.user import User
from app.schemas import BaseSchema

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/email-drafts", tags=["email-drafts"])


class EmailDraftResponse(BaseSchema):
    """Email draft response schema."""
    id: str
    bot_id: str
    subject: str
    body: str
    confidence_score: int
    status: str
    created_at: str
    citations: dict = None


class QueueRetryResponse(BaseSchema):
    """Response for retry request."""
    queue_id: str
    status: str
    message: str


@router.post("/queue/{queue_id}/retry")
async def retry_email_processing(
    queue_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> QueueRetryResponse:
    """Manually retry email processing for a failed queue item.
    
    Args:
        queue_id: ID of the email_processing_queue item
        db: Database session
        user: Current user (for authorization)
    
    Returns:
        QueueRetryResponse with status and message
    
    Raises:
        HTTPException: If not found or already processed
    """
    # Get queue item
    queue_item = await db.scalar(
        select(EmailProcessingQueue).where(
            and_(
                EmailProcessingQueue.id == queue_id,
                EmailProcessingQueue.tenant_id == user.tenant_id,
            )
        )
    )
    
    if not queue_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Email processing queue item not found",
        )
    
    # Only allow retry for failed items
    if queue_item.status not in ("failed", "queued"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot retry item with status '{queue_item.status}'",
        )
    
    # Check retry limit
    if queue_item.retry_count >= 3:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum retry attempts exceeded (max: 3)",
        )
    
    # Mark for retry
    queue_item.status = "queued"
    queue_item.error_message = None
    await db.commit()
    
    logger.info(f"Manually retrying email processing for queue item {queue_id}")
    
    return QueueRetryResponse(
        queue_id=str(queue_id),
        status="queued",
        message="Email queued for retry",
    )


@router.get("/pending")
async def list_pending_drafts(
    bot_id: UUID = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[EmailDraftResponse]:
    """List pending email drafts waiting for review.
    
    Args:
        bot_id: Optional filter by bot
        db: Database session
        user: Current user (for authorization)
    
    Returns:
        List of pending email drafts
    """
    query = select(EmailDraft).where(
        and_(
            EmailDraft.tenant_id == user.tenant_id,
            EmailDraft.status == "pending_review",
        )
    )
    
    if bot_id:
        query = query.where(EmailDraft.bot_id == bot_id)
    
    result = await db.execute(query.order_by(EmailDraft.created_at.desc()))
    drafts = result.scalars().all()
    
    return [
        EmailDraftResponse(
            id=str(d.id),
            bot_id=str(d.bot_id),
            subject=d.subject,
            body=d.body,
            confidence_score=d.confidence_score,
            status=d.status,
            created_at=d.created_at.isoformat(),
            citations=d.citations,
        )
        for d in drafts
    ]


@router.get("/failed")
async def list_failed_queue_items(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[dict]:
    """List failed email processing queue items.
    
    Args:
        db: Database session
        user: Current user (for authorization)
    
    Returns:
        List of failed queue items with error details
    """
    result = await db.execute(
        select(EmailProcessingQueue).where(
            and_(
                EmailProcessingQueue.tenant_id == user.tenant_id,
                EmailProcessingQueue.status == "failed",
            )
        ).order_by(EmailProcessingQueue.updated_at.desc())
    )
    
    items = result.scalars().all()
    
    return [
        {
            "queue_id": str(item.id),
            "email_subject": item.email_subject,
            "error_message": item.error_message,
            "retry_count": item.retry_count,
            "created_at": item.created_at.isoformat(),
            "updated_at": item.updated_at.isoformat(),
        }
        for item in items
    ]
