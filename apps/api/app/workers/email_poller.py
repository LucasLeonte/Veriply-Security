"""
Background polling worker for email integrations.

MVP: skeleton poller that iterates active integrations and logs intent.
Scheduling strategy: a simple in-process loop started on app startup.

Future: replace with APScheduler or Celery Beat.
"""
import asyncio
import logging
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.models.email_integration import EmailIntegration
from app.models.email_monitoring_rule import EmailMonitoringRule
from app.models.email_processing_queue import EmailProcessingQueue
from app.models.integration_credentials import IntegrationCredentials
from app.utils.encryption import decrypt_token
from app.integrations import gmail

logger = logging.getLogger(__name__)


async def poll_once(db_session: AsyncSession, *, tenant_id: Optional[UUID] = None):
    """Poll new emails for all active integrations, scoped by tenant if provided.
    This is a placeholder that demonstrates the flow and dedup strategy planning.
    """
    q = select(EmailIntegration).where(EmailIntegration.is_active == True)
    if tenant_id:
        q = q.where(EmailIntegration.tenant_id == tenant_id)

    res = await db_session.execute(q)
    integrations = res.scalars().all()

    for integ in integrations:
        # Load active rules ordered by priority
        res2 = await db_session.execute(
            select(EmailMonitoringRule)
            .where(
                and_(
                    EmailMonitoringRule.integration_id == integ.id,
                    EmailMonitoringRule.is_active == True,
                )
            )
            .order_by(EmailMonitoringRule.priority.asc())
        )
        rules = res2.scalars().all()

        logger.info(
            "[EmailPoller] Would poll provider=%s integration=%s rules=%d at %s",
            integ.provider,
            integ.id,
            len(rules),
            datetime.utcnow().isoformat(),
        )
        if integ.provider != "gmail":
            continue  # Skip non-gmail for now

        # Resolve OAuth creds: tenant-specific, else global, else settings
        client_id, client_secret = await _resolve_oauth_credentials(db_session, integ.tenant_id, "gmail")

        try:
            refresh_token = decrypt_token(integ.encrypted_refresh_token)
        except Exception:
            logger.exception("[EmailPoller] Failed to decrypt refresh token for %s", integ.id)
            continue

        # Build Gmail query from rule folders/labels
        labels = set()
        for r in rules:
            for lab in (r.folder_labels or []):
                if lab:
                    labels.add(lab)
        if not labels:
            labels.add("INBOX")

        label_terms = [f"label:{lab}" for lab in labels]
        query = " OR ".join(label_terms)

        try:
            threads = await gmail.list_threads(
                client_id=client_id,
                client_secret=client_secret,
                refresh_token=refresh_token,
                query=query,
                max_results=25,
            )
        except Exception:
            logger.exception("[EmailPoller] Gmail list_threads failed for integration %s", integ.id)
            continue

        # Convert rules to dicts for matcher
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

        from app.email_automation.matcher import EmailSample, match_email_to_rules

        for th in threads:
            provider_id = th.get("id")
            subject = th.get("subject", "")
            snippet = th.get("snippet", "")

            sample = EmailSample(subject=subject, body=snippet, folder="INBOX", labels=list(labels))
            matched = match_email_to_rules(sample, rules_dicts)
            if not matched:
                continue

            # Deduplicate by (integration_id, provider_message_id)
            exists = await db_session.execute(
                select(EmailProcessingQueue).where(
                    and_(
                        EmailProcessingQueue.integration_id == integ.id,
                        EmailProcessingQueue.provider_message_id == provider_id,
                    )
                )
            )
            if exists.scalar_one_or_none():
                continue

            # Enqueue: insert queued record
            record = EmailProcessingQueue(
                id=uuid4(),
                tenant_id=integ.tenant_id,
                integration_id=integ.id,
                rule_id=matched.get("id"),
                provider_message_id=provider_id,
                status="queued",
            )
            db_session.add(record)

        # Update last sync time
        try:
            integ.last_sync_time = datetime.utcnow()
            await db_session.commit()
        except Exception:
            await db_session.rollback()
            logger.exception("[EmailPoller] Failed to commit updates for integration %s", integ.id)


async def _resolve_oauth_credentials(db: AsyncSession, tenant_id: UUID, provider: str):
    # Try tenant-specific
    res = await db.execute(
        select(IntegrationCredentials)
        .where(and_(IntegrationCredentials.provider == provider, IntegrationCredentials.tenant_id == tenant_id))
        .limit(1)
    )
    cred = res.scalar_one_or_none()
    if not cred:
        # Try global
        res = await db.execute(
            select(IntegrationCredentials)
            .where(and_(IntegrationCredentials.provider == provider, IntegrationCredentials.tenant_id.is_(None)))
            .limit(1)
        )
        cred = res.scalar_one_or_none()

    if cred:
        try:
            client_secret = decrypt_token(cred.encrypted_client_secret)
        except Exception:
            client_secret = None
        return cred.client_id, client_secret

    # Fallback to settings
    from app.core.settings import settings
    if provider == "gmail":
        return settings.GOOGLE_CLIENT_ID, settings.GOOGLE_CLIENT_SECRET
    return None, None


async def run_periodic(db_session_factory, interval_seconds: int = 300):
    """Run poller periodically. db_session_factory must return an AsyncSession context manager."""
    while True:
        try:
            async with db_session_factory() as session:
                await poll_once(session)
        except Exception:
            logger.exception("[EmailPoller] Poll loop failed")
        await asyncio.sleep(interval_seconds)
