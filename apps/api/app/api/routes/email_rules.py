from typing import List, Optional
from uuid import UUID, uuid4
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, update, delete

from app.core.database import get_db
from app.api.v1.auth import get_current_user
from app.models.user import User
from app.models.email_monitoring_rule import EmailMonitoringRule
from app.models.email_integration import EmailIntegration
from app.models.bot import Bot
from app.schemas.email_rules import (
    EmailRuleCreate,
    EmailRuleUpdate,
    EmailRuleResponse,
    ReorderRequest,
    ToggleResponse,
    EmailSampleRequest,
    EmailSampleResult,
    MonitoringStatusResponse,
    MonitoringPauseRequest,
)
from app.email_automation.matcher import EmailSample, match_email_to_rules

router = APIRouter(prefix="/api/v1/email-rules", tags=["email-rules"])


async def _validate_bot_and_integration(db: AsyncSession, tenant_id: UUID, bot_id: UUID, integration_id: UUID):
    # check bot belongs to tenant
    res = await db.execute(select(Bot).where(and_(Bot.id == bot_id, Bot.tenant_id == tenant_id)))
    if not res.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Bot not found")

    # check integration belongs to tenant
    res = await db.execute(select(EmailIntegration).where(and_(EmailIntegration.id == integration_id, EmailIntegration.tenant_id == tenant_id)))
    if not res.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Integration not found")


@router.post("", response_model=EmailRuleResponse)
async def create_rule(
    payload: EmailRuleCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await _validate_bot_and_integration(db, current_user["tenant_id"], payload.bot_id, payload.integration_id)

    rule = EmailMonitoringRule(
        id=uuid4(),
        tenant_id=current_user["tenant_id"],
        user_id=current_user["sub"],
        integration_id=payload.integration_id,
        bot_id=payload.bot_id,
        folder_labels=payload.folder_labels or [],
        include_keywords=payload.include_keywords or [],
        exclude_keywords=payload.exclude_keywords or [],
        priority=payload.priority,
        is_active=payload.is_active,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(rule)
    await db.commit()
    await db.refresh(rule)
    return rule


@router.get("", response_model=List[EmailRuleResponse])
async def list_rules(
    integration_id: Optional[UUID] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = select(EmailMonitoringRule).where(EmailMonitoringRule.tenant_id == current_user["tenant_id"]).order_by(EmailMonitoringRule.priority.asc())
    if integration_id:
        q = q.where(EmailMonitoringRule.integration_id == integration_id)
    res = await db.execute(q)
    return res.scalars().all()


@router.put("/{rule_id}", response_model=EmailRuleResponse)
async def update_rule(
    rule_id: UUID,
    payload: EmailRuleUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    res = await db.execute(select(EmailMonitoringRule).where(and_(EmailMonitoringRule.id == rule_id, EmailMonitoringRule.tenant_id == current_user["tenant_id"])) )
    rule = res.scalar_one_or_none()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")

    if payload.bot_id is not None:
        await _validate_bot_and_integration(db, current_user["tenant_id"], payload.bot_id, rule.integration_id)
        rule.bot_id = payload.bot_id

    if payload.folder_labels is not None:
        rule.folder_labels = payload.folder_labels
    if payload.include_keywords is not None:
        rule.include_keywords = payload.include_keywords
    if payload.exclude_keywords is not None:
        rule.exclude_keywords = payload.exclude_keywords
    if payload.priority is not None:
        rule.priority = payload.priority
    if payload.is_active is not None:
        rule.is_active = payload.is_active

    rule.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(rule)
    return rule


@router.delete("/{rule_id}")
async def delete_rule(
    rule_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    res = await db.execute(select(EmailMonitoringRule).where(and_(EmailMonitoringRule.id == rule_id, EmailMonitoringRule.tenant_id == current_user["tenant_id"])) )
    rule = res.scalar_one_or_none()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    await db.delete(rule)
    await db.commit()
    return {"status": "deleted"}


@router.put("/reorder")
async def reorder_rules(
    payload: ReorderRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Assign sequential priorities starting at 1
    priorities = {rid: i + 1 for i, rid in enumerate(payload.ordered_ids)}

    res = await db.execute(select(EmailMonitoringRule).where(EmailMonitoringRule.tenant_id == current_user["tenant_id"]))
    rules = res.scalars().all()

    for r in rules:
        if r.id in priorities:
            r.priority = priorities[r.id]
            r.updated_at = datetime.utcnow()
    await db.commit()
    return {"status": "ok"}


@router.put("/{rule_id}/toggle", response_model=ToggleResponse)
async def toggle_rule(
    rule_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    res = await db.execute(select(EmailMonitoringRule).where(and_(EmailMonitoringRule.id == rule_id, EmailMonitoringRule.tenant_id == current_user["tenant_id"])) )
    rule = res.scalar_one_or_none()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")

    rule.is_active = not bool(rule.is_active)
    rule.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(rule)
    return ToggleResponse(id=rule.id, is_active=rule.is_active)


@router.post("/{rule_id}/test", response_model=EmailSampleResult)
async def test_rule(
    rule_id: UUID,
    payload: EmailSampleRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Load the rule and other active rules for the same integration
    res = await db.execute(select(EmailMonitoringRule).where(and_(EmailMonitoringRule.tenant_id == current_user["tenant_id"], EmailMonitoringRule.id == rule_id)))
    rule = res.scalar_one_or_none()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")

    res = await db.execute(select(EmailMonitoringRule).where(and_(EmailMonitoringRule.tenant_id == current_user["tenant_id"], EmailMonitoringRule.integration_id == rule.integration_id)))
    rules = res.scalars().all()

    sample = EmailSample(
        subject=payload.subject,
        body=payload.body,
        sender=payload.sender,
        folder=payload.folder,
        labels=payload.labels,
    )

    # Convert to list of dicts as matcher expects
    rules_dicts = [
        {
            "id": r.id,
            "folder_labels": r.folder_labels or [],
            "include_keywords": r.include_keywords or [],
            "exclude_keywords": r.exclude_keywords or [],
            "priority": r.priority,
            "is_active": r.is_active,
        }
        for r in rules
    ]

    matched = match_email_to_rules(sample, rules_dicts)

    explanation = ""
    if matched is None:
        return EmailSampleResult(matched=False, rule_id=None, explanation="No rules matched this sample.")

    rid = matched.get("id")
    top = "Matched rule {} by priority and conditions.".format(rid)
    explanation = top
    return EmailSampleResult(matched=True, rule_id=rid, explanation=explanation)


# Monitoring status endpoints (Story 6.3 Tasks 6-7)
@router.get("/monitoring/status", response_model=MonitoringStatusResponse)
async def get_monitoring_status(
    integration_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    res = await db.execute(
        select(EmailIntegration).where(
            and_(EmailIntegration.id == integration_id, EmailIntegration.tenant_id == current_user["tenant_id"])
        )
    )
    integ = res.scalar_one_or_none()
    if not integ:
        raise HTTPException(status_code=404, detail="Integration not found")

    return MonitoringStatusResponse(
        integration_id=integ.id,
        is_paused=bool(getattr(integ, "is_paused", False)),
        last_poll_at=getattr(integ, "last_poll_at", None),
        last_success_at=getattr(integ, "last_success_at", None),
        last_error_at=getattr(integ, "last_error_at", None),
        last_error_message=getattr(integ, "last_error_message", None),
        next_poll_at=getattr(integ, "next_poll_at", None),
        error_count=int(getattr(integ, "error_count", 0) or 0),
    )


@router.put("/monitoring/pause", response_model=MonitoringStatusResponse)
async def set_monitoring_pause(
    integration_id: UUID,
    payload: MonitoringPauseRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    res = await db.execute(
        select(EmailIntegration).where(
            and_(EmailIntegration.id == integration_id, EmailIntegration.tenant_id == current_user["tenant_id"])
        )
    )
    integ = res.scalar_one_or_none()
    if not integ:
        raise HTTPException(status_code=404, detail="Integration not found")

    integ.is_paused = bool(payload.is_paused)
    integ.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(integ)

    return MonitoringStatusResponse(
        integration_id=integ.id,
        is_paused=bool(getattr(integ, "is_paused", False)),
        last_poll_at=getattr(integ, "last_poll_at", None),
        last_success_at=getattr(integ, "last_success_at", None),
        last_error_at=getattr(integ, "last_error_at", None),
        last_error_message=getattr(integ, "last_error_message", None),
        next_poll_at=getattr(integ, "next_poll_at", None),
        error_count=int(getattr(integ, "error_count", 0) or 0),
    )
