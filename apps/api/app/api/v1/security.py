"""
Security Audit Log API — Admin endpoint
=========================================

GET /api/v1/security/audit-log
    Returns paginated, filterable security events from the audit_logs table.
    Requires: Owner or Admin role (tenant-scoped).
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user
from app.core.database import get_db
from app.models.audit_log import AuditLog

router = APIRouter(prefix="/api/v1/security", tags=["security"])


# ---------------------------------------------------------------------------
# Response schema
# ---------------------------------------------------------------------------

class AuditLogEntry(BaseModel):
    """Single audit log event returned to the admin caller."""
    id:           str
    ts:           datetime
    event_type:   Optional[str]
    severity:     Optional[str]
    outcome:      Optional[str]
    actor_id:     Optional[str]
    tenant_id:    Optional[str]
    ip_address:   Optional[str]
    user_agent:   Optional[str]
    http_method:  Optional[str]
    http_path:    Optional[str]
    http_status:  Optional[int]
    request_id:   Optional[str]
    detail:       Optional[str]

    model_config = {"from_attributes": True}


class AuditLogPage(BaseModel):
    total:  int
    page:   int
    limit:  int
    items:  list[AuditLogEntry]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_ADMIN_ROLES = {"owner", "admin"}


def _require_admin(current_user: dict) -> dict:
    """Raise 403 if the caller does not have owner or admin role."""
    role = (current_user.get("role") or "").lower()
    if role not in _ADMIN_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Security audit log requires Owner or Admin role.",
        )
    return current_user


def _row_to_entry(row: AuditLog) -> AuditLogEntry:
    return AuditLogEntry(
        id          = str(row.id),
        ts          = row.created_at,
        event_type  = row.event_type or row.action,
        severity    = row.severity,
        outcome     = row.outcome,
        actor_id    = str(row.actor_id) if row.actor_id else None,
        tenant_id   = str(row.tenant_id) if row.tenant_id else None,
        ip_address  = row.ip_address,
        user_agent  = row.user_agent,
        http_method = row.http_method,
        http_path   = row.http_path,
        http_status = row.http_status,
        request_id  = row.request_id,
        detail      = row.details,
    )


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------

@router.get(
    "/audit-log",
    response_model=AuditLogPage,
    summary="Security Audit Log",
    description=(
        "Returns a paginated, filterable list of security events. "
        "Results are scoped to the caller's tenant. "
        "Requires Owner or Admin role."
    ),
)
async def get_audit_log(
    # --- Auth ---
    current_user: dict = Depends(get_current_user),
    db:           AsyncSession = Depends(get_db),
    # --- Filters ---
    event_type:   Optional[str]      = Query(None, description="Filter by SecurityEvent type, e.g. AUTH_LOGIN_FAILURE"),
    severity:     Optional[str]      = Query(None, description="Filter by severity: DEBUG / INFO / WARNING / CRITICAL"),
    ip_address:   Optional[str]      = Query(None, description="Filter by client IP address"),
    actor_id:     Optional[UUID]     = Query(None, description="Filter by acting user UUID"),
    date_from:    Optional[datetime] = Query(None, description="ISO-8601 start of time range"),
    date_to:      Optional[datetime] = Query(None, description="ISO-8601 end of time range"),
    # --- Pagination ---
    page:         int                = Query(1,  ge=1,   description="Page number (1-based)"),
    limit:        int                = Query(50, ge=1, le=200, description="Results per page"),
) -> AuditLogPage:
    """
    Retrieve security events for your tenant.

    Only **Owner** and **Admin** users may access this endpoint.
    All results are automatically scoped to the caller's tenant.
    """
    _require_admin(current_user)
    tenant_id = UUID(current_user["tenant_id"])

    # Build filter conditions
    conditions = [AuditLog.tenant_id == tenant_id]

    if event_type:
        conditions.append(AuditLog.event_type == event_type.upper())
    if severity:
        conditions.append(AuditLog.severity == severity.upper())
    if ip_address:
        conditions.append(AuditLog.ip_address == ip_address)
    if actor_id:
        conditions.append(AuditLog.actor_id == actor_id)
    if date_from:
        conditions.append(AuditLog.created_at >= date_from)
    if date_to:
        conditions.append(AuditLog.created_at <= date_to)

    where_clause = and_(*conditions)

    # Total count
    count_q = select(AuditLog).where(where_clause)
    total_result = await db.execute(count_q)
    all_rows = total_result.scalars().all()
    total = len(all_rows)

    # Paginated results (newest first)
    offset = (page - 1) * limit
    page_q = (
        select(AuditLog)
        .where(where_clause)
        .order_by(AuditLog.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    page_result = await db.execute(page_q)
    rows = page_result.scalars().all()

    return AuditLogPage(
        total = total,
        page  = page,
        limit = limit,
        items = [_row_to_entry(r) for r in rows],
    )
