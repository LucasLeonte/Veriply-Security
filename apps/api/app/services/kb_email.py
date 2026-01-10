"""Service layer for KB Email operations."""

import logging
from typing import Optional, List, Tuple
from uuid import UUID
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, desc

from app.models.kb_email import KBEmail
from app.services.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)


async def create_kb_email(
    db: AsyncSession,
    tenant_id: UUID,
    group_id: UUID,
    user_id: UUID,
    integration_id: UUID,
    email_id: str,
    thread_id: Optional[str],
    subject: Optional[str],
    from_email: Optional[str],
    to_emails: Optional[str],
    body_text: Optional[str],
    sent_at: Optional[datetime],
    metadata: Optional[dict] = None,
    style_analysis_mode: str = "auto",  # 'auto', 'force', 'skip'
    style_content: Optional[str] = None,
) -> KBEmail:
    """Create a new KB email entry.
    
    Args:
        db: Database session
        tenant_id: Tenant UUID
        group_id: Group UUID for scoping
        user_id: User who imported the email
        integration_id: Email integration UUID
        email_id: Provider's message ID
        thread_id: Thread/conversation ID
        subject: Email subject
        from_email: Sender email address
        to_emails: Comma-separated recipient list
        body_text: Plain text email body
        sent_at: Email send timestamp
        metadata: Additional metadata dictionary (stored in email_metadata column)
    
    Returns:
        Created KBEmail instance
    """
    # Ensure sent_at is timezone-naive UTC
    if sent_at and sent_at.tzinfo:
        # Convert to UTC first if it has timezone info
        sent_at = sent_at.astimezone(timezone.utc).replace(tzinfo=None)

    kb_email = KBEmail(
        tenant_id=tenant_id,
        group_id=group_id,
        user_id=user_id,
        integration_id=integration_id,
        email_id=email_id,
        thread_id=thread_id,
        subject=subject or "",
        from_email=from_email,
        to_emails=to_emails,
        body_text=body_text,
        sent_at=sent_at,
        email_metadata=metadata or {},  # Renamed from 'metadata'
        status="uploaded",  # Will be processed by background worker
    )
    
    db.add(kb_email)
    await db.flush()
    await db.refresh(kb_email)
    
    # Async check for style analysis (dont block return)
    try:
        await check_and_trigger_style_analysis(
            db, tenant_id, user_id, integration_id, kb_email, 
            mode=style_analysis_mode,
            custom_content=style_content
        )
    except Exception as e:
        logger.error(f"Error in style analysis trigger: {e}")
    
    return kb_email


async def get_kb_email_by_id(
    db: AsyncSession,
    email_id: UUID,
    tenant_id: UUID,
) -> Optional[KBEmail]:
    """Get a KB email by ID with tenant isolation."""
    stmt = select(KBEmail).where(
        and_(
            KBEmail.id == email_id,
            KBEmail.tenant_id == tenant_id,
        )
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def list_kb_emails(
    db: AsyncSession,
    tenant_id: UUID,
    group_id: Optional[UUID] = None,
    integration_id: Optional[UUID] = None,
    status: Optional[str] = None,
    page: int = 1,
    page_size: int = 50,
) -> Tuple[List[KBEmail], int]:
    """List KB emails with optional filtering and pagination.
    
    Args:
        db: Database session
        tenant_id: Tenant UUID for isolation
        group_id: Optional group filter
        integration_id: Optional integration filter
        status: Optional status filter
        page: Page number (1-indexed)
        page_size: Number of results per page
    
    Returns:
        Tuple of (email list, total count)
    """
    # Build base query
    conditions = [KBEmail.tenant_id == tenant_id]
    
    if group_id:
        conditions.append(KBEmail.group_id == group_id)
    if integration_id:
        conditions.append(KBEmail.integration_id == integration_id)
    if status:
        conditions.append(KBEmail.status == status)
    
    # Count query
    count_stmt = select(func.count(KBEmail.id)).where(and_(*conditions))
    count_result = await db.execute(count_stmt)
    total = count_result.scalar() or 0
    
    # Data query with pagination
    offset = (page - 1) * page_size
    stmt = (
        select(KBEmail)
        .where(and_(*conditions))
        .order_by(desc(KBEmail.created_at))
        .limit(page_size)
        .offset(offset)
    )
    
    result = await db.execute(stmt)
    emails = result.scalars().all()
    
    return list(emails), total


async def update_kb_email_status(
    db: AsyncSession,
    kb_email: KBEmail,
    status: str,
    chunk_count: Optional[int] = None,
) -> KBEmail:
    """Update KB email processing status.
    
    Args:
        db: Database session
        kb_email: KBEmail instance to update
        status: New status (uploaded, processing, ready, failed)
        chunk_count: Optional number of chunks created
    
    Returns:
        Updated KBEmail instance
    """
    kb_email.status = status
    kb_email.updated_at = datetime.utcnow()
    
    if status in ("ready", "failed"):
        kb_email.processed_at = datetime.utcnow()
    
    if chunk_count is not None:
        kb_email.chunk_count = str(chunk_count)
    
    await db.flush()
    await db.refresh(kb_email)
    
    return kb_email


async def delete_kb_email(
    db: AsyncSession,
    kb_email: KBEmail,
) -> None:
    """Delete a KB email entry.
    
    Args:
        db: Database session
        kb_email: KBEmail instance to delete
    """
    await db.delete(kb_email)
    await db.flush()


async def reprocess_kb_email(
    db: AsyncSession,
    kb_email: KBEmail,
) -> KBEmail:
    """Reset KB email status to uploaded to trigger reprocessing.
    
    Args:
        db: Database session
        kb_email: KBEmail instance to reprocess
    
    Returns:
        Updated KBEmail instance
    """
    kb_email.status = "uploaded"
    kb_email.updated_at = datetime.utcnow()
    # Reset chunk count as they will be regenerated
    kb_email.chunk_count = None
    
    await db.flush()
    await db.refresh(kb_email)
    
    return kb_email


async def check_and_trigger_style_analysis(
    db: AsyncSession,
    tenant_id: UUID,
    user_id: UUID,
    integration_id: UUID,
    kb_email: KBEmail,
    mode: str = "auto",
    custom_content: Optional[str] = None
) -> None:
    """Check if email matches user's integration and trigger style analysis."""
    from app.models.email_integration import EmailIntegration
    from app.models.user_email_history import UserEmailHistory
    from app.workers.style_analyzer_worker import StyleAnalysisWorker
    
    # Get integration to check email address
    stmt = select(EmailIntegration).where(
        and_(
            EmailIntegration.id == integration_id,
            EmailIntegration.tenant_id == tenant_id,
        )
    )
    result = await db.execute(stmt)
    integration = result.scalar_one_or_none()
    
    # Check if sender matches integration email (case insensitive)
    # Use getattr because 'email' column might not be migrated yet
    integration_email = getattr(integration, "email", None)
    
    if not integration_email:
        # Fallback: check against user's email
        from app.models.user import User
        user = await db.get(User, user_id)
        if user and user.email:
            integration_email = user.email

    if not integration_email:
        return

    if mode == "skip":
        return

    should_process = False
    if mode == "force":
        should_process = True
    else:
        # Auto mode: check sender
        if kb_email.from_email and integration_email and kb_email.from_email.lower() == integration_email.lower():
            should_process = True
    
    if not should_process:
        return
    
    # It's a sent email! processing for style analysis
    logger.info(f"Detected sent email import (ID {kb_email.id}). Adding to style history.")
    
    content_to_analyze = custom_content if custom_content else kb_email.body_text
    
    if not content_to_analyze or not content_to_analyze.strip():
        logger.warning(f"No user-authored content found for style analysis (ID {kb_email.id}). Skipping.")
        return
    
    # Check if already in history
    hist_stmt = select(UserEmailHistory).where(
        and_(
            UserEmailHistory.integration_id == integration_id,
            UserEmailHistory.email_id == kb_email.email_id,
        )
    )
    hist_result = await db.execute(hist_stmt)
    if hist_result.scalar_one_or_none():
        return # Already exists
        
    # Add to history
    email_history = UserEmailHistory(
        tenant_id=tenant_id,
        user_id=user_id,
        integration_id=integration_id,
        email_id=kb_email.email_id,
        subject=kb_email.subject,
        body=content_to_analyze,
        sent_at=kb_email.sent_at or datetime.utcnow(),
        analyzed=False 
    )
    db.add(email_history)
    await db.flush()
    
    # Trigger analysis worker (fire and forget via background task ideally, but logic here for MVP)
    # Using the worker class directly here might be blocking if not careful, 
    # but since it's async it should be fine to await if short, or enqueue.
    # For now we will just log it. The weekly worker or manual refresh will pick it up,
    # OR we can explicitly trigger it.
    # Let's trigger it.
    try:
        worker = StyleAnalysisWorker(
            client_id="internal", # Not needed for internal processing usually
            client_secret="internal"
        )
        # We don't want to re-fetch from Gmail, just smooth analyze existing db records
        await worker.analyze_user_style(db, tenant_id, user_id, integration_id)
    except Exception as e:
        logger.error(f"Failed to trigger style analysis for KB email {kb_email.id}: {e}")

