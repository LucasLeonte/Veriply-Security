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

from fastapi import APIRouter, Depends, HTTPException, status, Query, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, and_
from sqlalchemy.orm import joinedload
import redis.asyncio as aioredis

from app.core.database import get_db
from app.core.settings import settings
from app.api.v1.auth import get_current_user, get_current_tenant
from app.models.user import User
from app.models.confidence_log import ConfidenceLog, RoutingDecision
from app.models.bot import Bot
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class ApproveQueueItemRequest(BaseModel):
    """Request to approve a review queue item."""
    edits: Optional[str] = Field(None, description="Optional edited response text")


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
    # Confidence is stored in the DB as a 0-1 float; keep the
    # API contract aligned so the frontend can render a % view
    # with a simple *100, matching the live chat certainty bar.
    confidence: float = Field(..., description="Confidence score (0-1)")
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
    current_tenant: UUID = Depends(get_current_tenant),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    sort_by: str = Query("oldest", regex="^(oldest|newest|lowest_confidence|highest_confidence)$"),
) -> ReviewQueueResponse:
    """
    Get pending HITL review items for the current tenant.
    
    Returns questions with confidence scores below bot thresholds that need
    human review. Items are filtered by tenant and by groups the user has access to.
    Items are sorted by creation date (oldest first by default) or confidence.
    
    Sorting options:
    - oldest: oldest items first (default, per AC requirement)
    - newest: newest items first
    - lowest_confidence: lowest confidence scores first
    - highest_confidence: highest confidence scores first
    """
    try:
        # Get user's group memberships to filter by accessible groups
        from app.models import GroupMember
        from sqlalchemy import func
        
        # Subquery to get group IDs user has access to
        user_groups_subquery = select(GroupMember.group_id).where(
            GroupMember.user_id == current_user.id
        ).subquery()
        
        # Query pending HITL items for this tenant, filtered by user's accessible groups
        query_stmt = select(ConfidenceLog).where(
            and_(
                ConfidenceLog.routing_decision == RoutingDecision.HITL,
                ConfidenceLog.hitl_resolved.is_(False),
                ConfidenceLog.tenant_id == current_tenant,
                # Filter by groups user has access to (or null group_id for tenant-wide bots)
                func.coalesce(ConfidenceLog.group_id, None).in_(
                    select(GroupMember.group_id).where(GroupMember.user_id == current_user.id)
                ) | ConfidenceLog.group_id.is_(None)
            )
        ).options(joinedload(ConfidenceLog.bot))

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

        # Get stats
        total = len(all_items)
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

    except Exception as e:
        logger.error(f"Error fetching HITL queue: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch review queue",
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
    Approve a review queue item (mark as resolved by human).
    Optionally accept edits to the AI draft.
    Publishes event to Redis for real-time updates.
    """
    try:
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

        # Mark as resolved
        item.hitl_resolved = True
        item.resolution_user_id = current_user.id
        item.resolution_timestamp = __import__('datetime').datetime.utcnow()

        # Store edits in metadata if provided; reassign the dict so JSON changes persist
        metadata = dict(item.metadata_json or {})

        if request.edits:
            metadata["human_edits"] = request.edits
            metadata["human_final_answer"] = request.edits
            metadata["resolution_action"] = "approved_with_edits"
            logger.debug(f"Approval with edits: {request.edits[:50]}...")
        else:
            # Default to AI draft as the approved answer if no edits supplied
            ai_draft = metadata.get("ai_draft", "")
            metadata["human_final_answer"] = ai_draft
            metadata["resolution_action"] = "approved"
            logger.debug("Approval without edits - using AI draft")

        item.metadata_json = metadata

        logger.debug(f"Committing approval for item {item_id}")
        await db.commit()
        logger.info(f"✓ HITL item {item_id} successfully marked as resolved (approved)")
        
        # Build response with the approved answer
        resolved_answer = (
            request.edits
            or item.metadata_json.get("ai_draft", "")
        )
        
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
            "resolved_answer": resolved_answer,
            "citations": item.metadata_json.get("citations", []),
        }

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

        logger.debug(f"Committing rejection for item {item_id}")
        await db.commit()
        logger.info(f"✓ HITL item {item_id} successfully marked as resolved (rejected)")
        
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
    """
    WebSocket endpoint for real-time HITL queue updates.
    
    Connects to Redis pub-sub to receive real-time notifications when:
    - New items are added to the queue
    - Items are resolved (approved/rejected)
    - Connection heartbeat (every 30 seconds)
    
    Clients receive:
    - "heartbeat": Periodic keep-alive message
    - "queue_update": New item or item resolved
    - "error": Connection or auth errors
    
    Protocol:
    1. Client connects with WebSocket (token passed as query param)
    2. Server authenticates and subscribes to tenant's Redis channel
    3. Server sends heartbeat every 30 seconds to keep connection alive
    4. Server forwards queue updates from Redis pub-sub
    5. On any error, client should reconnect with exponential backoff
    """
    
    # Authentication: Extract tenant from token
    try:
        if not token:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Token required")
            return
        
        # Verify token and extract tenant_id
        payload = verify_websocket_token(token)
        tenant_id = UUID(payload.get("tenant_id"))
        user_id = UUID(payload.get("sub"))
        
    except Exception as e:
        logger.error(f"WebSocket auth failed: {e}")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid token")
        return
    
    # Accept connection
    await connection_manager.connect(websocket, tenant_id)
    
    # Create Redis pub-sub subscriber
    redis_client = None
    pubsub = None
    heartbeat_task = None
    pubsub_task = None
    should_close = asyncio.Event()
    
    try:
        # Connect to Redis
        redis_client = await aioredis.from_url(settings.REDIS_URL, decode_responses=True)
        pubsub = redis_client.pubsub()
        
        # Subscribe to tenant-specific channel
        channel = f"hitl_queue:{tenant_id}"
        await pubsub.subscribe(channel)
        logger.info(f"User {user_id} subscribed to {channel}")
        
        # Create background tasks for heartbeat and pub-sub listening
        async def send_heartbeat():
            """Send heartbeat every 30 seconds to keep connection alive."""
            try:
                while True:
                    await asyncio.sleep(30)
                    if should_close.is_set():
                        break
                    await websocket.send_json({
                        "type": "heartbeat",
                        "timestamp": datetime.utcnow().isoformat(),
                    })
            except asyncio.CancelledError:
                pass
            except Exception as e:
                logger.error(f"Heartbeat task error: {e}")
                should_close.set()
                raise
        
        async def listen_pubsub():
            """Listen for messages from Redis pub-sub."""
            try:
                async for message in pubsub.listen():
                    if should_close.is_set():
                        break
                    if message["type"] == "message":
                        try:
                            data = json.loads(message["data"])
                            await websocket.send_json({
                                "type": "queue_update",
                                "data": data,
                                "timestamp": datetime.utcnow().isoformat(),
                            })
                        except json.JSONDecodeError:
                            logger.error(f"Invalid JSON in pubsub message: {message['data']}")
            except asyncio.CancelledError:
                pass
            except Exception as e:
                logger.error(f"PubSub listen error: {e}")
                should_close.set()
                raise
        
        async def receive_loop():
            """Listen for client messages."""
            try:
                while True:
                    if should_close.is_set():
                        break
                    try:
                        # Use timeout to periodically check if should_close is set
                        data = await asyncio.wait_for(websocket.receive_text(), timeout=60)
                        # Client can send {"action": "ping"} to verify connection is alive
                        if data:
                            try:
                                msg = json.loads(data)
                                if msg.get("action") == "ping":
                                    await websocket.send_json({"type": "pong"})
                            except json.JSONDecodeError:
                                pass
                    except asyncio.TimeoutError:
                        # Timeout is normal, just check if we should close and continue
                        continue
                    except WebSocketDisconnect:
                        # Client disconnected cleanly
                        logger.info(f"Client disconnected")
                        should_close.set()
                        break
                    except Exception as e:
                        # Log error but don't raise - let heartbeat/pubsub continue
                        logger.warning(f"Receive loop warning (non-fatal): {e}")
            except asyncio.CancelledError:
                pass
        
        # Start all three tasks
        heartbeat_task = asyncio.create_task(send_heartbeat())
        pubsub_task = asyncio.create_task(listen_pubsub())
        receive_task = asyncio.create_task(receive_loop())
        
        # Monitor all tasks concurrently
        # If heartbeat or pubsub fails, should_close.set() signals clean shutdown
        # If receive_loop fails non-fatally, it logs warning but continues
        tasks = [heartbeat_task, pubsub_task, receive_task]
        
        try:
            while True:
                # Check if any background task has failed
                done, pending = await asyncio.wait(tasks, timeout=5, return_when=asyncio.FIRST_EXCEPTION)
                
                for task in done:
                    try:
                        await task  # Get result to check for exceptions
                    except asyncio.CancelledError:
                        pass
                    except Exception as e:
                        logger.error(f"Background task failed: {e}")
                        should_close.set()
                        raise
                
                # If should_close is set, break and cleanup
                if should_close.is_set():
                    break
                
                # If no done tasks, continue monitoring
                if not done:
                    continue
        
        except WebSocketDisconnect:
            logger.info(f"User {user_id} disconnected from HITL queue")
        except Exception as e:
            logger.error(f"WebSocket error for tenant {tenant_id}: {e}")
            try:
                await websocket.send_json({
                    "type": "error",
                    "message": str(e),
                })
            except:
                pass
    except WebSocketDisconnect:
        logger.info(f"User {user_id} disconnected from HITL queue")
    except Exception as e:
        logger.error(f"WebSocket error for tenant {tenant_id}: {e}")
        try:
            await websocket.send_json({
                "type": "error",
                "message": str(e),
            })
        except:
            pass
    finally:
        # Signal background tasks to stop
        should_close.set()
        
        # Cleanup
        connection_manager.disconnect(websocket, tenant_id)
        
        # Cancel all tasks
        if heartbeat_task:
            heartbeat_task.cancel()
        if pubsub_task:
            pubsub_task.cancel()
        if 'receive_task' in locals():
            receive_task.cancel()
        
        # Wait for tasks to finish gracefully
        tasks_to_wait = [t for t in [heartbeat_task, pubsub_task, locals().get('receive_task')] if t]
        if tasks_to_wait:
            await asyncio.gather(*tasks_to_wait, return_exceptions=True)
        
        if pubsub:
            try:
                await pubsub.unsubscribe(f"hitl_queue:{tenant_id}")
                await pubsub.close()
            except:
                pass
        
        if redis_client:
            try:
                await redis_client.close()
            except:
                pass

