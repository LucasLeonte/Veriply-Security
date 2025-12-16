"""Audit service for tracking document and chunk provenance."""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from datetime import datetime
import json
import logging

from app.models import AuditLog

logger = logging.getLogger(__name__)


class AuditService:
    """Service for audit trail and provenance tracking."""

    @staticmethod
    async def log_action(
        db: AsyncSession,
        actor_id: UUID,
        action: str,
        tenant_id: UUID,
        group_id: UUID | None = None,
        target_type: str | None = None,
        target_id: UUID | None = None,
        details: dict | None = None,
    ) -> AuditLog:
        """
        Log an action to the audit trail.
        
        Args:
            db: Database session
            actor_id: User performing action
            action: Action name (e.g., 'document_uploaded', 'bot_created')
            tenant_id: Tenant ID
            group_id: Optional group ID
            target_type: Type of target (e.g., 'document', 'bot', 'chunk')
            target_id: ID of target resource
            details: Additional JSON details
            
        Returns:
            Created AuditLog object
        """
        log_entry = AuditLog(
            tenant_id=tenant_id,
            actor_id=actor_id,
            action=action,
            details=json.dumps(details or {}),
        )
        db.add(log_entry)
        await db.flush()

        logger.info(
            f"Audit logged: action={action}, actor_id={actor_id}, "
            f"tenant_id={tenant_id}, target_type={target_type}, target_id={target_id}"
        )
        return log_entry

    @staticmethod
    async def log_document_upload(
        db: AsyncSession,
        actor_id: UUID,
        tenant_id: UUID,
        group_id: UUID,
        document_id: UUID,
        filename: str,
        size_bytes: int,
        bot_id: UUID | None = None,
    ) -> AuditLog:
        """Log document upload action with provenance."""
        return await AuditService.log_action(
            db=db,
            actor_id=actor_id,
            action="document_uploaded",
            tenant_id=tenant_id,
            group_id=group_id,
            target_type="document",
            target_id=document_id,
            details={
                "filename": filename,
                "size_bytes": size_bytes,
                "bot_id": str(bot_id) if bot_id else None,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

    @staticmethod
    async def log_document_delete(
        db: AsyncSession,
        actor_id: UUID,
        tenant_id: UUID,
        group_id: UUID,
        document_id: UUID,
        filename: str,
    ) -> AuditLog:
        """Log document deletion (soft or hard)."""
        return await AuditService.log_action(
            db=db,
            actor_id=actor_id,
            action="document_deleted",
            tenant_id=tenant_id,
            group_id=group_id,
            target_type="document",
            target_id=document_id,
            details={
                "filename": filename,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

    @staticmethod
    async def log_bot_created(
        db: AsyncSession,
        actor_id: UUID,
        tenant_id: UUID,
        group_id: UUID,
        bot_id: UUID,
        bot_name: str,
    ) -> AuditLog:
        """Log bot creation."""
        return await AuditService.log_action(
            db=db,
            actor_id=actor_id,
            action="bot_created",
            tenant_id=tenant_id,
            group_id=group_id,
            target_type="bot",
            target_id=bot_id,
            details={
                "bot_name": bot_name,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

    @staticmethod
    async def log_group_created(
        db: AsyncSession,
        actor_id: UUID,
        tenant_id: UUID,
        group_id: UUID,
        group_name: str,
    ) -> AuditLog:
        """Log group creation."""
        return await AuditService.log_action(
            db=db,
            actor_id=actor_id,
            action="group_created",
            tenant_id=tenant_id,
            group_id=group_id,
            target_type="group",
            target_id=group_id,
            details={
                "group_name": group_name,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

    @staticmethod
    async def log_member_invited(
        db: AsyncSession,
        actor_id: UUID,
        tenant_id: UUID,
        group_id: UUID,
        invited_user_id: UUID,
        role: str,
    ) -> AuditLog:
        """Log member invitation."""
        return await AuditService.log_action(
            db=db,
            actor_id=actor_id,
            action="member_invited",
            tenant_id=tenant_id,
            group_id=group_id,
            target_type="group_member",
            target_id=invited_user_id,
            details={
                "invited_user_id": str(invited_user_id),
                "role": role,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

    @staticmethod
    async def log_chunk_created(
        db: AsyncSession,
        actor_id: UUID,
        tenant_id: UUID,
        group_id: UUID,
        chunk_id: UUID,
        document_id: UUID,
        bot_id: UUID | None = None,
    ) -> AuditLog:
        """Log chunk creation (during document processing)."""
        return await AuditService.log_action(
            db=db,
            actor_id=actor_id,
            action="chunk_created",
            tenant_id=tenant_id,
            group_id=group_id,
            target_type="chunk",
            target_id=chunk_id,
            details={
                "document_id": str(document_id),
                "bot_id": str(bot_id) if bot_id else None,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

    @staticmethod
    async def get_audit_log(
        db: AsyncSession, tenant_id: UUID, action: str | None = None, limit: int = 100
    ) -> list[AuditLog]:
        """Retrieve audit logs for a tenant with optional action filter."""
        query = select(AuditLog)

        if action:
            query = query.where(AuditLog.action == action)

        query = query.order_by(AuditLog.created_at.desc()).limit(limit)
        return list(await db.scalars(query))

    @staticmethod
    async def get_document_audit_trail(
        db: AsyncSession, document_id: UUID
    ) -> list[AuditLog]:
        """Get all audit entries related to a specific document."""
        return list(
            await db.scalars(
                select(AuditLog)
                .where(AuditLog.details.icontains(str(document_id)))
                .order_by(AuditLog.created_at.desc())
            )
        )
