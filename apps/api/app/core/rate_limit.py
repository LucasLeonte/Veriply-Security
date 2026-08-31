"""Rate limiting dependency and utilities using Redis and memory fallback (THR-07)."""

import time
import logging
from typing import Optional, Dict, Tuple
from fastapi import Request, HTTPException, status
import redis.asyncio as aioredis

from app.core.settings import settings
from app.core.security_logger import SecurityEvent, log_security_event, extract_request_context

logger = logging.getLogger(__name__)

# In-memory fallback sliding window cache: {key: (count, reset_timestamp)}
_in_memory_rate_cache: Dict[str, Tuple[int, float]] = {}
_redis_client: Optional[aioredis.Redis] = None


async def get_redis_client() -> Optional[aioredis.Redis]:
    """Get or initialize singleton Redis client for rate limiting."""
    global _redis_client
    if _redis_client is not None:
        return _redis_client

    try:
        client = await aioredis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            socket_timeout=2.0,
            socket_connect_timeout=2.0,
        )
        await client.ping()
        _redis_client = client
        return _redis_client
    except Exception as e:
        logger.warning(f"Redis unavailable for rate limiting ({e}); using in-memory fallback.")
        return None


def get_client_ip(request: Request) -> str:
    """Extract client IP from request, taking proxy headers into account safely."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        # First IP in the comma-separated chain is the client IP
        return forwarded.split(",")[0].strip()
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip.strip()
    if request.client and request.client.host:
        return request.client.host
    return "127.0.0.1"


class RateLimiter:
    """FastAPI dependency for rate limiting requests per IP or identifier."""

    def __init__(
        self,
        requests_per_minute: int = 30,
        window_seconds: int = 60,
        scope: str = "global",
    ):
        self.requests_per_minute = requests_per_minute
        self.window_seconds = window_seconds
        self.scope = scope

    async def __call__(self, request: Request) -> None:
        client_ip = get_client_ip(request)
        key = f"rate_limit:{self.scope}:{client_ip}"
        now = time.time()

        redis = await get_redis_client()

        if redis:
            try:
                # Sliding counter via Redis atomic pipeline
                pipe = redis.pipeline()
                pipe.incr(key)
                pipe.ttl(key)
                results = await pipe.execute()
                current_count = results[0]
                current_ttl = results[1]

                # Set expiry if key was just created
                if current_count == 1 or current_ttl == -1:
                    await redis.expire(key, self.window_seconds)
                    current_ttl = self.window_seconds

                if current_count > self.requests_per_minute:
                    retry_after = max(1, current_ttl)
                    ctx = extract_request_context(request)
                    await log_security_event(
                        SecurityEvent.RATE_LIMIT_HIT,
                        status=429,
                        detail=(
                            f"Rate limit exceeded on scope '{self.scope}': "
                            f"{current_count}/{self.requests_per_minute} req/{self.window_seconds}s"
                        ),
                        **ctx,
                    )
                    raise HTTPException(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        detail="Too many requests. Please slow down.",
                        headers={
                            "Retry-After": str(retry_after),
                            "X-RateLimit-Limit": str(self.requests_per_minute),
                            "X-RateLimit-Remaining": "0",
                            "X-RateLimit-Reset": str(int(now + retry_after)),
                        },
                    )
                return
            except HTTPException:
                raise
            except Exception as e:
                logger.warning(f"Redis rate limiter error ({e}); falling back to memory.")

        # In-memory fallback
        global _in_memory_rate_cache
        current_data = _in_memory_rate_cache.get(key)

        if current_data is None or now >= current_data[1]:
            # Reset window
            _in_memory_rate_cache[key] = (1, now + self.window_seconds)
            return

        count, reset_at = current_data
        if count >= self.requests_per_minute:
            retry_after = max(1, int(reset_at - now))
            ctx = extract_request_context(request)
            await log_security_event(
                SecurityEvent.RATE_LIMIT_HIT,
                status=429,
                detail=(
                    f"In-memory rate limit exceeded on scope '{self.scope}': "
                    f"{count + 1}/{self.requests_per_minute} req/{self.window_seconds}s"
                ),
                **ctx,
            )
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many requests. Please slow down.",
                headers={
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Limit": str(self.requests_per_minute),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(reset_at)),
                },
            )

        _in_memory_rate_cache[key] = (count + 1, reset_at)
