"""Knowledge Base API endpoints for managing verified answers.

Provides CRUD operations for the verified answers knowledge base,
allowing management of human-approved Q&A pairs.
"""

import logging
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, and_, func
from sqlalchemy.orm import joinedload
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.api.v1.auth import get_current_user, get_current_tenant
from app.models.user import User
from app.models.verified_answer import VerifiedAnswer
from app.models.bot import Bot

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/knowledge-base", tags=["knowledge-base"])


class VerifiedAnswerResponse(BaseModel):
    """Response model for verified answer."""
    id: str
    bot_id: str
    bot_name: str
    question: str
    answer: str
    is_active: bool
    created_at: str
    updated_at: str
    created_by_name: Optional[str] = None
    metadata: Optional[dict] = None

    class Config:
        from_attributes = True


class VerifiedAnswerCreateRequest(BaseModel):
    """Request to create a verified answer."""
    bot_id: str = Field(..., description="Bot ID this answer belongs to")
    question: str = Field(..., description="The question text")
    answer: str = Field(..., description="The verified answer text")
    metadata: Optional[dict] = Field(default=None, description="Additional metadata")


class VerifiedAnswerUpdateRequest(BaseModel):
    """Request to update a verified answer."""
    question: Optional[str] = Field(None, description="Updated question text")
    answer: Optional[str] = Field(None, description="Updated answer text")
    is_active: Optional[bool] = Field(None, description="Whether answer is active")
    metadata: Optional[dict] = Field(None, description="Updated metadata")


class VerifiedAnswerListResponse(BaseModel):
    """Response for list of verified answers."""
    items: List[VerifiedAnswerResponse]
    total: int
    page: int
    page_size: int


@router.get("/answers", response_model=VerifiedAnswerListResponse)
async def list_verified_answers(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_tenant: UUID = Depends(get_current_tenant),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    bot_id: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
) -> VerifiedAnswerListResponse:
    """
    List verified answers for the current tenant.
    
    Supports pagination, filtering by bot, search by question text,
    and filtering by active status.
    """
    try:
        # Build base query
        query = select(VerifiedAnswer).where(
            VerifiedAnswer.tenant_id == current_tenant
        ).options(
            joinedload(VerifiedAnswer.bot),
            joinedload(VerifiedAnswer.created_by)
        )
        
        # Apply filters
        if bot_id:
            query = query.where(VerifiedAnswer.bot_id == UUID(bot_id))
        
        if search:
            query = query.where(VerifiedAnswer.question.ilike(f"%{search}%"))
        
        if is_active is not None:
            query = query.where(VerifiedAnswer.is_active == is_active)
        
        # Get total count
        count_query = select(func.count()).select_from(
            query.subquery()
        )
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0
        
        # Apply pagination and ordering
        query = query.order_by(desc(VerifiedAnswer.created_at))
        query = query.offset((page - 1) * page_size).limit(page_size)
        
        result = await db.execute(query)
        items = result.unique().scalars().all()
        
        # Convert to response format
        response_items = []
        for item in items:
            bot_name = item.bot.name if item.bot else "Unknown Bot"
            created_by_name = None
            if item.created_by:
                created_by_name = item.created_by.display_name or item.created_by.email
            
            response_items.append(VerifiedAnswerResponse(
                id=str(item.id),
                bot_id=str(item.bot_id),
                bot_name=bot_name,
                question=item.question,
                answer=item.answer,
                is_active=item.is_active,
                created_at=item.created_at.isoformat(),
                updated_at=item.updated_at.isoformat(),
                created_by_name=created_by_name,
                metadata=item.metadata_json,
            ))
        
        return VerifiedAnswerListResponse(
            items=response_items,
            total=total,
            page=page,
            page_size=page_size,
        )
    
    except Exception as e:
        logger.error(f"Error listing verified answers: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list verified answers",
        )


@router.post("/answers", response_model=VerifiedAnswerResponse, status_code=status.HTTP_201_CREATED)
async def create_verified_answer(
    request: VerifiedAnswerCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_tenant: UUID = Depends(get_current_tenant),
) -> VerifiedAnswerResponse:
    """
    Create a new verified answer manually.
    
    This endpoint allows users to add Q&A pairs directly to the knowledge base
    without going through the HITL review queue.
    """
    try:
        # Verify bot exists and belongs to tenant
        bot_uuid = UUID(request.bot_id)
        bot_result = await db.execute(
            select(Bot).where(
                and_(Bot.id == bot_uuid, Bot.tenant_id == current_tenant)
            )
        )
        bot = bot_result.scalars().first()
        
        if not bot:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bot not found",
            )
        
        # Create the verified answer
        verified_answer = VerifiedAnswer(
            tenant_id=current_tenant,
            bot_id=bot_uuid,
            group_id=bot.group_id,
            question=request.question.strip(),
            answer=request.answer.strip(),
            created_by_user_id=current_user.id,
            is_active=True,
            metadata_json=request.metadata or {},
        )
        
        db.add(verified_answer)
        await db.commit()
        await db.refresh(verified_answer)
        
        logger.info(f"Created verified answer {verified_answer.id} for bot {bot_uuid}")
        
        return VerifiedAnswerResponse(
            id=str(verified_answer.id),
            bot_id=str(verified_answer.bot_id),
            bot_name=bot.name,
            question=verified_answer.question,
            answer=verified_answer.answer,
            is_active=verified_answer.is_active,
            created_at=verified_answer.created_at.isoformat(),
            updated_at=verified_answer.updated_at.isoformat(),
            created_by_name=current_user.display_name or current_user.email,
            metadata=verified_answer.metadata_json,
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating verified answer: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create verified answer",
        )


@router.get("/answers/{answer_id}", response_model=VerifiedAnswerResponse)
async def get_verified_answer(
    answer_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_tenant: UUID = Depends(get_current_tenant),
) -> VerifiedAnswerResponse:
    """Get a specific verified answer by ID."""
    try:
        answer_uuid = UUID(answer_id)
        
        result = await db.execute(
            select(VerifiedAnswer).where(
                and_(
                    VerifiedAnswer.id == answer_uuid,
                    VerifiedAnswer.tenant_id == current_tenant,
                )
            ).options(
                joinedload(VerifiedAnswer.bot),
                joinedload(VerifiedAnswer.created_by)
            )
        )
        item = result.unique().scalars().first()
        
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Verified answer not found",
            )
        
        bot_name = item.bot.name if item.bot else "Unknown Bot"
        created_by_name = None
        if item.created_by:
            created_by_name = item.created_by.display_name or item.created_by.email
        
        return VerifiedAnswerResponse(
            id=str(item.id),
            bot_id=str(item.bot_id),
            bot_name=bot_name,
            question=item.question,
            answer=item.answer,
            is_active=item.is_active,
            created_at=item.created_at.isoformat(),
            updated_at=item.updated_at.isoformat(),
            created_by_name=created_by_name,
            metadata=item.metadata_json,
        )
    
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid answer ID format",
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting verified answer: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get verified answer",
        )


@router.put("/answers/{answer_id}", response_model=VerifiedAnswerResponse)
async def update_verified_answer(
    answer_id: str,
    request: VerifiedAnswerUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_tenant: UUID = Depends(get_current_tenant),
) -> VerifiedAnswerResponse:
    """Update an existing verified answer."""
    try:
        answer_uuid = UUID(answer_id)
        
        result = await db.execute(
            select(VerifiedAnswer).where(
                and_(
                    VerifiedAnswer.id == answer_uuid,
                    VerifiedAnswer.tenant_id == current_tenant,
                )
            ).options(joinedload(VerifiedAnswer.bot))
        )
        item = result.unique().scalars().first()
        
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Verified answer not found",
            )
        
        # Apply updates
        if request.question is not None:
            item.question = request.question.strip()
        if request.answer is not None:
            item.answer = request.answer.strip()
        if request.is_active is not None:
            item.is_active = request.is_active
        if request.metadata is not None:
            item.metadata_json = request.metadata
        
        item.updated_by_user_id = current_user.id
        item.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(item)
        
        logger.info(f"Updated verified answer {answer_id}")
        
        bot_name = item.bot.name if item.bot else "Unknown Bot"
        
        return VerifiedAnswerResponse(
            id=str(item.id),
            bot_id=str(item.bot_id),
            bot_name=bot_name,
            question=item.question,
            answer=item.answer,
            is_active=item.is_active,
            created_at=item.created_at.isoformat(),
            updated_at=item.updated_at.isoformat(),
            created_by_name=None,
            metadata=item.metadata_json,
        )
    
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid answer ID format",
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating verified answer: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update verified answer",
        )


@router.delete("/answers/{answer_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_verified_answer(
    answer_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_tenant: UUID = Depends(get_current_tenant),
):
    """Delete a verified answer (soft delete by setting is_active=False)."""
    try:
        answer_uuid = UUID(answer_id)
        
        result = await db.execute(
            select(VerifiedAnswer).where(
                and_(
                    VerifiedAnswer.id == answer_uuid,
                    VerifiedAnswer.tenant_id == current_tenant,
                )
            )
        )
        item = result.scalars().first()
        
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Verified answer not found",
            )
        
        # Soft delete
        item.is_active = False
        item.updated_by_user_id = current_user.id
        item.updated_at = datetime.utcnow()
        
        await db.commit()
        
        logger.info(f"Soft deleted verified answer {answer_id}")
        
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid answer ID format",
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting verified answer: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete verified answer",
        )
