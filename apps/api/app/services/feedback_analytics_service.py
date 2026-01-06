"""Analytics aggregation for feedback."""

import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as aioredis

from app.models import Feedback, FeedbackReason, FeedbackType
from app.core.settings import settings


class FeedbackAnalyticsService:
    """Compute aggregate feedback statistics for a bot."""
    
    # Redis client for caching (initialized on first use)
    _redis_client: Optional[aioredis.Redis] = None
    
    @classmethod
    async def _get_redis(cls) -> Optional[aioredis.Redis]:
        """Get or create Redis client for caching."""
        if cls._redis_client is None:
            try:
                cls._redis_client = await aioredis.from_url(
                    settings.REDIS_URL,
                    encoding="utf-8",
                    decode_responses=True,
                )
                # Test connection
                await cls._redis_client.ping()
            except Exception:
                # Redis unavailable - disable caching
                return None
        return cls._redis_client
    
    @classmethod
    async def invalidate_cache(cls, bot_id: UUID) -> None:
        """Invalidate cached analytics for a bot (called on new feedback)."""
        redis = await cls._get_redis()
        if redis is None:
            return
        
        try:
            # Delete all cache keys for this bot (all time windows)
            pattern = f"feedback_stats:{bot_id}:*"
            cursor = 0
            while True:
                cursor, keys = await redis.scan(cursor, match=pattern, count=100)
                if keys:
                    await redis.delete(*keys)
                if cursor == 0:
                    break
        except Exception:
            # Ignore cache errors
            pass

    @classmethod
    async def aggregate_stats(
        cls,
        db: AsyncSession,
        *,
        bot_id: UUID,
        tenant_id: UUID,
        hours: int = 24,
    ) -> Dict[str, Any]:
        # Try to get from cache first
        cache_key = f"feedback_stats:{bot_id}:{hours}h"
        redis = await cls._get_redis()
        
        if redis is not None:
            try:
                cached = await redis.get(cache_key)
                if cached:
                    return json.loads(cached)
            except Exception:
                # Ignore cache errors, fallback to DB query
                pass
        
        # Cache miss or unavailable - compute from DB
        window_start = datetime.utcnow() - timedelta(hours=hours)

        base_filter = (
            Feedback.bot_id == bot_id,
            Feedback.created_at >= window_start,
        )

        total = await db.scalar(select(func.count(Feedback.id)).where(*base_filter)) or 0

        positive = await db.scalar(
            select(func.count(Feedback.id)).where(*base_filter, Feedback.type == FeedbackType.POSITIVE)
        ) or 0

        negative = await db.scalar(
            select(func.count(Feedback.id)).where(*base_filter, Feedback.type == FeedbackType.NEGATIVE)
        ) or 0

        harmful = await db.scalar(
            select(func.count(Feedback.id)).where(
                *base_filter,
                Feedback.type == FeedbackType.NEGATIVE,
                Feedback.reason == FeedbackReason.HARMFUL,
            )
        ) or 0

        # Top negative reasons grouped
        reason_rows = await db.execute(
            select(Feedback.reason, func.count(Feedback.id))
            .where(*base_filter, Feedback.type == FeedbackType.NEGATIVE)
            .group_by(Feedback.reason)
        )
        negative_reasons = {
            (reason.value if reason else "unknown"): count for reason, count in reason_rows.all()
        }

        result = {
            "total": total,
            "positive_count": positive,
            "negative_count": negative,
            "negative_reasons": negative_reasons,
            "harmful_count": harmful,
            "window_hours": hours,
        }
        
        # Store in cache with 1h TTL
        if redis is not None:
            try:
                await redis.setex(
                    cache_key,
                    3600,  # 1 hour in seconds
                    json.dumps(result),
                )
            except Exception:
                # Ignore cache errors
                pass
        
        return result