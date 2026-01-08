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
from app.core.database import get_db, set_tenant_context

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/bots/{bot_id}/review-queue", tags=["review-queue"])

# Patterns that indicate the bot doesn't know the answer
NO_ANSWER_PATTERNS = [
    "i don't have information",
    "i don't know",
    "i do not have information",
    "i do not know",
    "i'm not sure",
    "i am not sure",
    "i cannot find",
    "i can't find",
    "no information available",
    "not in the knowledge base",
    "checking with the team",
    "i'm checking with",
    "i am checking with",
    "you'll hear from us",
    "unable to answer",
    "cannot answer",
    "can't answer",
    "don't have enough information",
    "do not have enough information",
    "outside my knowledge",
    "beyond my knowledge",
    "not able to find",
]


def _check_no_answer_patterns(ai_draft: str) -> bool:
    """Check if the AI draft indicates the bot doesn't know the answer."""
    if not ai_draft:
        return True  # Empty draft means no answer
    
    draft_lower = ai_draft.lower()
    for pattern in NO_ANSWER_PATTERNS:
        if pattern in draft_lower:
            logger.debug(f"Detected 'no answer' pattern: '{pattern}'")
            return True
    return False


class ReviewQueueSubmissionRequest(BaseModel):
    """Request to submit a low-confidence response to review queue."""
    user_question: str = Field(..., description="Original user question")
    ai_draft: str = Field(..., description="AI-generated response")
    confidence: float = Field(..., ge=0, le=1, description="Confidence score (0-1)")
    citations: Optional[List[dict]] = Field(
        default_factory=list,
        description="Source citations for the response"
    )
    session_id: Optional[str] = Field(
        None,
        description="Chat session ID for sending approved answer back"
    )


# Placeholder messages that should be rejected - these don't contain real AI responses
PLACEHOLDER_MESSAGES = [
    "I'm checking with the team for the best answer",
    "You'll hear from us shortly",
    "checking with the team",
]


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
    - `ai_draft`: The AI-generated response (must be real AI response, not placeholder)
    - `confidence`: Confidence score between 0 and 1
    - `citations`: Optional list of source citations
    
    **Response:**
    - `success`: Whether the submission was successful
    - `message`: Confirmation message
    - `queue_item_id`: ID of the created review queue item
    
    **Note:** This endpoint rejects placeholder messages and duplicate submissions.
    The backend already creates review queue entries via calculate_confidence().
    """
    # GUARD: Reject placeholder messages - these are not real AI responses
    ai_draft_lower = (request.ai_draft or "").lower()
    for placeholder in PLACEHOLDER_MESSAGES:
        if placeholder.lower() in ai_draft_lower:
            logger.warning(
                "Rejected review queue submission with placeholder message for bot_id=%s", 
                bot_id
            )
            return {
                "success": False,
                "message": "Submission rejected: contains placeholder message, not actual AI response",
                "queue_item_id": None,
            }
    
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
        # Check for deduplication - don't create duplicate entries for same question
        existing = await session.execute(
            select(ConfidenceLog)
            .where(ConfidenceLog.bot_id == bot_id)
            .where(ConfidenceLog.query_text == (request.user_question[:500] if request.user_question else None))
            .where(ConfidenceLog.hitl_resolved == False)
            .limit(1)
        )
        if existing.scalar():
            logger.info(f"Duplicate review queue submission detected for bot_id={bot_id}, skipping")
            return {
                "success": True,
                "message": "Response already in review queue",
                "queue_item_id": None,
            }
        
        # Override confidence to 0 if the AI draft indicates it doesn't know the answer
        actual_confidence = request.confidence
        if _check_no_answer_patterns(request.ai_draft):
            logger.info("AI draft indicates no answer - setting confidence to 0")
            actual_confidence = 0.0
        
        # GUARD: Check for duplicate - if a ConfidenceLog already exists for this 
        # exact query_text and bot_id within the last 5 minutes, don't create another.
        # The backend's calculate_confidence() already creates the entry.
        from sqlalchemy import and_
        from datetime import datetime, timedelta
        
        recent_cutoff = datetime.utcnow() - timedelta(minutes=5)
        existing = await session.scalar(
            select(ConfidenceLog).where(
                and_(
                    ConfidenceLog.bot_id == bot_id,
                    ConfidenceLog.query_text == (request.user_question[:500] if request.user_question else None),
                    ConfidenceLog.created_at >= recent_cutoff,
                    ConfidenceLog.hitl_resolved == False,
                )
            ).order_by(ConfidenceLog.created_at.desc())
        )
        
        if existing:
            logger.info(
                "Skipping duplicate review queue submission for bot_id=%s, query='%s' - "
                "entry %s already exists",
                bot_id, request.user_question[:50], existing.id
            )
            return {
                "success": True,
                "message": "Entry already exists in review queue",
                "queue_item_id": str(existing.id),
            }
        
        # Create a new confidence log entry for review
        confidence_log = ConfidenceLog(
            bot_id=bot_id,
            tenant_id=bot.tenant_id,
            group_id=bot.group_id,  # Include group_id from bot for RLS
            query_id=uuid4(),  # Generate unique query ID
            query_text=request.user_question[:500] if request.user_question else None,  # Truncate to fit
            retrieval_confidence=actual_confidence,  # Use corrected confidence
            overall_confidence=actual_confidence,
            threshold_used=0.8,  # Default threshold
            routing_decision=RoutingDecision.hitl,
            hitl_resolved=False,
            is_verified_kb=False,
            metadata_json={
                "type": "chat",
                "ai_draft": request.ai_draft,
                "citations": request.citations or [],
                "source": "chatbot_auto_submission",
                "original_confidence": request.confidence,  # Keep original for debugging
                "session_id": request.session_id,  # For sending approved answer back to chat
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
        logger.error(f"Error submitting to review queue: {e}", exc_info=True)
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit to review queue: {str(e)}",
        )
