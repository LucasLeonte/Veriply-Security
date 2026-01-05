"""Review queue submission endpoint for low-confidence chat responses.

Allows the chat interface to submit low-confidence responses to the 
review queue for human review by customer service.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from uuid import UUID, uuid4
from typing import Optional, List
import logging
from pydantic import BaseModel, Field

from app.models.bot import Bot
from app.models.confidence_log import ConfidenceLog, RoutingDecision
from app.core.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/bots/{bot_id}/review-queue", tags=["review-queue"])


class ReviewQueueSubmissionRequest(BaseModel):
    """Request to submit a low-confidence response to review queue."""
    user_question: str = Field(..., description="Original user question")
    ai_draft: str = Field(..., description="AI-generated response")
    confidence: float = Field(..., ge=0, le=1, description="Confidence score (0-1)")
    citations: Optional[List[dict]] = Field(
        default_factory=list,
        description="Source citations for the response"
    )


@router.post("", status_code=status.HTTP_201_CREATED)
async def submit_to_review_queue(
    bot_id: UUID,
    request: ReviewQueueSubmissionRequest,
    session: AsyncSession = Depends(get_db),
):
    """
    Submit a low-confidence chat response to the review queue for human review.
    
    This endpoint is called automatically when a chat response has confidence 
    below 80% threshold. The response is queued for customer service review.
    
    **Request Body:**
    - `user_question`: The original question from the user
    - `ai_draft`: The AI-generated response
    - `confidence`: Confidence score between 0 and 1
    - `citations`: Optional list of source citations
    
    **Response:**
    - `success`: Whether the submission was successful
    - `message`: Confirmation message
    - `queue_item_id`: ID of the created review queue item
    """
    # Verify bot exists (best-effort for public chat submissions)
    bot = await session.scalar(select(Bot).where(Bot.id == bot_id))
    if not bot:
        # For public chat flows we don't want hard 404s to break UX or
        # spam logs; log and return a soft failure instead.
        logger.warning("Review queue submission for unknown bot_id=%s", bot_id)
        return {
            "success": False,
            "message": "Bot not found for review queue submission",
            "queue_item_id": None,
        }
    
    try:
        # Create a new confidence log entry for review
        confidence_log = ConfidenceLog(
            bot_id=bot_id,
            tenant_id=bot.tenant_id,
            query_id=uuid4(),  # Generate unique query ID
            query_text=request.user_question[:500] if request.user_question else None,  # Truncate to fit
            retrieval_confidence=request.confidence,  # Use submitted confidence as retrieval
            overall_confidence=request.confidence,
            threshold_used=0.8,  # Default threshold
            routing_decision=RoutingDecision.HITL,
            hitl_resolved=False,
            is_verified_kb=False,
            metadata_json={
                "type": "chat",
                "ai_draft": request.ai_draft,
                "citations": request.citations or [],
                "source": "chatbot_auto_submission",
            }
        )
        
        session.add(confidence_log)
        await session.commit()
        
        logger.info(f"Submitted low-confidence response to review queue: {confidence_log.id}")
        
        return {
            "success": True,
            "message": "Response submitted to review queue for customer service review",
            "queue_item_id": str(confidence_log.id),
        }
    
    except Exception as e:
        logger.error(f"Error submitting to review queue: {e}")
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to submit to review queue",
        )
