"""
Bot Access Audit Logging
Logs all bot access for compliance and security monitoring.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import insert
from uuid import UUID, uuid4
from datetime import datetime
from app.models.audit_log import AuditLog
import logging
import json

logger = logging.getLogger(__name__)


class BotAccessAudit:
    """Service for logging bot access events"""
    
    @staticmethod
    async def log_bot_access(
        db: AsyncSession,
        user_id: UUID,
        bot_id: UUID,
        tenant_id: UUID,
        action: str,
        status: str = "success",
        details: dict | None = None,
        ip_address: str | None = None,
    ) -> None:
        """
        Log a bot access event for audit trail.
        
        Args:
            db: Database session
            user_id: User performing the action
            bot_id: Bot being accessed
            tenant_id: Tenant context
            action: Action performed (view, search, query, edit, delete)
            status: success or failed
            details: Additional context as dict
            ip_address: Client IP address (if available)
        """
        try:
            audit_details = {
                "action": action,
                "status": status,
                "bot_id": str(bot_id),
                **(details or {}),
            }
            if ip_address:
                audit_details["ip_address"] = ip_address
            
            log_entry = AuditLog(
                id=uuid4(),
                tenant_id=tenant_id,
                actor_id=user_id,
                target_user_id=None,  # Not applicable for bot access
                action=f"bot_access_{action}",
                details=json.dumps(audit_details),
                created_at=datetime.utcnow(),
            )
            
            db.add(log_entry)
            # Use flush instead of commit - caller controls transaction
            await db.flush()
            
        except Exception as e:
            logger.exception(
                f"Failed to log bot access: user_id={user_id}, bot_id={bot_id}, action={action}",
                exc_info=e
            )
            # Don't raise - logging errors shouldn't break the operation
    
    @staticmethod
    async def log_unauthorized_access(
        db: AsyncSession,
        user_id: UUID,
        bot_id: UUID,
        tenant_id: UUID,
        action: str,
        ip_address: str | None = None,
    ) -> None:
        """
        Log an unauthorized access attempt (security event).
        
        Args:
            db: Database session
            user_id: User attempting access
            bot_id: Bot being accessed
            tenant_id: Tenant context
            action: Attempted action
            ip_address: Client IP address
        """
        await BotAccessAudit.log_bot_access(
            db=db,
            user_id=user_id,
            bot_id=bot_id,
            tenant_id=tenant_id,
            action=action,
            status="unauthorized",
            details={"security_event": "unauthorized_access_attempt"},
            ip_address=ip_address,
        )
    
    @staticmethod
    async def log_isolation_violation(
        db: AsyncSession,
        user_id: UUID,
        bot_id_attempted: UUID,
        bot_id_owned: UUID,
        tenant_id: UUID,
        action: str,
        ip_address: str | None = None,
    ) -> None:
        """
        Log a bot isolation violation (critical security event).
        
        Args:
            db: Database session
            user_id: User
            bot_id_attempted: Bot user tried to access
            bot_id_owned: Bot user actually owns
            tenant_id: Tenant context
            action: Attempted action
            ip_address: Client IP address
        """
        await BotAccessAudit.log_bot_access(
            db=db,
            user_id=user_id,
            bot_id=bot_id_attempted,
            tenant_id=tenant_id,
            action=action,
            status="isolation_violation",
            details={
                "security_event": "cross_bot_access_attempt",
                "bot_attempted": str(bot_id_attempted),
                "bot_owned": str(bot_id_owned),
            },
            ip_address=ip_address,
        )
