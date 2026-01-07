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
from app.schemas.verified_qa import VerifiedQACreate, VerifiedQAResponse
from app.services.verified_qa import (
    create_verified_qa,
    get_verified_qa_by_id,
    list_verified_qa,
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
    
    **Access Control:** Current user must have permission to manage this bot
    **Scoping:** Entry is automatically scoped to tenant_id and bot's group_id
    """
    try:
        # Verify bot belongs to tenant and get group_id
        bot_stmt = select(Bot).where(
            and_(
                Bot.id == payload.bot_id,
                Bot.tenant_id == tenant_id,
            )
        )
        bot_result = await db.execute(bot_stmt)
        bot = bot_result.scalar_one_or_none()

        if not bot:
            raise HTTPException(
                status_code=403,
                detail=f"Bot {payload.bot_id} not found or does not belong to your tenant",
            )

        # Generate embedding for question
        try:
            question_embedding = await embedding_service.embed(payload.question_text)
        except Exception as e:
            logger.error(f"Embedding generation failed for question: {e}")
            raise HTTPException(
                status_code=500,
                detail="Failed to generate embedding for question",
            )

        # Check for duplicate questions in the same bot scope (case-insensitive)
        dup_stmt = select(VerifiedQA).where(
            and_(
                VerifiedQA.bot_id == payload.bot_id,
                VerifiedQA.question_text.ilike(payload.question_text.strip()),
            )
        )
        dup_result = await db.execute(dup_stmt)
        if dup_result.scalar_one_or_none():
            raise HTTPException(
                status_code=409,
                detail="A verified Q&A with this question already exists for this bot",
            )

        # Create the entry
        verified_qa = await create_verified_qa(
            db=db,
            tenant_id=tenant_id,
            group_id=bot.group_id,
            bot_id=payload.bot_id,
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
    bot_id: UUID = Query(..., description="Bot ID for scoping"),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: UUID = Depends(get_current_tenant),
):
    """Bulk import Q&A pairs from CSV file.
    
    **CSV Format:** question,answer columns (required); other columns ignored
    **Access Control:** Current user must have permission to manage this bot
    **Max Size:** 5MB per file, max 1000 rows
    
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

        # Verify bot access
        bot_stmt = select(Bot).where(
            and_(
                Bot.id == bot_id,
                Bot.tenant_id == tenant_id,
            )
        )
        bot_result = await db.execute(bot_stmt)
        bot = bot_result.scalar_one_or_none()

        if not bot:
            raise HTTPException(
                status_code=403,
                detail=f"Bot {bot_id} not found or does not belong to your tenant",
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

                # Check for duplicates
                dup_stmt = select(VerifiedQA).where(
                    and_(
                        VerifiedQA.bot_id == bot_id,
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
                    question_embedding = await embedding_service.embed(question)
                except Exception as e:
                    logger.error(f"Embedding failed for row {idx}: {e}")
                    skipped_rows.append({
                        "row": idx,
                        "reason": "Failed to generate embedding",
                    })
                    continue

                # Create entry
                verified_qa = await create_verified_qa(
                    db=db,
                    tenant_id=tenant_id,
                    group_id=bot.group_id,
                    bot_id=bot_id,
                    question_text=question,
                    question_embedding=question_embedding,
                    answer_text=answer,
                    approved_by_user_id=current_user.id,
                    approved_at=datetime.utcnow(),
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
            entry_id=entry_id,
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
    **Pagination:** Default 10 items, max 100 per request
    """
    try:
        entries = await list_verified_qa(
            db=db,
            tenant_id=tenant_id,
            bot_id=bot_id,
            group_id=group_id,
            skip=skip,
            limit=limit,
        )

        return [VerifiedQAResponse.from_orm(entry) for entry in entries]

    except Exception as e:
        logger.error(f"Error listing verified Q&A entries: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to list entries",
        )
