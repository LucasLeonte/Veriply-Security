"""Service layer for VerifiedQA operations.

Handles business logic for creating, reading, updating, and deleting verified Q&A pairs,
with proper RLS enforcement and multi-tenant scoping.
"""

import logging
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.verified_qa import VerifiedQA
from app.models.bot import Bot
from app.schemas.verified_qa import VerifiedQACreate, VerifiedQAUpdate

logger = logging.getLogger(__name__)


async def create_verified_qa(
    db: AsyncSession,
    tenant_id: UUID,
    group_id: UUID,
    question_text: str,
    question_embedding: List[float],
    answer_text: str,
    approved_by_user_id: UUID,
    approved_at: datetime,
    bot_id: Optional[UUID] = None,
    source_citations: Optional[dict] = None,
) -> VerifiedQA:
    """Create a new verified Q&A entry.
    
    This function is called when a HITL approval creates a verified entry,
    or when manually adding Q&A pairs through the API.
    
    Args:
        db: Async database session
        tenant_id: Tenant UUID for RLS isolation
        group_id: Group UUID for group-level scoping (Q&A is shared across all bots in group)
        question_text: The verified question
        question_embedding: 768-dim embedding vector for semantic search
        answer_text: The approved answer
        approved_by_user_id: User who approved this entry
        approved_at: Timestamp of approval
        bot_id: Optional bot UUID (for backwards compatibility, but entries are now group-scoped)
        source_citations: Optional document citations (JSONB)
        
    Returns:
        Created VerifiedQA instance
        
    Raises:
        ValueError: If validation fails (e.g., question too long)
        Exception: If database operation fails
    """
    # Validate question length (belt-and-suspenders with DB constraint)
    if len(question_text) > 2000:
        raise ValueError(f"Question text exceeds maximum length of 2000 characters (got {len(question_text)})")
    
    # Validate embedding dimensions
    if len(question_embedding) != 768:
        raise ValueError(f"Question embedding must be 768 dimensions (got {len(question_embedding)})")
    
    # Validate group exists for this tenant (no longer validating bot since entries are group-scoped)
    from app.models.group import Group
    group_stmt = select(Group).where(
        and_(
            Group.id == group_id,
            Group.tenant_id == tenant_id,
        )
    )
    group_result = await db.execute(group_stmt)
    group = group_result.scalar_one_or_none()
    
    if not group:
        raise ValueError(f"Group {group_id} not found or does not belong to tenant {tenant_id}")
    
    # Create verified_qa entry
    verified_qa = VerifiedQA(
        tenant_id=tenant_id,
        group_id=group_id,
        bot_id=bot_id,
        question_text=question_text.strip(),
        question_embedding=question_embedding,
        answer_text=answer_text.strip(),
        source_citations=source_citations,
        approved_by_user_id=approved_by_user_id,
        approved_at=approved_at,
    )
    
    db.add(verified_qa)
    await db.flush()  # Flush to get ID without committing transaction
    
    logger.info(
        f"Created verified Q&A entry {verified_qa.id} for bot {bot_id} "
        f"(tenant={tenant_id}, group={group_id})"
    )
    
    return verified_qa


async def get_verified_qa_by_id(
    db: AsyncSession,
    verified_qa_id: UUID,
    tenant_id: UUID,
    group_id: Optional[UUID] = None,
) -> Optional[VerifiedQA]:
    """Retrieve a verified Q&A entry by ID with RLS enforcement.
    
    Args:
        db: Async database session
        verified_qa_id: UUID of the verified Q&A entry
        tenant_id: Tenant UUID for RLS check
        group_id: Optional group UUID for additional scoping
        
    Returns:
        VerifiedQA instance if found and accessible, None otherwise
    """
    conditions = [
        VerifiedQA.id == verified_qa_id,
        VerifiedQA.tenant_id == tenant_id,
    ]
    if group_id:
        conditions.append(VerifiedQA.group_id == group_id)
    
    stmt = select(VerifiedQA).where(and_(*conditions))
    
    result = await db.execute(stmt)
    verified_qa = result.scalar_one_or_none()
    
    if verified_qa:
        logger.debug(f"Retrieved verified Q&A {verified_qa_id}")
    else:
        logger.debug(f"Verified Q&A {verified_qa_id} not found or not accessible")
    
    return verified_qa


async def list_verified_qa(
    db: AsyncSession,
    tenant_id: UUID,
    bot_id: Optional[UUID] = None,
    group_id: Optional[UUID] = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[List[VerifiedQA], int]:
    """List verified Q&A entries with pagination.
    
    Args:
        db: Async database session
        tenant_id: Tenant UUID for RLS filtering
        bot_id: Optional bot ID to filter by specific bot
        group_id: Optional group UUID for group-level scoping
        limit: Maximum number of entries to return (default 50)
        offset: Pagination offset (default 0)
        
    Returns:
        Tuple of (list of VerifiedQA entries, total count)
    """
    # Build base query with RLS filters
    base_conditions = [
        VerifiedQA.tenant_id == tenant_id,
    ]
    
    if group_id:
        base_conditions.append(VerifiedQA.group_id == group_id)
    
    if bot_id:
        base_conditions.append(VerifiedQA.bot_id == bot_id)
    
    # Count query
    count_stmt = select(func.count()).select_from(VerifiedQA).where(and_(*base_conditions))
    count_result = await db.execute(count_stmt)
    total = count_result.scalar_one()
    
    # Data query with pagination
    stmt = (
        select(VerifiedQA)
        .where(and_(*base_conditions))
        .order_by(VerifiedQA.approved_at.desc())
        .limit(limit)
        .offset(offset)
    )
    
    result = await db.execute(stmt)
    items = result.scalars().all()
    
    logger.debug(
        f"Listed {len(items)} verified Q&A entries (total={total}, "
        f"bot_id={bot_id}, limit={limit}, offset={offset})"
    )
    
    return list(items), total


async def update_verified_qa(
    db: AsyncSession,
    verified_qa_id: UUID,
    tenant_id: UUID,
    group_id: UUID,
    update_data: VerifiedQAUpdate,
) -> Optional[VerifiedQA]:
    """Update a verified Q&A entry.
    
    Used in Story 7.4 for editing existing verified entries.
    Only provided fields will be updated.
    
    Args:
        db: Async database session
        verified_qa_id: UUID of entry to update
        tenant_id: Tenant UUID for RLS check
        group_id: Group UUID for RLS check
        update_data: Pydantic schema with update fields
        
    Returns:
        Updated VerifiedQA instance if found and updated, None otherwise
    """
    # Fetch existing entry with RLS enforcement
    verified_qa = await get_verified_qa_by_id(db, verified_qa_id, tenant_id, group_id)
    
    if not verified_qa:
        return None
    
    # Apply updates
    update_dict = update_data.model_dump(exclude_unset=True)
    
    for field, value in update_dict.items():
        setattr(verified_qa, field, value)
    
    # Update timestamp
    verified_qa.updated_at = datetime.utcnow()
    
    await db.flush()
    
    logger.info(f"Updated verified Q&A {verified_qa_id} with fields: {list(update_dict.keys())}")
    
    return verified_qa


async def delete_verified_qa(
    db: AsyncSession,
    verified_qa_id: UUID,
    tenant_id: UUID,
    group_id: UUID,
) -> bool:
    """Delete a verified Q&A entry.
    
    Used in Story 7.4 for removing entries and for GDPR compliance
    (Right to be Forgotten).
    
    Args:
        db: Async database session
        verified_qa_id: UUID of entry to delete
        tenant_id: Tenant UUID for RLS check
        group_id: Group UUID for RLS check
        
    Returns:
        True if entry was deleted, False if not found or not accessible
    """
    # Fetch entry with RLS enforcement
    verified_qa = await get_verified_qa_by_id(db, verified_qa_id, tenant_id, group_id)
    
    if not verified_qa:
        return False
    
    await db.delete(verified_qa)
    await db.flush()
    
    logger.info(f"Deleted verified Q&A {verified_qa_id}")
    
    return True


async def search_verified_qa(
    db: AsyncSession,
    tenant_id: UUID,
    group_id: UUID,
    bot_id: Optional[UUID],
    query_embedding: List[float],
    k: int = 3,
    similarity_threshold: float = 0.7,
) -> List[tuple[VerifiedQA, float]]:
    """Search verified Q&A entries by semantic similarity.
    
    Performs a vector similarity search against the verified_qa question embeddings
    to find human-approved answers that match the query. These results should be
    prioritized over RAG-generated answers from document chunks.
    
    Q&A entries are now group-scoped (shared across all bots in the group).
    
    Args:
        db: Async database session
        tenant_id: Tenant UUID for RLS filtering
        group_id: Group UUID for group-level scoping (primary filter)
        bot_id: Optional bot UUID (ignored - Q&A is now group-scoped)
        query_embedding: 768-dim embedding vector of the user's query
        k: Maximum number of results to return (default 3)
        similarity_threshold: Minimum cosine similarity score (default 0.7, higher than
            document search since verified answers should be high-confidence matches)
        
    Returns:
        List of tuples (VerifiedQA entry, similarity score), sorted by similarity desc
    """
    from sqlalchemy import text
    
    # Validate embedding dimensions
    if len(query_embedding) != 768:
        logger.warning(f"Query embedding has wrong dimensions: {len(query_embedding)} (expected 768)")
        return []
    
    # Set RLS session variables to allow query access (required for public chat flow)
    # This ensures the RLS policy on verified_qa allows access to the correct tenant/group
    try:
        await db.execute(text(f"SET LOCAL app.current_tenant_id = '{str(tenant_id)}'"))
        await db.execute(text(f"SET LOCAL app.current_group_id = '{str(group_id)}'"))
    except Exception as rls_err:
        logger.warning(f"Failed to set RLS session variables: {rls_err}")
        # Continue anyway - the explicit WHERE clauses should still work
    
    # Set HNSW search parameter for performance
    await db.execute(text("SET hnsw.ef_search = 40"))
    
    # Perform vector similarity search using pgvector cosine distance
    # Note: cosine_distance returns 0 for identical vectors, 2 for opposite
    # Similarity = 1 - distance
    # Q&A entries are group-scoped (shared across all bots), so we only filter by group_id
    from sqlalchemy import select, and_
    
    stmt = (
        select(
            VerifiedQA,
            VerifiedQA.question_embedding.cosine_distance(query_embedding).label("distance"),
        )
        .where(
            and_(
                VerifiedQA.tenant_id == tenant_id,
                VerifiedQA.group_id == group_id,
                VerifiedQA.question_embedding.isnot(None),
            )
        )
        .order_by(text("distance"))
        .limit(k * 2)  # Get extra for threshold filtering
    )
    
    result = await db.execute(stmt)
    rows = result.all()
    
    # Convert distance to similarity and filter by threshold
    results: List[tuple[VerifiedQA, float]] = []
    for verified_qa, distance in rows:
        similarity = 1.0 - distance
        if similarity >= similarity_threshold:
            results.append((verified_qa, round(similarity, 4)))
        if len(results) >= k:
            break
    
    logger.info(
        f"Verified Q&A search: group_id={group_id}, results={len(results)}, "
        f"threshold={similarity_threshold}"
    )
    
    return results
