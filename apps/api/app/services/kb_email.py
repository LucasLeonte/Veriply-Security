"""Service layer for KB Email operations."""

import logging
from typing import Optional, List, Tuple
from uuid import UUID
from datetime import datetime

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
        metadata: Additional metadata dictionary
    
    Returns:
        Created KBEmail instance
    """
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
        metadata=metadata or {},
        status="uploaded",  # Will be processed by background worker
    )
    
    db.add(kb_email)
    await db.flush()
    await db.refresh(kb_email)
    
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
