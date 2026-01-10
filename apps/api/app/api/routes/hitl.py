"""HITL (Human-In-The-Loop) Review Queue endpoints.

Provides access to questions routed to human review due to low confidence scores
from chatbots. This allows human reviewers to provide better answers for low
confidence responses.
"""

import logging
import json
import asyncio
from typing import List, Optional, Set, Dict
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Query, WebSocket, WebSocketDisconnect, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, and_, join
from sqlalchemy.orm import joinedload
import redis.asyncio as redis
from sqlalchemy.orm import joinedload
import redis.asyncio as aioredis

from app.core.database import get_db, set_tenant_context
from app.core.settings import settings
from app.api.v1.auth import get_current_user, get_current_tenant
from app.models.user import User
from app.models.confidence_log import ConfidenceLog, RoutingDecision
from app.models.bot import Bot
from app.models.bot import Bot
from app.services.embedding_service import EmbeddingService, EmbeddingError
from app.services.verified_qa import create_verified_qa
from app.services.document_service import create_document
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class ApproveQueueItemRequest(BaseModel):
    """Request to approve a review queue item."""
    edits: Optional[str] = Field(None, description="Optional edited response text")
    send_to_chat: bool = Field(True, description="Send approved answer back to chat")
    add_to_kb: bool = Field(True, description="Whether to add the approved answer to the Knowledge Base")


class RejectQueueItemRequest(BaseModel):
    """Request to reject a review queue item."""
    reason: Optional[str] = Field(None, description="Optional rejection reason")

router = APIRouter(prefix="/api/v1/hitl", tags=["hitl"])


class ReviewQueueItemResponse(BaseModel):
    """Review queue item returned to frontend."""
    id: str = Field(..., description="Confidence log ID")
    type: str = Field(default="chat", description="Type of query (chat/email)")
    timestamp: str = Field(..., description="ISO timestamp of query")
    userQuestion: str = Field(..., description="Original user question")
    aiDraft: str = Field(..., description="AI-generated draft response")
    botName: str = Field(..., description="Name of the bot that generated the response")
    botName: str = Field(..., description="Name of the bot that generated the response")
    # Confidence is stored in the DB as a 0-1 float; keep the
    # API contract aligned so the frontend can render a % view
    # with a simple *100, matching the live chat certainty bar.
    confidence: float = Field(..., description="Confidence score (0-1)")
    citations: List[dict] = Field(default_factory=list, description="Source citations")
    status: str = Field(default="pending", description="Review status")
    source: str = Field(default="chatbot", description="Source of the question")
    metadata: Optional[dict] = Field(default=None, description="Additional metadata")


class ContextChunk(BaseModel):
    """Context chunk with source document information."""
    chunk_id: str = Field(..., description="Unique chunk identifier")
    document_id: str = Field(..., description="Source document ID")
    document_name: str = Field(..., description="Source document name")
    section: Optional[str] = Field(None, description="Document section")
    text: str = Field(..., description="Chunk text content")
    similarity: float = Field(..., description="Similarity score (0-1)")
    page_number: Optional[int] = Field(None, description="Page number if available")


class ReviewQueueItemDetailResponse(BaseModel):
    """Detailed review queue item with context chunks."""
    id: str = Field(..., description="Confidence log ID")
    type: str = Field(default="chat", description="Type of query (chat/email)")
    timestamp: str = Field(..., description="ISO timestamp of query")
    userQuestion: str = Field(..., description="Original user question")
    aiDraft: str = Field(..., description="AI-generated draft response")
    botName: str = Field(..., description="Name of the bot that generated the response")
    confidence: float = Field(..., description="Confidence score (0-1)")
    citations: List[dict] = Field(default_factory=list, description="Source citations")
    contextChunks: List[ContextChunk] = Field(default_factory=list, description="Retrieved context chunks")
    status: str = Field(default="pending", description="Review status")
    source: str = Field(default="chatbot", description="Source of the question")
    timeInQueue: str = Field(..., description="Time waiting in queue (human readable)")
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


class BotFilterOption(BaseModel):
    """Bot option for filter dropdown."""
    id: str = Field(..., description="Bot UUID")
    name: str = Field(..., description="Bot name")


class BotFilterOptionsResponse(BaseModel):
    """Response with bot filter options."""
    bots: List[BotFilterOption]


@router.get("/bots", response_model=BotFilterOptionsResponse)
async def get_bots_for_filter(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_tenant: UUID = Depends(get_current_tenant),
    group_id: Optional[UUID] = Query(None, description="Filter to bots in specific group (group-scoped)"),
) -> BotFilterOptionsResponse:
    """
    Get list of bots for filter dropdown (AC 5.5).
    
    If group_id is provided, returns only bots from that group.
    Otherwise, returns all bots accessible to the current user across all their groups.
    
    Security: Only returns bots from groups the user has access to.
    """
    try:
        # SECURITY: Set RLS context for tenant isolation
        await set_tenant_context(db, current_user.tenant_id)

        from app.models import GroupMember
        
        # If group_id is specified, verify user has access to that group
        if group_id:
            membership_result = await db.execute(
                select(GroupMember).where(
                    and_(
                        GroupMember.group_id == group_id,
                        GroupMember.user_id == current_user.id,
                    )
                )
            )
            if not membership_result.scalars().first():
                # User doesn't have access to this group - return empty results
                logger.warning(
                    f"Access denied: User {current_user.id} attempted to filter bots "
                    f"by group {group_id} without membership"
                )
                return BotFilterOptionsResponse(bots=[])
            
            # Get bots from specific group
            query_stmt = select(Bot).where(
                and_(
                    Bot.group_id == group_id,
                    Bot.tenant_id == current_tenant,
                )
            ).order_by(Bot.name)
        else:
            # Get all bots from groups the user has access to
            query_stmt = select(Bot).join(
                GroupMember, Bot.group_id == GroupMember.group_id
            ).where(
                and_(
                    GroupMember.user_id == current_user.id,
                    Bot.tenant_id == current_tenant,
                )
            ).distinct().order_by(Bot.name)
        
        result = await db.execute(query_stmt)
        bots = result.scalars().all()
        
        return BotFilterOptionsResponse(
            bots=[
                BotFilterOption(id=str(bot.id), name=bot.name)
                for bot in bots
            ]
        )
    except Exception as e:
        logger.exception(f"Error fetching bots for filter: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch bots for filter"
        )


@router.get("/queue", response_model=ReviewQueueResponse)
async def get_review_queue(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_tenant: UUID = Depends(get_current_tenant),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    sort_by: str = Query("oldest", regex="^(oldest|newest|lowest_confidence|highest_confidence)$"),
    group_id: Optional[UUID] = Query(None, description="Filter to specific group (group-scoped review queue)"),
    bot_id: Optional[UUID] = Query(None, description="Filter by specific bot ID"),
    date_from: Optional[datetime] = Query(None, description="Filter items created on or after this date"),
    date_to: Optional[datetime] = Query(None, description="Filter items created on or before this date"),
    status_filter: Optional[str] = Query(None, regex="^(pending|in-progress)$", description="Filter by status (pending, in-progress)"),
) -> ReviewQueueResponse:
    """
    Get pending HITL review items for the current tenant.
    
    Returns questions with confidence scores below bot thresholds that need
    human review. Items are filtered by tenant, user's group memberships, and
    optionally by a specific group_id to scope to that group only.
    
    Items are sorted by creation date (oldest first by default) or confidence.
    
    Sorting options:
    - oldest: oldest items first (default, per AC requirement)
    - newest: newest items first
    - lowest_confidence: lowest confidence scores first
    - highest_confidence: highest confidence scores first
    
    Filtering options (AC 5.5 + group-scoping):
    - group_id: Filter to items from specific group (enforces group-scoped queue)
    - bot_id: Filter by specific bot UUID
    - date_from/date_to: Filter by date range
    - status_filter: Filter by status (pending, in-progress)
    
    Security: Only returns items from groups the user has access to.
    If group_id is specified, verifies user has GroupMember access before filtering.
    """
    try:
        # Ensure RLS context is set for this connection
        await set_tenant_context(db, current_tenant)
        
        # CRITICAL: Commit any pending transaction and start fresh
        # to ensure we see the latest committed data (especially after recent rejections/approvals)
        await db.commit()
        
        # Get user's group memberships to filter by accessible groups
        from app.models import GroupMember
        from sqlalchemy import func
        
        # Subquery to get group IDs user has access to
        user_groups_subquery = select(GroupMember.group_id).where(
            GroupMember.user_id == current_user.id
        ).subquery()
        
        # Query pending HITL items for this tenant, filtered by user's accessible groups
        # Items with null group_id (tenant-wide) OR items from groups the user belongs to
        query_stmt = select(ConfidenceLog).where(
            and_(
                ConfidenceLog.routing_decision == RoutingDecision.hitl,
                ConfidenceLog.hitl_resolved.is_(False),
                ConfidenceLog.tenant_id == current_tenant,
            )
        ).where(
            # Items with null group_id (tenant-wide) OR items from user's groups
            (ConfidenceLog.group_id.is_(None)) | 
            (ConfidenceLog.group_id.in_(
                select(GroupMember.group_id).where(GroupMember.user_id == current_user.id)
            ))
        ).options(joinedload(ConfidenceLog.bot))

        # Apply filters (AC 5.5)
        if group_id:
            # SECURITY: Verify user has access to the specified group
            from app.models.group_member import GroupMember
            membership_result = await db.execute(
                select(GroupMember).where(
                    and_(
                        GroupMember.group_id == group_id,
                        GroupMember.user_id == current_user.id,
                    )
                )
            )
            if not membership_result.scalars().first():
                # User doesn't have access to this group - return empty results
                logger.warning(
                    f"Access denied: User {current_user.id} attempted to filter HITL queue "
                    f"by group {group_id} without membership"
                )
                return ReviewQueueResponse(items=[], stats=ReviewQueueStatsResponse(total=0, pending=0, chat=0, email=0))
            # Filter to specific group
            query_stmt = query_stmt.where(ConfidenceLog.group_id == group_id)
        
        if bot_id:
            query_stmt = query_stmt.where(ConfidenceLog.bot_id == bot_id)
        
        if date_from:
            query_stmt = query_stmt.where(ConfidenceLog.created_at >= date_from)
        
        if date_to:
            query_stmt = query_stmt.where(ConfidenceLog.created_at <= date_to)
        
        # Status filter: 'pending' = hitl_resolved=False, 'in-progress' could use metadata
        # For now, all items in queue are 'pending' by default; future enhancement for 'in-progress'
        if status_filter == "in-progress":
            # Filter for items marked as in-progress (e.g., via metadata)
            # This is a placeholder; adjust based on how in-progress is tracked
            pass  # Could filter by metadata.status == "in-progress" if stored


        # Sort based on parameter (oldest first by default per AC1)
        if sort_by == "lowest_confidence":
            query_stmt = query_stmt.order_by(ConfidenceLog.overall_confidence.asc())
        elif sort_by == "highest_confidence":
            query_stmt = query_stmt.order_by(ConfidenceLog.overall_confidence.desc())
        elif sort_by == "newest":
            query_stmt = query_stmt.order_by(desc(ConfidenceLog.created_at))
        else:  # oldest (default)
            query_stmt = query_stmt.order_by(ConfidenceLog.created_at.asc())

        # Execute query with pagination
        result = await db.execute(query_stmt)
        all_items = result.unique().scalars().all()

        # Get stats from ALL items (not paginated)
        total = len(all_items)
        
        # Calculate type counts from ALL items before pagination
        all_chat_count = 0
        all_email_count = 0
        for item in all_items:
            raw_metadata = getattr(item, "metadata_json", None) or getattr(item, "metadata", None)
            metadata = raw_metadata or {}
            if isinstance(metadata, str):
                try:
                    metadata = json.loads(metadata)
                except Exception:
                    metadata = {}
            if not isinstance(metadata, dict):
                metadata = {}
            item_type = metadata.get("type", "chat")
            if item_type == "chat":
                all_chat_count += 1
            elif item_type == "email":
                all_email_count += 1
        
        paginated_items = all_items[offset : offset + limit]

        # Convert to response format
        items_response = []
        for item in paginated_items:
            # Normalize metadata payload (support legacy "metadata" column and strings)
            raw_metadata = getattr(item, "metadata_json", None) or getattr(item, "metadata", None)
            metadata = raw_metadata or {}
            if isinstance(metadata, str):
                try:
                    metadata = json.loads(metadata)
                except Exception:
                    metadata = {}
            if not isinstance(metadata, dict):
                metadata = {}

            # Determine type based on metadata or default to chat
            item_type = metadata.get("type", "chat")

            # Parse citations from metadata if available
            citations = metadata.get("citations", []) if isinstance(metadata.get("citations"), list) else []

            # Get bot name (with fallback if relationship not loaded)
            bot_name = "Unknown Bot"
            if hasattr(item, 'bot') and item.bot:
                bot_name = item.bot.name
            else:
                # Fallback: use metadata if bot relationship not loaded
                bot_name = metadata.get("bot_name", "Unknown Bot")

            # CRITICAL: Log to debug why resolved items might appear in response
            if item.hitl_resolved:
                logger.warning(
                    f"CRITICAL BUG: Returning resolved item in queue! "
                    f"item_id={item.id}, hitl_resolved={item.hitl_resolved}, "
                    f"resolution_action={metadata.get('resolution_action')}, "
                    f"created_at={item.created_at}"
                )

            response_item = ReviewQueueItemResponse(
                id=str(item.id),
                type=item_type,
                timestamp=item.created_at.isoformat(),
                userQuestion=item.query_text or "Unknown question",
                aiDraft=metadata.get("ai_draft", ""),
                botName=bot_name,
                # Keep confidence on a 0-1 scale so the Review Queue UI
                # displays the same certainty value as the live chat
                # bar (which multiplies by 100 for display only).
                confidence=float(item.overall_confidence),
                citations=citations,
                status="pending",
                source=metadata.get("source", "chatbot"),
                metadata={
                    "bot_id": str(item.bot_id),
                    "query_id": str(item.query_id),
                    "is_verified_kb": item.is_verified_kb,
                    "session_id": metadata.get("session_id"),  # For sending approved answer back to chat
                    "resolution_action": metadata.get("resolution_action"),  # Include resolution action so frontend can filter
                },
            )
            items_response.append(response_item)

        # Use pre-calculated stats from ALL items (not just paginated ones)
        stats = ReviewQueueStatsResponse(
            total=total,
            pending=total,
            chat=all_chat_count,
            email=all_email_count,
        )

        return ReviewQueueResponse(items=items_response, stats=stats)

    except Exception as e:
        logger.error(f"Error fetching HITL queue: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch review queue",
        )


@router.get("/queue/{item_id}", response_model=ReviewQueueItemDetailResponse)
async def get_queue_item_detail(
    item_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_tenant: UUID = Depends(get_current_tenant),
) -> ReviewQueueItemDetailResponse:
    """
    Get detailed information about a specific HITL queue item.
    
    Returns full context chunks with source documents for review interface.
    This endpoint supports AC1 (split view with query + context + draft).
    
    Security: Enforces tenant_id AND group_id access control with membership validation.
    """
    try:
        item_uuid = UUID(item_id)
        
        # Import GroupMember for access control
        from app.models.group_member import GroupMember
        
        # Query the specific item with Bot relationship loaded
        result = await db.execute(
            select(ConfidenceLog).where(
                and_(
                    ConfidenceLog.id == item_uuid,
                    ConfidenceLog.tenant_id == current_tenant,
                    ConfidenceLog.routing_decision == RoutingDecision.hitl,
                )
            ).options(joinedload(ConfidenceLog.bot))
        )
        item = result.scalars().first()
        
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Item not found",
            )
        
        # SECURITY: Verify user has access to the group this item belongs to
        if item.group_id:
            membership_result = await db.execute(
                select(GroupMember).where(
                    and_(
                        GroupMember.group_id == item.group_id,
                        GroupMember.user_id == current_user.id,
                    )
                )
            )
            membership = membership_result.scalars().first()
            
            if not membership:
                logger.warning(
                    f"Access denied: User {current_user.id} attempted to access "
                    f"HITL item {item_id} from group {item.group_id} without membership"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied: You do not have access to this item",
                )
        
        # Parse metadata
        raw_metadata = getattr(item, "metadata_json", None) or {}
        if isinstance(raw_metadata, str):
            try:
                raw_metadata = json.loads(raw_metadata)
            except Exception:
                raw_metadata = {}
        metadata = raw_metadata if isinstance(raw_metadata, dict) else {}
        
        # Extract context chunks from metadata
        context_chunks = []
        search_results = metadata.get("search_results", [])
        if isinstance(search_results, list):
            for chunk_data in search_results:
                if isinstance(chunk_data, dict):
                    context_chunks.append(ContextChunk(
                        chunk_id=chunk_data.get("chunk_id", ""),
                        document_id=chunk_data.get("document_id", ""),
                        document_name=chunk_data.get("document_name", "Unknown"),
                        section=chunk_data.get("section"),
                        text=chunk_data.get("text", ""),
                        similarity=float(chunk_data.get("similarity", 0.0)),
                        page_number=chunk_data.get("page_number"),
                    ))
        
        # Get citations
        citations = metadata.get("citations", [])
        if not isinstance(citations, list):
            citations = []
        
        # Get bot name
        bot_name = "Unknown Bot"
        if hasattr(item, 'bot') and item.bot:
            bot_name = item.bot.name
        else:
            bot_name = metadata.get("bot_name", "Unknown Bot")
        
        # Calculate time in queue
        time_diff = datetime.utcnow() - item.created_at
        minutes = int(time_diff.total_seconds() / 60)
        if minutes < 1:
            time_in_queue = "just now"
        elif minutes < 60:
            time_in_queue = f"{minutes}m"
        elif minutes < 1440:  # Less than 24 hours
            hours = minutes // 60
            time_in_queue = f"{hours}h"
        else:
            days = minutes // 1440
            time_in_queue = f"{days}d"
        
        return ReviewQueueItemDetailResponse(
            id=str(item.id),
            type=metadata.get("type", "chat"),
            timestamp=item.created_at.isoformat(),
            userQuestion=item.query_text or "Unknown question",
            aiDraft=metadata.get("ai_draft", ""),
            botName=bot_name,
            confidence=float(item.overall_confidence),
            citations=citations,
            contextChunks=context_chunks,
            status="pending" if not item.hitl_resolved else "resolved",
            source=metadata.get("source", "chatbot"),
            timeInQueue=time_in_queue,
            metadata={
                "bot_id": str(item.bot_id),
                "query_id": str(item.query_id),
                "is_verified_kb": item.is_verified_kb,
            },
        )
    
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid item ID",
        )
    except Exception as e:
        logger.error(f"Error fetching queue item detail: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch item detail",
        )


@router.post("/queue/{item_id}/approve")
async def approve_queue_item(
    item_id: str,
    request: ApproveQueueItemRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_tenant: UUID = Depends(get_current_tenant),
):
    """
    Approve a review queue item with atomic operations:
    1. Send response to end-user (future: email/chat integration)
    2. Update Verified Knowledge Base
    3. Remove item from queue (mark as resolved)
    4. Record diff between AI draft and human edit (if edited)
    
    Optionally accept edits to the AI draft.
    Publishes event to Redis for real-time updates.
    
    **AC1**: Response is sent, Q&A added to Verified KB, item removed from queue
    **AC2**: If edited, system records diff between AI and human version
    """
    try:
        # Ensure RLS / tenant isolation is set for this connection before any writes
        await set_tenant_context(db, current_user.tenant_id)

        item_uuid = UUID(item_id)
        
        logger.debug(f"Approving HITL item {item_id} by user {current_user.id}")
        
        # Find the item
        result = await db.execute(
            select(ConfidenceLog).where(
                and_(
                    ConfidenceLog.id == item_uuid,
                    ConfidenceLog.tenant_id == current_tenant,
                )
            )
        )
        item = result.scalars().first()

        if not item:
            logger.warning(f"HITL item {item_id} not found for tenant {current_tenant}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Item not found",
            )

        logger.debug(f"Found HITL item: {item.id}, currently resolved={item.hitl_resolved}")
        
        # SECURITY: Check if item is already resolved (optimistic locking)
        if item.hitl_resolved:
            logger.warning(
                f"Race condition prevented: Item {item_id} already resolved by user "
                f"{item.resolution_user_id} at {item.resolution_timestamp}"
            )
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Item has already been resolved by another user",
            )
        
        # SECURITY: Verify user has access to the group this item belongs to
        if item.group_id:
            from app.models.group_member import GroupMember
            membership_result = await db.execute(
                select(GroupMember).where(
                    and_(
                        GroupMember.group_id == item.group_id,
                        GroupMember.user_id == current_user.id,
                    )
                )
            )
            membership = membership_result.scalars().first()
            
            if not membership:
                logger.warning(
                    f"Access denied: User {current_user.id} attempted to approve "
                    f"HITL item {item_id} from group {item.group_id} without membership"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied: You do not have access to this item",
                )

        # Extract question and prepare answer for Verified KB
        question_text = item.query_text or ""
        metadata = dict(item.metadata_json or {})
        ai_draft = metadata.get("ai_draft", "")
        
        # Determine final answer and track if edited
        was_edited = False
        diff_result = None
        final_answer = ai_draft
        
        if request.edits and request.edits != ai_draft:
            was_edited = True
            final_answer = request.edits
            
            # AC2: Record diff between AI draft and human edit
            diff_result = {
                "ai_version": ai_draft,
                "human_version": request.edits,
                "edited_by": str(current_user.id),
                "edited_at": datetime.utcnow().isoformat(),
                # Calculate character-level changes for analytics
                "char_diff": {
                    "ai_length": len(ai_draft),
                    "human_length": len(request.edits),
                    "diff_length": len(request.edits) - len(ai_draft),
                }
            }
            
            metadata["diff"] = diff_result
            # SECURITY: Sanitize edited draft (basic validation)
            # Strip leading/trailing whitespace and limit length
            sanitized_edits = request.edits.strip()
            if len(sanitized_edits) > 10000:  # Reasonable limit for draft responses
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Edited draft exceeds maximum length of 10000 characters",
                )
            if not sanitized_edits:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Edited draft cannot be empty",
                )
            metadata["human_edits"] = sanitized_edits
            metadata["human_final_answer"] = sanitized_edits
            metadata["resolution_action"] = "approved_with_edits"
            logger.info(f"Approval with edits for item {item_id} - AI:{len(ai_draft)} chars → Human:{len(request.edits)} chars")
        else:
            # Default to AI draft as the approved answer if no edits supplied
            ai_draft = metadata.get("ai_draft", "")
            metadata["human_final_answer"] = ai_draft
            metadata["resolution_action"] = "approved"
            logger.debug("Approval without edits - using AI draft")

        item.metadata_json = metadata

        # Mark item as resolved BEFORE creating VerifiedQA (which needs resolution timestamp)
        item.hitl_resolved = True
        item.resolution_user_id = current_user.id
        item.resolution_timestamp = __import__('datetime').datetime.utcnow()

        # Prepare the approved answer and citations for storage
        approved_answer = final_answer
        source_citations = metadata.get("citations", [])
        kb_doc_id = None

        # Create VerifiedQA entry (FR52: Auto-add approved HITL to Verified KB)
        verified_qa_created = False
        if request.add_to_kb and question_text and approved_answer and item.bot_id:
            try:
                # Generate embedding for the question
                embedding_service = EmbeddingService()
                question_embedding = await embedding_service.embed_verified_question(question_text)
                await embedding_service.close()
                
                # Fetch bot to get group_id
                bot_result = await db.execute(
                    select(Bot).where(
                        and_(
                            Bot.id == item.bot_id,
                            Bot.tenant_id == current_tenant,
                        )
                    )
                )
                bot = bot_result.scalar_one_or_none()
                
                if bot and bot.group_id:
                    # Create VerifiedQA entry
                    verified_qa = await create_verified_qa(
                        db=db,
                        tenant_id=current_tenant,
                        group_id=bot.group_id,
                        bot_id=item.bot_id,
                        question_text=question_text,
                        question_embedding=question_embedding,
                        answer_text=approved_answer,
                        approved_by_user_id=current_user.id,
                        approved_at=item.resolution_timestamp,
                        source_citations=source_citations,
                    )
                    
                    logger.info(
                        f"Created VerifiedQA entry {verified_qa.id} from HITL approval "
                        f"(item={item_id}, bot={item.bot_id})"
                    )

                    # Mark that VerifiedQA creation succeeded and set flag on confidence log
                    verified_qa_created = True
                    item.is_verified_kb = True

                    # Add reference to verified_qa in metadata
                    item.metadata_json["verified_qa_id"] = str(verified_qa.id)
                    
                    # Also add to documents table (knowledge base) for RAG retrieval
                    kb_doc_id = None
                    try:
                        # Format Q&A as a text document
                        doc_content = f"Question: {question_text}\n\nAnswer: {approved_answer}"
                        doc_bytes = doc_content.encode('utf-8')
                        
                        # Create document with descriptive filename
                        safe_question = question_text[:50].replace('/', '-').replace('\\', '-')
                        doc_filename = f"HITL-{item_id[:8]}-{safe_question}.txt"
                        
                        doc, _ = await create_document(
                            db=db,
                            bot_id=bot.group_id,  # create_document maps bot_id to group_id
                            tenant_id=current_tenant,
                            uploader_id=current_user.id,
                            filename=doc_filename,
                            size_bytes=len(doc_bytes),
                            mime_type="text/plain",
                            file_bytes=doc_bytes,
                            title=f"Verified Q&A: {question_text[:80]}",
                        )
                        
                        kb_doc_id = str(doc.id)
                        
                        # For HITL-approved Q&A, create chunk directly with the existing embedding
                        # This bypasses async processing which may fail
                        from app.models.chunk import Chunk
                        chunk = Chunk(
                            document_id=doc.id,
                            tenant_id=current_tenant,
                            group_id=bot.group_id,
                            chunk_index=0,
                            content=doc_content,
                            page_number=None,
                            vector=question_embedding,  # Reuse the embedding from VerifiedQA
                            metadata_json=json.dumps({"source": "hitl_approval", "verified_qa_id": str(verified_qa.id)}),
                            created_at=datetime.utcnow(),
                            updated_at=datetime.utcnow(),
                        )
                        db.add(chunk)
                        
                        # Mark document as ready immediately (skip async processing)
                        doc.status = "ready"
                        doc.updated_at = datetime.utcnow()
                        await db.flush()
                        
                        logger.info(
                            f"Created knowledge base document {doc.id} with chunk from HITL approval "
                            f"(item={item_id}, verified_qa={verified_qa.id})"
                        )
                        
                        # Link document to verified_qa in metadata
                        item.metadata_json["kb_document_id"] = kb_doc_id
                        # If document/chunk created, ensure is_verified_kb flag is set
                        item.is_verified_kb = True
                        
                    except Exception as e:
                        logger.error(
                            f"Failed to create knowledge base document for HITL item {item_id}: {e}",
                            exc_info=True
                        )
                        # Continue - VerifiedQA still created successfully
                else:
                    logger.warning(
                        f"Bot {item.bot_id} not found or missing group_id, "
                        f"skipping VerifiedQA creation for HITL item {item_id}"
                    )
                    # Ensure verified_qa_created remains False
                        
            except EmbeddingError as e:
                logger.error(
                    f"Failed to generate embedding for VerifiedQA from HITL item {item_id}: {e}"
                )
                # Continue with approval even if VerifiedQA creation fails
                # This prevents blocking the approval workflow
            except Exception as e:
                logger.error(
                    f"Failed to create VerifiedQA entry for HITL item {item_id}: {e}",
                    exc_info=True
                )
                # Continue with approval even if VerifiedQA creation fails
        else:
            logger.warning(
                f"Skipping VerifiedQA creation for HITL item {item_id}: "
                f"missing question_text={bool(question_text)}, "
                f"approved_answer={bool(approved_answer)}, "
                f"bot_id={bool(item.bot_id)}"
            )
            # No VerifiedQA created in this case

        # Commit transaction (HITL approval + VerifiedQA + Document + Chunk if created)
        try:
            logger.debug(f"Flushing approval changes for item {item_id}")
            await db.flush()
            
            # Refetch to confirm the changes were persisted
            await db.refresh(item)
            
            if not item.hitl_resolved:
                logger.error(f"CRITICAL: hitl_resolved flag not persisted for item {item_id}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to persist approval - database write issue",
                )
            
            logger.debug(f"Committing approval for item {item_id}")
            await db.commit()
            
            # CRITICAL: Refetch again after commit to ensure all changes are visible
            await db.refresh(item)
            
            logger.info(f"✓ HITL item {item_id} successfully marked as resolved (approved), hitl_resolved={item.hitl_resolved}, resolution_action={item.metadata_json.get('resolution_action')}")
            # Document is already set to "ready" with chunk created inline - no async processing needed
        except Exception as e:
            logger.error(f"Transaction failed during approval of {item_id}: {e}", exc_info=True)
            await db.rollback()
            raise

        # Build response with the approved answer
        resolved_answer = approved_answer
        
        # Send approved answer to chat if requested and session_id is available
        chat_sent = False
        if request.send_to_chat:
            try:
                session_id = item.metadata_json.get("session_id")
                if session_id:
                    redis_client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
                    chat_channel = f"chat_session:{session_id}"
                    chat_message = {
                        "type": "approved_answer",
                        "answer": resolved_answer,
                        "question": item.query_text,
                        "citations": item.metadata_json.get("citations", []),
                        "timestamp": datetime.utcnow().isoformat(),
                        "message_id": item.metadata_json.get("message_id"),
                    }
                    await redis_client.publish(chat_channel, json.dumps(chat_message))
                    await redis_client.close()
                    chat_sent = True
                    logger.info(f"✓ Sent approved answer to chat session: {session_id}")
                else:
                    logger.debug("No session_id in metadata, skipping send to chat")
            except Exception as chat_error:
                logger.warning(f"Failed to send to chat: {chat_error}")
        
        # Publish resolution event to Redis for real-time updates
        try:
            redis_client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
            channel = f"hitl_queue:{current_tenant}"
            message = {
                "action": "item_resolved",
                "item_id": item_id,
                "status": "approved",
                "timestamp": datetime.utcnow().isoformat(),
            }
            await redis_client.publish(channel, json.dumps(message))
            await redis_client.close()
        except Exception as e:
            logger.warning(f"Failed to publish approval event to Redis: {e}")

        return {
            "status": "approved",
            "item_id": item_id,
            "resolved_answer": final_answer,
            "was_edited": was_edited,
            "diff": diff_result if was_edited else None,
            "verified_kb_updated": bool(verified_qa_created),
            "citations": metadata.get("citations", []),
            "chat_sent": chat_sent,
        }

    except HTTPException:
        # Re-raise HTTP exceptions (like 404) without wrapping
        raise
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid item ID",
        )
    except Exception as e:
        logger.error(f"❌ Error approving item {item_id}: {type(e).__name__}: {e}", exc_info=True)
        try:
            await db.rollback()
        except Exception as rollback_error:
            logger.error(f"Rollback failed after approval error: {rollback_error}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to approve item: {str(e)}",
        )


@router.post("/queue/{item_id}/reject")
async def reject_queue_item(
    item_id: str,
    request: RejectQueueItemRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_tenant: UUID = Depends(get_current_tenant),
):
    """
    Reject a review queue item (mark as resolved with rejection).
    Optionally provide a reason for rejection.
    Publishes event to Redis for real-time updates.
    """
    try:
        # SECURITY: Set RLS context for tenant isolation
        await set_tenant_context(db, current_user.tenant_id)

        item_uuid = UUID(item_id)
        
        logger.debug(f"Rejecting HITL item {item_id} by user {current_user.id}")
        
        # Find the item
        result = await db.execute(
            select(ConfidenceLog).where(
                and_(
                    ConfidenceLog.id == item_uuid,
                    ConfidenceLog.tenant_id == current_tenant,
                )
            )
        )
        item = result.scalars().first()

        if not item:
            logger.warning(f"HITL item {item_id} not found for tenant {current_tenant}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Item not found",
            )

        logger.debug(f"Found HITL item: {item.id}, currently resolved={item.hitl_resolved}")
        
        # SECURITY: Check if item is already resolved (prevent race condition)
        if item.hitl_resolved:
            logger.warning(
                f"Race condition prevented: Item {item_id} already resolved by user "
                f"{item.resolution_user_id} at {item.resolution_timestamp}"
            )
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Item has already been resolved by another user",
            )
        
        # SECURITY: Verify user has access to the group this item belongs to
        if item.group_id:
            from app.models.group_member import GroupMember
            membership_result = await db.execute(
                select(GroupMember).where(
                    and_(
                        GroupMember.group_id == item.group_id,
                        GroupMember.user_id == current_user.id,
                    )
                )
            )
            membership = membership_result.scalars().first()
            
            if not membership:
                logger.warning(
                    f"Access denied: User {current_user.id} attempted to reject "
                    f"HITL item {item_id} from group {item.group_id} without membership"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied: You do not have access to this item",
                )

        # Mark as resolved
        item.hitl_resolved = True
        item.resolution_user_id = current_user.id
        item.resolution_timestamp = __import__('datetime').datetime.utcnow()

        # Store rejection reason; reassign metadata so JSON updates persist
        metadata = dict(item.metadata_json or {})
        metadata["resolution_action"] = "rejected"
        if request.reason:
            metadata["rejection_reason"] = request.reason
            logger.debug(f"Rejection reason: {request.reason[:50]}...")

        item.metadata_json = metadata

        logger.debug(f"Flushing rejection changes for item {item_id}")
        await db.flush()
        
        # Refetch to confirm the changes were persisted
        await db.refresh(item)
        
        if not item.hitl_resolved:
            logger.error(f"CRITICAL: hitl_resolved flag not persisted for item {item_id}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to persist rejection - database write issue",
            )
        
        logger.debug(f"Committing rejection for item {item_id}")
        await db.commit()
        
        # CRITICAL: Refetch again after commit to ensure all changes are visible
        await db.refresh(item)
        
        logger.info(f"✓ HITL item {item_id} successfully marked as resolved (rejected), hitl_resolved={item.hitl_resolved}, resolution_action={item.metadata_json.get('resolution_action')}")
        
        # Publish resolution event to Redis for real-time updates
        try:
            redis_client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
            channel = f"hitl_queue:{current_tenant}"
            message = {
                "action": "item_resolved",
                "item_id": item_id,
                "status": "rejected",
                "timestamp": datetime.utcnow().isoformat(),
            }
            await redis_client.publish(channel, json.dumps(message))
            await redis_client.close()
        except Exception as e:
            logger.warning(f"Failed to publish rejection event to Redis: {e}")

        return {"status": "rejected", "item_id": item_id}

    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid item ID",
        )
    except Exception as e:
        logger.error(f"❌ Error rejecting item {item_id}: {type(e).__name__}: {e}", exc_info=True)
        try:
            await db.rollback()
        except Exception as rollback_error:
            logger.error(f"Rollback failed after rejection error: {rollback_error}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reject item: {str(e)}",
        )


# ============================================================================
# WebSocket for Real-Time Queue Updates (AC2)
# ============================================================================

def verify_websocket_token(token: str) -> dict:
    """
    Verify JWT token for WebSocket connection and extract payload.
    
    Returns:
        dict with 'sub' (user_id), 'tenant_id', and other JWT claims
    
    Raises:
        Exception on invalid or expired token
    """
    import jwt as pyjwt
    from app.core.settings import settings
    
    JWT_ALGORITHM = "HS256"
    
    try:
        payload = pyjwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[JWT_ALGORITHM]
        )
        
        if not payload.get("sub") or not payload.get("tenant_id"):
            raise ValueError("Missing required token claims")
        
        return payload
    except pyjwt.ExpiredSignatureError:
        raise ValueError("Token has expired")
    except pyjwt.InvalidTokenError as e:
        raise ValueError(f"Invalid token: {e}")
    except Exception as e:
        raise ValueError(f"Token verification failed: {e}")


class ConnectionManager:
    """
    Manages WebSocket connections per tenant.
    
    Tracks active connections and broadcasts real-time updates via Redis pub-sub.
    Ensures tenant isolation - each tenant receives only their queue updates.
    """
    
    def __init__(self):
        self.active_connections: Dict[UUID, Set[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, tenant_id: UUID):
        """Accept connection and register for this tenant."""
        await websocket.accept()
        if tenant_id not in self.active_connections:
            self.active_connections[tenant_id] = set()
        self.active_connections[tenant_id].add(websocket)
        logger.info(f"WebSocket connected for tenant {tenant_id}. Active: {len(self.active_connections[tenant_id])}")
    
    def disconnect(self, websocket: WebSocket, tenant_id: UUID):
        """Unregister connection for this tenant."""
        if tenant_id in self.active_connections:
            self.active_connections[tenant_id].discard(websocket)
            if not self.active_connections[tenant_id]:
                del self.active_connections[tenant_id]
        logger.info(f"WebSocket disconnected for tenant {tenant_id}")
    
    async def broadcast_to_tenant(self, tenant_id: UUID, message: dict):
        """Send message to all connections for a specific tenant."""
        if tenant_id not in self.active_connections:
            return
        
        disconnected = set()
        for connection in self.active_connections[tenant_id]:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting to connection: {e}")
                disconnected.add(connection)
        
        # Clean up disconnected websockets
        for connection in disconnected:
            self.disconnect(connection, tenant_id)


# Global connection manager instance
connection_manager = ConnectionManager()


@router.websocket("/ws/queue")
async def websocket_queue_updates(
    websocket: WebSocket,
    token: Optional[str] = None,
):
    """WebSocket endpoint for real-time HITL queue updates."""
    
    tenant_id = None
    user_id = None
    redis_client = None
    pubsub = None
    
    try:
        # Validate token BEFORE accepting connection
        if not token:
            logger.warning("WebSocket: No token provided")
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Token required")
            return
        
        try:
            payload = verify_websocket_token(token)
            tenant_id = UUID(payload.get("tenant_id"))
            user_id = UUID(payload.get("sub"))
            logger.info(f"WebSocket auth OK: user={user_id}, tenant={tenant_id}")
        except Exception as e:
            logger.error(f"WebSocket auth failed: {e}")
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid token")
            return
        
        # Accept connection
        await connection_manager.connect(websocket, tenant_id)
        
        # Try Redis pub-sub (optional)
        redis_available = False
        try:
            try:
                redis_client = await aioredis.from_url(settings.REDIS_URL, decode_responses=True)
                await redis_client.ping()
            except Exception as first_error:
                # Fallback for local development if 'redis' host resolution fails
                if "redis" in settings.REDIS_URL and "getaddrinfo failed" in str(first_error):
                    logger.warning(f"Redis connection failed with {settings.REDIS_URL}, attempting localhost fallback...")
                    fallback_url = "redis://localhost:6379/0"
                    if settings.REDIS_PASSWORD:
                        fallback_url = f"redis://:{settings.REDIS_PASSWORD}@localhost:6379/0"
                    
                    redis_client = await aioredis.from_url(fallback_url, decode_responses=True)
                    await redis_client.ping()
                    logger.info("Connected to Redis via localhost fallback")
                else:
                    raise first_error

            pubsub = redis_client.pubsub()
            channel = f"hitl_queue:{tenant_id}"
            await pubsub.subscribe(channel)
            logger.info(f"WebSocket: Subscribed to {channel}")
            redis_available = True
        except Exception as e:
            logger.warning(f"WebSocket: Redis unavailable: {e}. Heartbeat-only mode")
        
        # Send initial connection success
        try:
            await websocket.send_json({
                "type": "connected",
                "timestamp": datetime.utcnow().isoformat(),
                "redis_available": redis_available,
            })
        except:
            pass
        
        # Keep connection alive with heartbeats and pub-sub messages
        last_heartbeat = datetime.utcnow()
        while True:
            try:
                # Listen for messages with timeout
                try:
                    data = await asyncio.wait_for(websocket.receive_text(), timeout=30)
                    # Handle client pings
                    if data:
                        try:
                            msg = json.loads(data)
                            if msg.get("action") == "ping":
                                await websocket.send_json({"type": "pong", "timestamp": datetime.utcnow().isoformat()})
                        except:
                            pass
                except asyncio.TimeoutError:
                    # Send heartbeat on timeout
                    await websocket.send_json({
                        "type": "heartbeat",
                        "timestamp": datetime.utcnow().isoformat(),
                    })
                    continue
                
                # Check for Redis pub-sub messages
                if redis_available and pubsub:
                    message = pubsub.get_message()
                    if message and message.get("type") == "message":
                        try:
                            data = json.loads(message["data"])
                            await websocket.send_json({
                                "type": "queue_update",
                                "data": data,
                                "timestamp": datetime.utcnow().isoformat(),
                            })
                        except:
                            pass
                            
            except WebSocketDisconnect:
                logger.info(f"WebSocket: Client disconnected, user={user_id}, tenant={tenant_id}")
                break
            except Exception as e:
                logger.error(f"WebSocket: Error for tenant {tenant_id}: {e}")
                try:
                    await websocket.send_json({"type": "error", "message": str(e)})
                except:
                    pass
                break
    
    except Exception as e:
        logger.error(f"WebSocket: Unhandled error: {e}")
        try:
            await websocket.close(code=status.WS_1011_SERVER_ERROR, reason="Internal error")
        except:
            pass
    
    finally:
        # Cleanup
        try:
            if tenant_id:
                connection_manager.disconnect(websocket, tenant_id)
            if pubsub:
                try:
                    await pubsub.unsubscribe()
                    await pubsub.close()
                except:
                    pass
            if redis_client:
                try:
                    await redis_client.close()
                except:
                    pass
        except Exception as e:
            logger.error(f"WebSocket cleanup error: {e}")


