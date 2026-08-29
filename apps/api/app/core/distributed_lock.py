"""Distributed locking utility for HITL review queue concurrency protection (THR-06)."""

import time
import logging
from typing import Optional, Tuple, Dict
import redis.asyncio as aioredis

from app.core.settings import settings

logger = logging.getLogger(__name__)

# In-memory fallback lock store: {item_id: (operator_id, expires_at)}
_in_memory_locks: Dict[str, Tuple[str, float]] = {}
_redis_lock_client: Optional[aioredis.Redis] = None


async def get_redis_lock_client() -> Optional[aioredis.Redis]:
    """Get or create singleton Redis client for distributed locking."""
    global _redis_lock_client
    if _redis_lock_client is not None:
        return _redis_lock_client

    try:
        client = await aioredis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            socket_timeout=2.0,
            socket_connect_timeout=2.0,
        )
        await client.ping()
        _redis_lock_client = client
        return _redis_lock_client
    except Exception as e:
        logger.warning(f"Redis unavailable for distributed locking ({e}); using in-memory fallback.")
        return None


async def acquire_review_lock(
    item_id: str,
    operator_id: str,
    ttl: int = settings.REDIS_LOCK_DEFAULT_TTL,
) -> Tuple[bool, Optional[str]]:
    """Attempt to acquire an exclusive lock on a review queue item.

    Args:
        item_id: ID of the review queue item or interaction
        operator_id: UUID or identifier of the operator requesting the lock
        ttl: Time-to-live in seconds

    Returns:
        Tuple of (acquired: bool, current_holder_operator_id: Optional[str])
    """
    key = f"lock:review_item:{item_id}"
    now = time.time()
    redis = await get_redis_lock_client()

    if redis:
        try:
            # Atomic SET if Not eXists with EXpiration
            acquired = await redis.set(key, operator_id, nx=True, ex=ttl)
            if acquired:
                logger.info(f"Lock acquired for review item {item_id} by operator {operator_id} (TTL={ttl}s)")
                return True, operator_id
            
            # If not acquired, check who currently holds the lock
            current_holder = await redis.get(key)
            if current_holder == operator_id:
                # Same operator already owns it, renew TTL
                await redis.expire(key, ttl)
                return True, operator_id
            return False, current_holder
        except Exception as e:
            logger.warning(f"Redis lock error ({e}); using in-memory fallback.")

    # In-memory fallback
    global _in_memory_locks
    existing = _in_memory_locks.get(item_id)
    if existing:
        holder, expires_at = existing
        if now < expires_at:
            if holder == operator_id:
                _in_memory_locks[item_id] = (operator_id, now + ttl)
                return True, operator_id
            return False, holder

    # Acquire memory lock
    _in_memory_locks[item_id] = (operator_id, now + ttl)
    return True, operator_id


async def release_review_lock(item_id: str, operator_id: str) -> bool:
    """Release a review queue item lock if held by the operator.

    Args:
        item_id: ID of the review queue item
        operator_id: Identifier of the operator releasing the lock

    Returns:
        True if lock was released, False otherwise
    """
    key = f"lock:review_item:{item_id}"
    redis = await get_redis_lock_client()

    if redis:
        try:
            # Lua script to release only if value matches operator_id
            release_script = """
            if redis.call("get", KEYS[1]) == ARGV[1] then
                return redis.call("del", KEYS[1])
            else
                return 0
            end
            """
            result = await redis.eval(release_script, 1, key, operator_id)
            return bool(result)
        except Exception as e:
            logger.warning(f"Redis release lock error ({e}); cleaning up memory.")

    # In-memory fallback
    global _in_memory_locks
    existing = _in_memory_locks.get(item_id)
    if existing and existing[0] == operator_id:
        _in_memory_locks.pop(item_id, None)
        return True
    return False


async def extend_review_lock(
    item_id: str,
    operator_id: str,
    ttl: int = settings.REDIS_LOCK_DEFAULT_TTL,
) -> bool:
    """Extend the TTL on an active review lock (heartbeat).

    Args:
        item_id: ID of the review queue item
        operator_id: Identifier of the operator holding the lock
        ttl: New expiration duration in seconds

    Returns:
        True if extended, False if lock not held
    """
    acquired, holder = await acquire_review_lock(item_id, operator_id, ttl)
    return acquired and holder == operator_id
