"""API routes for Verified QA operations.

Handles manual entry creation, CSV bulk import, and retrieval of verified Q&A pairs
with proper authorization and multi-tenant scoping.
"""

import io
import csv
import logging
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.core.database import get_db
from app.api.v1.auth import get_current_user, get_current_tenant
from app.models.user import User
from app.models.verified_qa import VerifiedQA
from app.models.bot import Bot
from app.models.group import Group
from app.schemas.verified_qa import VerifiedQACreate, VerifiedQAResponse, VerifiedQAUpdate
from app.services.verified_qa import (
    create_verified_qa,
    get_verified_qa_by_id,
    list_verified_qa,
    list_verified_qa_with_search,
    update_verified_qa_with_embedding,
    soft_delete_verified_qa,
)
from app.services.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)

# Router for verified QA endpoints
router = APIRouter(prefix="/verified-qa", tags=["verified-qa"])

# Initialize embedding service singleton
embedding_service = EmbeddingService()


@router.post("", status_code=201, response_model=VerifiedQAResponse)
async def create_entry(
    payload: VerifiedQACreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: UUID = Depends(get_current_tenant),
):
    """Create a new verified Q&A entry manually.
    
    **Access Control:** Current user must have permission to access this group
    **Scoping:** Entry is scoped to tenant_id and group_id (shared across all bots in the group)
    """
    try:
        # Verify group belongs to tenant
        group_stmt = select(Group).where(
            and_(
                Group.id == payload.group_id,
                Group.tenant_id == tenant_id,
            )
        )
        group_result = await db.execute(group_stmt)
        group = group_result.scalar_one_or_none()

        if not group:
            raise HTTPException(
                status_code=403,
                detail=f"Group {payload.group_id} not found or does not belong to your tenant",
            )

        # Generate embedding for question
        try:
            question_embedding = await embedding_service.embed_query(payload.question_text)
        except Exception as e:
            logger.error(f"Embedding generation failed for question: {e}")
            raise HTTPException(
                status_code=500,
                detail="Failed to generate embedding for question",
            )

        # Check for duplicate questions in the same group scope (case-insensitive)
        dup_stmt = select(VerifiedQA).where(
            and_(
                VerifiedQA.group_id == payload.group_id,
                VerifiedQA.question_text.ilike(payload.question_text.strip()),
            )
        )
        dup_result = await db.execute(dup_stmt)
        if dup_result.scalar_one_or_none():
            raise HTTPException(
                status_code=409,
                detail="A verified Q&A with this question already exists for this group",
            )

        # Create the entry (bot_id is now NULL since it's group-scoped)
        verified_qa = await create_verified_qa(
            db=db,
            tenant_id=tenant_id,
            group_id=payload.group_id,
            bot_id=None,  # Group-scoped, not bot-specific
            question_text=payload.question_text,
            question_embedding=question_embedding,
            answer_text=payload.answer_text,
            approved_by_user_id=current_user.id,
            approved_at=datetime.utcnow(),
            source_citations=payload.source_citations,
        )

        await db.commit()
        return VerifiedQAResponse.from_orm(verified_qa)

    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating verified Q&A entry: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to create verified Q&A entry",
        )


@router.post("/bulk-import", status_code=201)
async def bulk_import_csv(
    group_id: UUID = Query(..., description="Group ID for scoping (Q&A is shared across all bots in group)"),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: UUID = Depends(get_current_tenant),
):
    """Bulk import Q&A pairs from CSV file.
    
    **CSV Format:** question,answer columns (required); other columns ignored
    **Access Control:** Current user must have permission to access this group
    **Max Size:** 5MB per file, max 1000 rows
    **Scoping:** Q&A entries are shared across all bots in the group
    
    Returns summary of imported vs skipped entries.
    """
    try:
        # Validate file size
        MAX_IMPORT_SIZE = 5 * 1024 * 1024  # 5MB
        contents = await file.read()
        if len(contents) > MAX_IMPORT_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"File exceeds maximum size of {MAX_IMPORT_SIZE} bytes",
            )

        # Verify group access
        group_stmt = select(Group).where(
            and_(
                Group.id == group_id,
                Group.tenant_id == tenant_id,
            )
        )
        group_result = await db.execute(group_stmt)
        group = group_result.scalar_one_or_none()

        if not group:
            raise HTTPException(
                status_code=403,
                detail=f"Group {group_id} not found or does not belong to your tenant",
            )

        # Parse CSV
        try:
            content_str = contents.decode("utf-8")
            csv_reader = csv.DictReader(io.StringIO(content_str))
            
            if not csv_reader.fieldnames or "question" not in csv_reader.fieldnames or "answer" not in csv_reader.fieldnames:
                raise HTTPException(
                    status_code=400,
                    detail="CSV must contain 'question' and 'answer' columns",
                )

            rows = list(csv_reader)
            if len(rows) > 1000:
                raise HTTPException(
                    status_code=400,
                    detail="CSV file cannot contain more than 1000 rows",
                )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"CSV parsing error: {e}")
            raise HTTPException(
                status_code=400,
                detail="Failed to parse CSV file",
            )

        # Process rows
        imported_count = 0
        skipped_rows = []

        for idx, row in enumerate(rows, start=2):  # Start at 2 to account for header
            try:
                question = row.get("question", "").strip()
                answer = row.get("answer", "").strip()

                # Validate required fields
                if not question or not answer:
                    skipped_rows.append({
                        "row": idx,
                        "reason": "Missing question or answer",
                    })
                    continue

                # Check length constraints
                if len(question) > 2000:
                    skipped_rows.append({
                        "row": idx,
                        "reason": f"Question exceeds 2000 characters ({len(question)} chars)",
                    })
                    continue

                if len(answer) > 8000:
                    skipped_rows.append({
                        "row": idx,
                        "reason": f"Answer exceeds 8000 characters ({len(answer)} chars)",
                    })
                    continue

                # Check for duplicates in group scope
                dup_stmt = select(VerifiedQA).where(
                    and_(
                        VerifiedQA.group_id == group_id,
                        VerifiedQA.question_text.ilike(question),
                    )
                )
                dup_result = await db.execute(dup_stmt)
                if dup_result.scalar_one_or_none():
                    skipped_rows.append({
                        "row": idx,
                        "reason": "Question already exists in verified KB",
                    })
                    continue

                # Generate embedding
                try:
                    question_embedding = await embedding_service.embed_query(question)
                except Exception as e:
                    logger.error(f"Embedding failed for row {idx}: {e}")
                    skipped_rows.append({
                        "row": idx,
                        "reason": "Failed to generate embedding",
                    })
                    continue

                # Create entry (group-scoped, not bot-specific)
                verified_qa = await create_verified_qa(
                    db=db,
                    tenant_id=tenant_id,
                    group_id=group_id,
                    question_text=question,
                    question_embedding=question_embedding,
                    answer_text=answer,
                    approved_by_user_id=current_user.id,
                    approved_at=datetime.utcnow(),
                    bot_id=None,
                    source_citations=None,
                )
                imported_count += 1

            except Exception as e:
                logger.error(f"Error processing CSV row {idx}: {e}")
                skipped_rows.append({
                    "row": idx,
                    "reason": "Unexpected error during processing",
                })

        # Commit all successful imports
        await db.commit()

        return {
            "imported_count": imported_count,
            "skipped_count": len(skipped_rows),
            "total_rows": len(rows),
            "skipped_rows": skipped_rows,
        }

    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error during bulk import: {e}")
        raise HTTPException(
            status_code=500,
            detail="Bulk import failed",
        )


@router.get("/{entry_id}", response_model=VerifiedQAResponse)
async def get_entry(
    entry_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: UUID = Depends(get_current_tenant),
):
    """Retrieve a specific verified Q&A entry.
    
    **Access Control:** RLS enforced - user can only access entries from their tenant
    """
    try:
        verified_qa = await get_verified_qa_by_id(
            db=db,
            verified_qa_id=entry_id,
            tenant_id=tenant_id,
        )

        if not verified_qa:
            raise HTTPException(
                status_code=404,
                detail="Verified Q&A entry not found",
            )

        return VerifiedQAResponse.from_orm(verified_qa)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving verified Q&A entry: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve entry",
        )


@router.get("", response_model=List[VerifiedQAResponse])
async def list_entries(
    bot_id: Optional[UUID] = Query(None, description="Filter by bot ID"),
    group_id: Optional[UUID] = Query(None, description="Filter by group ID"),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: UUID = Depends(get_current_tenant),
):
    """List verified Q&A entries.
    
    **Access Control:** RLS enforced - returns only entries from current tenant
    **Filtering:** Can filter by bot_id and/or group_id
    **Pagination:** Default 10 items, max 100 per request
    """
    try:
        # Query parameter bot_id/group_id filters by specific scope
        entries, total = await list_verified_qa(
            db=db,
            tenant_id=tenant_id,
            bot_id=bot_id,
            group_id=group_id,
            limit=limit,
            offset=skip,
        )

        return [VerifiedQAResponse.from_orm(entry) for entry in entries]

    except Exception as e:
        logger.error(f"Error listing verified Q&A entries: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to list entries",
        )


@router.get("/search", response_model=dict)
async def search_entries(
    group_id: UUID = Query(..., description="Group ID to search within"),
    search: Optional[str] = Query(None, description="Keyword search (question/answer text)"),
    creator_id: Optional[UUID] = Query(None, description="Filter by creator/approver user ID"),
    from_date: Optional[str] = Query(None, description="Filter from date (ISO 8601 format)"),
    to_date: Optional[str] = Query(None, description="Filter to date (ISO 8601 format)"),
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: UUID = Depends(get_current_tenant),
):
    """Search and list verified Q&A entries with advanced filtering.
    
    **Features:**
    - Keyword search across question and answer text (case-insensitive)
    - Filter by creator/approver
    - Filter by date range (creation date)
    - Pagination
    
    **Access Control:** RLS enforced - can only search within accessible groups
    **Soft-delete:** Automatically excludes deleted entries
    """
    try:
        # Verify group access
        group_stmt = select(Group).where(
            and_(
                Group.id == group_id,
                Group.tenant_id == tenant_id,
            )
        )
        group_result = await db.execute(group_stmt)
        group = group_result.scalar_one_or_none()

        if not group:
            raise HTTPException(
                status_code=403,
                detail=f"Group {group_id} not found or does not belong to your tenant",
            )

        # Parse optional dates
        from_date_obj = None
        to_date_obj = None
        if from_date:
            try:
                from_date_obj = datetime.fromisoformat(from_date.replace('Z', '+00:00'))
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid from_date format: {from_date}. Use ISO 8601.",
                )
        if to_date:
            try:
                to_date_obj = datetime.fromisoformat(to_date.replace('Z', '+00:00'))
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid to_date format: {to_date}. Use ISO 8601.",
                )

        # Calculate offset from page number
        offset = (page - 1) * limit

        # Perform search with filters
        entries, total = await list_verified_qa_with_search(
            db=db,
            tenant_id=tenant_id,
            group_id=group_id,
            search_query=search,
            creator_id=creator_id,
            from_date=from_date_obj,
            to_date=to_date_obj,
            limit=limit,
            offset=offset,
        )

        return {
            "items": [VerifiedQAResponse.from_orm(entry) for entry in entries],
            "total": total,
            "page": page,
            "limit": limit,
            "total_pages": (total + limit - 1) // limit,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error searching verified Q&A entries: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to search entries",
        )


@router.put("/{entry_id}", response_model=VerifiedQAResponse)
async def update_entry(
    entry_id: UUID,
    group_id: UUID = Query(..., description="Group ID for RLS enforcement"),
    payload: VerifiedQAUpdate = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: UUID = Depends(get_current_tenant),
):
    """Update a verified Q&A entry (question, answer, or citations).
    
    **Important:** If you modify the question text, you MUST regenerate the embedding
    and provide it in the request. The API will NOT automatically regenerate embeddings.
    
    **Access Control:** RLS enforced - can only edit entries in accessible groups
    **Audit:** Updates are tracked with updated_at and updated_by_user_id
    """
    try:
        if not payload:
            raise HTTPException(
                status_code=400,
                detail="Request body required",
            )

        # Verify group access
        group_stmt = select(Group).where(
            and_(
                Group.id == group_id,
                Group.tenant_id == tenant_id,
            )
        )
        group_result = await db.execute(group_stmt)
        group = group_result.scalar_one_or_none()

        if not group:
            raise HTTPException(
                status_code=403,
                detail=f"Group {group_id} not found or does not belong to your tenant",
            )

        # Get existing entry with RLS check
        verified_qa = await get_verified_qa_by_id(
            db=db,
            verified_qa_id=entry_id,
            tenant_id=tenant_id,
            group_id=group_id,
        )

        if not verified_qa:
            raise HTTPException(
                status_code=404,
                detail="Verified Q&A entry not found",
            )

        # If question text is being updated, embedding must be regenerated
        # For now, the client must provide the new embedding
        # In a full implementation, we could regenerate here automatically
        question_changed = (
            payload.question_text is not None 
            and payload.question_text.strip() != verified_qa.question_text.strip()
        )

        if question_changed:
            # Re-embed the new question
            try:
                new_embedding = await embedding_service.embed_query(payload.question_text)
            except Exception as e:
                logger.error(f"Failed to regenerate embedding for updated question: {e}")
                raise HTTPException(
                    status_code=500,
                    detail="Failed to regenerate embedding for updated question",
                )
        else:
            new_embedding = None

        # Update entry with embedding if needed
        updated_qa = await update_verified_qa_with_embedding(
            db=db,
            verified_qa_id=entry_id,
            tenant_id=tenant_id,
            group_id=group_id,
            updated_by_user_id=current_user.id,
            update_data=payload,
            new_question_embedding=new_embedding,
        )

        await db.commit()
        return VerifiedQAResponse.from_orm(updated_qa)

    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error updating verified Q&A entry: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to update entry",
        )


@router.delete("/{entry_id}", status_code=204)
async def delete_entry(
    entry_id: UUID,
    group_id: UUID = Query(..., description="Group ID for RLS enforcement"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: UUID = Depends(get_current_tenant),
):
    """Delete (soft-delete) a verified Q&A entry.
    
    **Deletion Method:** Soft-delete with deleted_at timestamp
    **Auditability:** Deleted entries are preserved in the database for audit trails
    **Exclusion:** Soft-deleted entries are automatically excluded from all retrieval paths
    
    **Access Control:** RLS enforced - can only delete entries in accessible groups
    """
    try:
        # Verify group access
        group_stmt = select(Group).where(
            and_(
                Group.id == group_id,
                Group.tenant_id == tenant_id,
            )
        )
        group_result = await db.execute(group_stmt)
        group = group_result.scalar_one_or_none()

        if not group:
            raise HTTPException(
                status_code=403,
                detail=f"Group {group_id} not found or does not belong to your tenant",
            )

        # Get existing entry to verify it exists
        verified_qa = await get_verified_qa_by_id(
            db=db,
            verified_qa_id=entry_id,
            tenant_id=tenant_id,
            group_id=group_id,
        )

        if not verified_qa:
            raise HTTPException(
                status_code=404,
                detail="Verified Q&A entry not found",
            )

        # Soft-delete the entry
        success = await soft_delete_verified_qa(
            db=db,
            verified_qa_id=entry_id,
            tenant_id=tenant_id,
            group_id=group_id,
            deleted_by_user_id=current_user.id,
        )

        if not success:
            raise HTTPException(
                status_code=404,
                detail="Verified Q&A entry not found",
            )

        await db.commit()
        # No content response for successful delete

    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error deleting verified Q&A entry: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to delete entry",
        )

