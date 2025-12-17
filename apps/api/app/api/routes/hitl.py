"""HITL (Human-In-The-Loop) Review Queue endpoints.

Provides access to questions routed to human review due to low confidence scores
from chatbots. This allows human reviewers to provide better answers for low
confidence responses.
"""

import logging
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, and_

from app.core.database import get_db
from app.api.v1.auth import get_current_user, get_current_tenant
from app.models.user import User
from app.models.confidence_log import ConfidenceLog, RoutingDecision
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/hitl", tags=["hitl"])


class ReviewQueueItemResponse(BaseModel):
    """Review queue item returned to frontend."""
    id: str = Field(..., description="Confidence log ID")
    type: str = Field(default="chat", description="Type of query (chat/email)")
    timestamp: str = Field(..., description="ISO timestamp of query")
    userQuestion: str = Field(..., description="Original user question")
    aiDraft: str = Field(..., description="AI-generated draft response")
    confidence: float = Field(..., description="Confidence score (0-100)")
    citations: List[dict] = Field(default_factory=list, description="Source citations")
    status: str = Field(default="pending", description="Review status")
    source: str = Field(default="chatbot", description="Source of the question")
    metadata: Optional[dict] = Field(default=None, description="Additional metadata")


class ReviewQueueStatsResponse(BaseModel):
    """Statistics about the review queue."""
    total: int = Field(..., description="Total items in queue")
    pending: int = Field(..., description="Pending review items")
    chat: int = Field(..., description="Chat-type items")
    email: int = Field(..., description="Email-type items")


class ReviewQueueResponse(BaseModel):
    """Complete review queue response."""
    items: List[ReviewQueueItemResponse]
    stats: ReviewQueueStatsResponse


@router.get("/queue", response_model=ReviewQueueResponse)
async def get_review_queue(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_tenant: str = Depends(get_current_tenant),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    sort_by: str = Query("newest", regex="^(newest|lowest_confidence|highest_confidence)$"),
) -> ReviewQueueResponse:
    """
    Get pending HITL review items for the current tenant.
    
    Returns questions with confidence scores below bot thresholds that need
    human review. Items are sorted by creation date (newest first) or confidence.
    """
    try:
        # Query pending HITL items for this tenant
        query_stmt = select(ConfidenceLog).where(
            and_(
                ConfidenceLog.routing_decision == RoutingDecision.HITL,
                ConfidenceLog.hitl_resolved == False,
                ConfidenceLog.tenant_id == UUID(current_tenant),
            )
        )

        # Sort based on parameter
        if sort_by == "lowest_confidence":
            query_stmt = query_stmt.order_by(ConfidenceLog.overall_confidence.asc())
        elif sort_by == "highest_confidence":
            query_stmt = query_stmt.order_by(ConfidenceLog.overall_confidence.desc())
        else:  # newest (default)
            query_stmt = query_stmt.order_by(desc(ConfidenceLog.created_at))

        # Execute query with pagination
        result = await db.execute(query_stmt)
        all_items = result.scalars().all()

        # Get stats
        total = len(all_items)
        paginated_items = all_items[offset : offset + limit]

        # Convert to response format
        items_response = []
        for item in paginated_items:
            # Determine type based on metadata or default to chat
            item_type = "chat"
            if item.metadata_json and isinstance(item.metadata_json, dict):
                item_type = item.metadata_json.get("type", "chat")

            # Parse citations from metadata if available
            citations = []
            if item.metadata_json and isinstance(item.metadata_json, dict):
                citations = item.metadata_json.get("citations", [])

            response_item = ReviewQueueItemResponse(
                id=str(item.id),
                type=item_type,
                timestamp=item.created_at.isoformat(),
                userQuestion=item.query_text or "Unknown question",
                aiDraft=item.metadata_json.get("ai_draft", "") if item.metadata_json else "",
                confidence=float(item.overall_confidence) * 100,  # Convert to percentage
                citations=citations,
                status="pending",
                source=item.metadata_json.get("source", "chatbot") if item.metadata_json else "chatbot",
                metadata={
                    "bot_id": str(item.bot_id),
                    "query_id": str(item.query_id),
                    "is_verified_kb": item.is_verified_kb,
                },
            )
            items_response.append(response_item)

        # Calculate type counts
        chat_count = sum(1 for item in items_response if item.type == "chat")
        email_count = sum(1 for item in items_response if item.type == "email")

        stats = ReviewQueueStatsResponse(
            total=total,
            pending=total,
            chat=chat_count,
            email=email_count,
        )

        return ReviewQueueResponse(items=items_response, stats=stats)

    except ValueError as e:
        logger.error(f"Invalid tenant ID: {current_tenant}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid tenant")
    except Exception as e:
        logger.error(f"Error fetching HITL queue: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch review queue",
        )


@router.post("/queue/{item_id}/approve")
async def approve_queue_item(
    item_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_tenant: str = Depends(get_current_tenant),
    edits: Optional[str] = None,
):
    """
    Approve a review queue item (mark as resolved by human).
    Optionally accept edits to the AI draft.
    """
    try:
        item_uuid = UUID(item_id)
        
        # Find the item
        result = await db.execute(
            select(ConfidenceLog).where(
                and_(
                    ConfidenceLog.id == item_uuid,
                    ConfidenceLog.tenant_id == UUID(current_tenant),
                )
            )
        )
        item = result.scalars().first()

        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Item not found",
            )

        # Mark as resolved
        item.hitl_resolved = True
        item.resolution_user_id = current_user.id
        item.resolution_timestamp = __import__('datetime').datetime.utcnow()

        # Store edits in metadata if provided
        if edits:
            if not item.metadata_json:
                item.metadata_json = {}
            item.metadata_json["human_edits"] = edits
            item.metadata_json["resolution_action"] = "approved_with_edits"
        else:
            if not item.metadata_json:
                item.metadata_json = {}
            item.metadata_json["resolution_action"] = "approved"

        await db.commit()

        return {"status": "approved", "item_id": item_id}

    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid item ID",
        )
    except Exception as e:
        logger.error(f"Error approving item {item_id}: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to approve item",
        )


@router.post("/queue/{item_id}/reject")
async def reject_queue_item(
    item_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_tenant: str = Depends(get_current_tenant),
    reason: Optional[str] = None,
):
    """
    Reject a review queue item (mark as resolved with rejection).
    Optionally provide a reason for rejection.
    """
    try:
        item_uuid = UUID(item_id)
        
        # Find the item
        result = await db.execute(
            select(ConfidenceLog).where(
                and_(
                    ConfidenceLog.id == item_uuid,
                    ConfidenceLog.tenant_id == UUID(current_tenant),
                )
            )
        )
        item = result.scalars().first()

        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Item not found",
            )

        # Mark as resolved
        item.hitl_resolved = True
        item.resolution_user_id = current_user.id
        item.resolution_timestamp = __import__('datetime').datetime.utcnow()

        # Store rejection reason
        if not item.metadata_json:
            item.metadata_json = {}
        item.metadata_json["resolution_action"] = "rejected"
        if reason:
            item.metadata_json["rejection_reason"] = reason

        await db.commit()

        return {"status": "rejected", "item_id": item_id}

    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid item ID",
        )
    except Exception as e:
        logger.error(f"Error rejecting item {item_id}: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reject item",
        )
