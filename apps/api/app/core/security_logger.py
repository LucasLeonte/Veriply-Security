"""
Security Event Logger
=====================

Single entry point for all security-relevant event logging.

Every call to ``log_security_event()`` does three things atomically:

1. Emits a structured JSON line to stdout (captured by Docker / log aggregator)
2. Persists the event to the ``audit_logs`` PostgreSQL table (fire-and-forget)
3. For ``AUTH_LOGIN_FAILURE``: increments a per-IP Redis counter and emits
   ``SUSPICIOUS_ACTIVITY`` (CRITICAL) when the brute-force threshold is reached

Usage::

    from app.core.security_logger import SecurityEvent, log_security_event, extract_request_context

    ctx = extract_request_context(request)
    await log_security_event(
        SecurityEvent.AUTH_LOGIN_FAILURE,
        detail="Invalid password",
        user_id=str(user.id),
        **ctx,
    )
"""
from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from uuid import UUID

logger = logging.getLogger("veriply.security")

# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class SecurityEvent(str, Enum):
    """All tracked security event types."""
    AUTH_LOGIN_SUCCESS        = "AUTH_LOGIN_SUCCESS"
    AUTH_LOGIN_FAILURE        = "AUTH_LOGIN_FAILURE"
    AUTH_LOGOUT               = "AUTH_LOGOUT"
    AUTH_TOKEN_INVALID        = "AUTH_TOKEN_INVALID"
    AUTH_TOKEN_EXPIRED        = "AUTH_TOKEN_EXPIRED"
    AUTH_REGISTER             = "AUTH_REGISTER"
    PASSWORD_RESET_REQUESTED  = "PASSWORD_RESET_REQUESTED"
    PASSWORD_RESET_COMPLETED  = "PASSWORD_RESET_COMPLETED"
    ACCESS_DENIED             = "ACCESS_DENIED"
    RATE_LIMIT_HIT            = "RATE_LIMIT_HIT"
    ADMIN_ACTION              = "ADMIN_ACTION"
    SUSPICIOUS_ACTIVITY       = "SUSPICIOUS_ACTIVITY"


class _Severity(str, Enum):
    DEBUG    = "DEBUG"
    INFO     = "INFO"
    WARNING  = "WARNING"
    CRITICAL = "CRITICAL"


class _Outcome(str, Enum):
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    BLOCKED = "BLOCKED"


# (severity, outcome) defaults per event type
_EVENT_CONFIG: dict[SecurityEvent, tuple[_Severity, _Outcome]] = {
    SecurityEvent.AUTH_LOGIN_SUCCESS:       (_Severity.INFO,     _Outcome.SUCCESS),
    SecurityEvent.AUTH_LOGIN_FAILURE:       (_Severity.WARNING,  _Outcome.FAILURE),
    SecurityEvent.AUTH_LOGOUT:              (_Severity.INFO,     _Outcome.SUCCESS),
    SecurityEvent.AUTH_TOKEN_INVALID:       (_Severity.WARNING,  _Outcome.FAILURE),
    SecurityEvent.AUTH_TOKEN_EXPIRED:       (_Severity.WARNING,  _Outcome.FAILURE),
    SecurityEvent.AUTH_REGISTER:            (_Severity.INFO,     _Outcome.SUCCESS),
    SecurityEvent.PASSWORD_RESET_REQUESTED: (_Severity.INFO,     _Outcome.SUCCESS),
    SecurityEvent.PASSWORD_RESET_COMPLETED: (_Severity.INFO,     _Outcome.SUCCESS),
    SecurityEvent.ACCESS_DENIED:            (_Severity.WARNING,  _Outcome.BLOCKED),
    SecurityEvent.RATE_LIMIT_HIT:           (_Severity.WARNING,  _Outcome.BLOCKED),
    SecurityEvent.ADMIN_ACTION:             (_Severity.INFO,     _Outcome.SUCCESS),
    SecurityEvent.SUSPICIOUS_ACTIVITY:      (_Severity.CRITICAL, _Outcome.BLOCKED),
}

_STDLIB_LEVEL: dict[str, int] = {
    "DEBUG":    logging.DEBUG,
    "INFO":     logging.INFO,
    "WARNING":  logging.WARNING,
    "CRITICAL": logging.CRITICAL,
}

# ---------------------------------------------------------------------------
# Brute-force thresholds
# ---------------------------------------------------------------------------

BRUTE_FORCE_THRESHOLD       = 5    # failures before SUSPICIOUS_ACTIVITY is raised
BRUTE_FORCE_WINDOW_SECONDS  = 300  # 5-minute rolling window

_redis_client = None


async def _get_redis():
    """Lazy-init Redis client for brute-force tracking. Returns None if unavailable."""
    global _redis_client
    if _redis_client is not None:
        return _redis_client
    try:
        import redis.asyncio as aioredis
        from app.core.settings import settings
        client = await aioredis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            socket_timeout=1.0,
            socket_connect_timeout=1.0,
        )
        await client.ping()
        _redis_client = client
    except Exception:
        pass
    return _redis_client


async def _check_and_increment_brute_force(ip: str) -> bool:
    """
    Increment the per-IP failure counter and return True only when the counter
    hits exactly BRUTE_FORCE_THRESHOLD (so we alert once per burst, not on
    every subsequent failure).
    """
    redis = await _get_redis()
    if redis is None:
        return False
    key = f"sec:bf:{ip}"
    try:
        count = await redis.incr(key)
        if count == 1:
            await redis.expire(key, BRUTE_FORCE_WINDOW_SECONDS)
        return count == BRUTE_FORCE_THRESHOLD
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Record dataclass
# ---------------------------------------------------------------------------

@dataclass
class _SecurityEventRecord:
    event:      SecurityEvent
    ip:         str           = "unknown"
    user_id:    Optional[str] = None
    tenant_id:  Optional[str] = None
    user_agent: Optional[str] = None
    method:     Optional[str] = None
    path:       Optional[str] = None
    status:     Optional[int] = None
    detail:     Optional[str] = None
    request_id: Optional[str] = None
    ts:         str            = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    severity:   str            = field(init=False)
    outcome:    str            = field(init=False)

    def __post_init__(self) -> None:
        sev, out = _EVENT_CONFIG.get(self.event, (_Severity.INFO, _Outcome.SUCCESS))
        self.severity = sev.value
        self.outcome  = out.value


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _emit_log(record: _SecurityEventRecord) -> None:
    """Write a structured JSON line to stdout via the security logger."""
    payload = {
        "ts":         record.ts,
        "event":      record.event.value,
        "severity":   record.severity,
        "outcome":    record.outcome,
        "user_id":    record.user_id or "anonymous",
        "tenant_id":  record.tenant_id,
        "ip":         record.ip,
        "user_agent": record.user_agent,
        "method":     record.method,
        "path":       record.path,
        "status":     record.status,
        "detail":     record.detail,
        "request_id": record.request_id,
    }
    logger.log(
        _STDLIB_LEVEL.get(record.severity, logging.INFO),
        json.dumps(payload, default=str),
    )


async def _persist_event(record: _SecurityEventRecord) -> None:
    """Persist a security event to ``audit_logs``. Fails silently."""
    try:
        from app.core.database import AsyncSessionLocal
        from app.models.audit_log import AuditLog

        actor_uuid  = _safe_uuid(record.user_id)
        tenant_uuid = _safe_uuid(record.tenant_id)

        async with AsyncSessionLocal() as session:
            entry = AuditLog(
                tenant_id   = tenant_uuid,
                actor_id    = actor_uuid,
                action      = record.event.value,
                event_type  = record.event.value,
                severity    = record.severity,
                outcome     = record.outcome,
                details     = record.detail,
                ip_address  = record.ip,
                user_agent  = (record.user_agent or "")[:512],
                http_method = record.method,
                http_path   = (record.path or "")[:512],
                http_status = record.status,
                request_id  = record.request_id,
            )
            session.add(entry)
            await session.commit()
    except Exception as exc:
        logger.error("[security] DB persist failed for %s: %s", record.event.value, exc)


def _safe_uuid(value: Optional[str]) -> Optional[UUID]:
    """Parse a UUID string, returning None on failure."""
    if not value:
        return None
    try:
        return UUID(value)
    except (ValueError, AttributeError):
        return None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

async def log_security_event(
    event: SecurityEvent,
    *,
    ip:         str           = "unknown",
    user_id:    Optional[str] = None,
    tenant_id:  Optional[str] = None,
    user_agent: Optional[str] = None,
    method:     Optional[str] = None,
    path:       Optional[str] = None,
    status:     Optional[int] = None,
    detail:     Optional[str] = None,
    request_id: Optional[str] = None,
) -> None:
    """
    Emit and persist a security event.

    This is the **single entry point** for all security logging across the
    application. Safe to call from any async context.

    Example::

        await log_security_event(
            SecurityEvent.AUTH_LOGIN_FAILURE,
            ip=client_ip,
            path="/api/v1/auth/login",
            detail="Invalid password",
        )
    """
    record = _SecurityEventRecord(
        event      = event,
        ip         = ip,
        user_id    = user_id,
        tenant_id  = tenant_id,
        user_agent = user_agent,
        method     = method,
        path       = path,
        status     = status,
        detail     = detail,
        request_id = request_id,
    )

    # 1. Structured stdout log (synchronous — never blocks)
    _emit_log(record)

    # 2. DB persistence (fire-and-forget — does not block the HTTP response)
    try:
        asyncio.get_running_loop().create_task(_persist_event(record))
    except RuntimeError:
        pass  # No running event loop (e.g., test context) — skip DB write

    # 3. Brute-force detection (AUTH_LOGIN_FAILURE only)
    if event == SecurityEvent.AUTH_LOGIN_FAILURE:
        threshold_hit = await _check_and_increment_brute_force(ip)
        if threshold_hit:
            # Recursive call — emits its own log + DB write, no further BF check
            await log_security_event(
                SecurityEvent.SUSPICIOUS_ACTIVITY,
                ip         = ip,
                user_id    = user_id,
                tenant_id  = tenant_id,
                user_agent = user_agent,
                method     = method,
                path       = path,
                detail     = (
                    f"Brute-force threshold reached: "
                    f"{BRUTE_FORCE_THRESHOLD} login failures within "
                    f"{BRUTE_FORCE_WINDOW_SECONDS}s from {ip}"
                ),
                request_id = request_id,
            )


def extract_request_context(request) -> dict:
    """
    Extract IP, user agent, HTTP method, path, and request ID from a
    FastAPI ``Request`` object.

    Returns a dict that can be spread directly into ``log_security_event``::

        ctx = extract_request_context(request)
        await log_security_event(SecurityEvent.AUTH_LOGIN_FAILURE, **ctx)
    """
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        ip = forwarded.split(",")[0].strip()
    else:
        real_ip = request.headers.get("X-Real-IP")
        ip = real_ip or (request.client.host if request.client else "unknown")

    return {
        "ip":         ip,
        "user_agent": request.headers.get("User-Agent"),
        "method":     request.method,
        "path":       str(request.url.path),
        "request_id": getattr(request.state, "request_id", None),
    }
