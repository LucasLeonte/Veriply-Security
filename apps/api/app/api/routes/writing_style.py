"""API endpoints for writing style management."""

import logging
from uuid import UUID
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.core.security import get_current_user
from app.core.database import get_db
from app.models.user_writing_style import UserWritingStyle
from app.models.user import User
from app.models.email_integration import EmailIntegration
from app.workers.style_analyzer_worker import StyleAnalysisWorker
from app.schemas import BaseModel

router = APIRouter(prefix="/api/v1/writing-style", tags=["writing-style"])

logger = logging.getLogger(__name__)


class StyleProfileResponse(BaseModel):
    """Response schema for style profile."""
    id: str
    integration_id: str
    integration_provider: str
    tone: str
    formality_score: int
    greeting_pattern: Optional[str]
    closing_pattern: Optional[str]
    avg_email_length: Optional[int]
    avg_sentence_length: Optional[int]
    uses_emojis: bool
    sample_count: int
    is_manual_override: bool
    last_analyzed_at: Optional[str]
    custom_preferences: Optional[dict]


class StylePreferencesUpdate(BaseModel):
    """Schema for updating style preferences."""
    tone: Optional[str] = None
    greeting_pattern: Optional[str] = None
    closing_pattern: Optional[str] = None
    formality_score: Optional[int] = None
    uses_emojis: Optional[bool] = None
    custom_preferences: Optional[dict] = None


class AllStylesResponse(BaseModel):
    """Response schema for all styles."""
    styles: List[StyleProfileResponse]


@router.get("", response_model=AllStylesResponse)
async def get_all_writing_styles(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AllStylesResponse:
    """Get all writing style profiles for current user.
    
    Returns style profile for each connected email account.
    """
    stmt = select(UserWritingStyle).where(
        UserWritingStyle.user_id == current_user.id
    )
    result = await db.execute(stmt)
    styles = result.scalars().all()
    
    # Fetch integration details for each style
    responses = []
    for style in styles:
        integration_stmt = select(EmailIntegration).where(
            EmailIntegration.id == style.integration_id
        )
        integration_result = await db.execute(integration_stmt)
        integration = integration_result.scalar()
        
        responses.append(StyleProfileResponse(
            id=str(style.id),
            integration_id=str(style.integration_id),
            integration_provider=integration.provider if integration else "unknown",
            tone=style.tone,
            formality_score=style.formality_score,
            greeting_pattern=style.greeting_pattern,
            closing_pattern=style.closing_pattern,
            avg_email_length=style.avg_email_length,
            avg_sentence_length=style.avg_sentence_length,
            uses_emojis=style.uses_emojis,
            sample_count=style.sample_count,
            is_manual_override=style.is_manual_override,
            last_analyzed_at=style.last_analyzed_at.isoformat() if style.last_analyzed_at else None,
            custom_preferences=style.custom_preferences,
        ))
    
    return AllStylesResponse(styles=responses)


@router.get("/{integration_id}", response_model=StyleProfileResponse)
async def get_writing_style(
    integration_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> StyleProfileResponse:
    """Get writing style profile for specific email integration."""
    try:
        integration_uuid = UUID(integration_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid integration ID")
    
    stmt = select(UserWritingStyle).where(
        and_(
            UserWritingStyle.user_id == current_user.id,
            UserWritingStyle.integration_id == integration_uuid,
        )
    )
    result = await db.execute(stmt)
    style = result.scalar()
    
    if not style:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Style profile not found"
        )
    
    # Get integration details
    integration_stmt = select(EmailIntegration).where(
        EmailIntegration.id == style.integration_id
    )
    integration_result = await db.execute(integration_stmt)
    integration = integration_result.scalar()
    
    return StyleProfileResponse(
        id=str(style.id),
        integration_id=str(style.integration_id),
        integration_provider=integration.provider if integration else "unknown",
        tone=style.tone,
        formality_score=style.formality_score,
        greeting_pattern=style.greeting_pattern,
        closing_pattern=style.closing_pattern,
        avg_email_length=style.avg_email_length,
        avg_sentence_length=style.avg_sentence_length,
        uses_emojis=style.uses_emojis,
        sample_count=style.sample_count,
        is_manual_override=style.is_manual_override,
        last_analyzed_at=style.last_analyzed_at.isoformat() if style.last_analyzed_at else None,
        custom_preferences=style.custom_preferences,
    )


@router.put("/{integration_id}", response_model=StyleProfileResponse)
async def update_writing_style(
    integration_id: str,
    preferences: StylePreferencesUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> StyleProfileResponse:
    """Update writing style preferences.
    
    Allows manual override of auto-detected style.
    """
    try:
        integration_uuid = UUID(integration_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid integration ID")
    
    stmt = select(UserWritingStyle).where(
        and_(
            UserWritingStyle.user_id == current_user.id,
            UserWritingStyle.integration_id == integration_uuid,
        )
    )
    result = await db.execute(stmt)
    style = result.scalar()
    
    if not style:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Style profile not found"
        )
    
    # Update fields
    if preferences.tone:
        style.tone = preferences.tone
    if preferences.greeting_pattern:
        style.greeting_pattern = preferences.greeting_pattern
    if preferences.closing_pattern:
        style.closing_pattern = preferences.closing_pattern
    if preferences.formality_score is not None:
        style.formality_score = preferences.formality_score
    if preferences.uses_emojis is not None:
        style.uses_emojis = preferences.uses_emojis
    if preferences.custom_preferences:
        style.custom_preferences = preferences.custom_preferences
    
    # Mark as manual override
    style.is_manual_override = True
    
    await db.commit()
    await db.refresh(style)
    
    # Get integration details
    integration_stmt = select(EmailIntegration).where(
        EmailIntegration.id == style.integration_id
    )
    integration_result = await db.execute(integration_stmt)
    integration = integration_result.scalar()
    
    logger.info(f"Updated writing style for user {current_user.id}, integration {integration_id}")
    
    return StyleProfileResponse(
        id=str(style.id),
        integration_id=str(style.integration_id),
        integration_provider=integration.provider if integration else "unknown",
        tone=style.tone,
        formality_score=style.formality_score,
        greeting_pattern=style.greeting_pattern,
        closing_pattern=style.closing_pattern,
        avg_email_length=style.avg_email_length,
        avg_sentence_length=style.avg_sentence_length,
        uses_emojis=style.uses_emojis,
        sample_count=style.sample_count,
        is_manual_override=style.is_manual_override,
        last_analyzed_at=style.last_analyzed_at.isoformat() if style.last_analyzed_at else None,
        custom_preferences=style.custom_preferences,
    )


@router.post("/{integration_id}/refresh", response_model=StyleProfileResponse)
async def refresh_writing_style(
    integration_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> StyleProfileResponse:
    """Refresh writing style by re-analyzing emails.
    
    Fetches new sent emails and updates style profile.
    """
    try:
        integration_uuid = UUID(integration_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid integration ID")
    
    # Verify integration belongs to user
    integration_stmt = select(EmailIntegration).where(
        and_(
            EmailIntegration.id == integration_uuid,
            EmailIntegration.user_id == current_user.id,
        )
    )
    integration_result = await db.execute(integration_stmt)
    integration = integration_result.scalar()
    
    if not integration:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Email integration not found"
        )
    
    try:
        # Run style analysis
        from app.core.config import settings
        
        worker = StyleAnalysisWorker(
            settings.OAUTH_CLIENT_ID,
            settings.OAUTH_CLIENT_SECRET
        )
        
        style = await worker.refresh_user_style(
            db=db,
            tenant_id=current_user.tenant_id,
            user_id=current_user.id,
            integration_id=integration_uuid,
            fetch_new_emails=True
        )
        
        if not style:
            raise HTTPException(
                status_code=500,
                detail="Failed to analyze style"
            )
        
        logger.info(f"Refreshed writing style for user {current_user.id}, integration {integration_id}")
        
        return StyleProfileResponse(
            id=str(style.id),
            integration_id=str(style.integration_id),
            integration_provider=integration.provider,
            tone=style.tone,
            formality_score=style.formality_score,
            greeting_pattern=style.greeting_pattern,
            closing_pattern=style.closing_pattern,
            avg_email_length=style.avg_email_length,
            avg_sentence_length=style.avg_sentence_length,
            uses_emojis=style.uses_emojis,
            sample_count=style.sample_count,
            is_manual_override=style.is_manual_override,
            last_analyzed_at=style.last_analyzed_at.isoformat() if style.last_analyzed_at else None,
            custom_preferences=style.custom_preferences,
        )
    
    except Exception as e:
        logger.exception(f"Error refreshing style: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to refresh writing style"
        )


@router.delete("/{integration_id}/override")
async def reset_writing_style_override(
    integration_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Reset writing style to auto-detected profile.
    
    Removes manual overrides and re-enables auto-detection.
    """
    try:
        integration_uuid = UUID(integration_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid integration ID")
    
    stmt = select(UserWritingStyle).where(
        and_(
            UserWritingStyle.user_id == current_user.id,
            UserWritingStyle.integration_id == integration_uuid,
        )
    )
    result = await db.execute(stmt)
    style = result.scalar()
    
    if not style:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Style profile not found"
        )
    
    # Reset to auto-detected
    style.is_manual_override = False
    style.custom_preferences = {}
    
    await db.commit()
    
    logger.info(f"Reset writing style override for user {current_user.id}, integration {integration_id}")
    
    return {"message": "Style reset to auto-detected"}
