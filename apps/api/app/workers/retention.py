"""Background worker for data retention and cleanup.

Implements automatic deletion of old chat history, confidence logs, and HITL data
per the data retention policy. Runs daily via APScheduler.

Story 8.5: Data Retention Automation
"""

import logging
from datetime import datetime, timedelta
from sqlalchemy import select, delete, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chat_message import ChatMessage
from app.models.confidence_log import ConfidenceLog, RoutingDecision

logger = logging.getLogger(__name__)


async def cleanup_chat_history(db: AsyncSession, days: int = 90) -> int:
    """Delete chat history older than specified days.
    
    Per Data Retention Policy:
    - Retention: 90 days from creation
    - Reason: Service analytics and UX improvement
    - Compliance: GDPR Article 5 (Storage Limitation)
    
    Args:
        db: Database session
        days: Number of days to retain (default 90)
        
    Returns:
        Number of records deleted
    """
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Count before deletion
        count_result = await db.execute(
            select(ChatMessage).where(ChatMessage.created_at < cutoff_date)
        )
        count_before = len(count_result.scalars().all())
        
        # Delete old records
        result = await db.execute(
            delete(ChatMessage).where(ChatMessage.created_at < cutoff_date)
        )
        await db.commit()
        
        logger.info(
            f"Deleted {count_before} chat history records older than {days} days "
            f"(cutoff: {cutoff_date.isoformat()})"
        )
        return count_before
        
    except Exception as e:
        logger.error(f"Error cleaning up chat history: {e}")
        await db.rollback()
        return 0


async def cleanup_confidence_logs(db: AsyncSession, days: int = 180) -> int:
    """Delete resolved confidence logs older than specified days.
    
    Per Data Retention Policy:
    - Retention: 180 days from resolution
    - Reason: Used for model training; 180-day window sufficient for feedback loop
    - Compliance: GDPR Article 17 (partial anonymization on account deletion)
    
    Args:
        db: Database session
        days: Number of days to retain (default 180)
        
    Returns:
        Number of records deleted
    """
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Count before deletion (only delete resolved logs)
        count_result = await db.execute(
            select(ConfidenceLog).where(
                and_(
                    ConfidenceLog.created_at < cutoff_date,
                    ConfidenceLog.hitl_resolved == True
                )
            )
        )
        count_before = len(count_result.scalars().all())
        
        # Delete old resolved records
        result = await db.execute(
            delete(ConfidenceLog).where(
                and_(
                    ConfidenceLog.created_at < cutoff_date,
                    ConfidenceLog.hitl_resolved == True
                )
            )
        )
        await db.commit()
        
        logger.info(
            f"Deleted {count_before} resolved confidence logs older than {days} days "
            f"(cutoff: {cutoff_date.isoformat()})"
        )
        return count_before
        
    except Exception as e:
        logger.error(f"Error cleaning up confidence logs: {e}")
        await db.rollback()
        return 0


async def cleanup_hitl_data(db: AsyncSession, days: int = 365) -> int:
    """Delete resolved HITL items older than specified days.
    
    Per Data Retention Policy:
    - Retention: 365 days (auto-deleted)
    - Reason: Compliance period for human-in-the-loop feedback
    - Note: Only deletes items marked as resolved/completed (hitl_resolved=True)
    
    Args:
        db: Database session
        days: Number of days to retain (default 365)
        
    Returns:
        Number of records deleted
    """
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Count before deletion (only delete resolved items)
        count_result = await db.execute(
            select(ConfidenceLog).where(
                and_(
                    ConfidenceLog.routing_decision == RoutingDecision.hitl,
                    ConfidenceLog.created_at < cutoff_date,
                    ConfidenceLog.hitl_resolved == True
                )
            )
        )
        count_before = len(count_result.scalars().all())
        
        # Delete old resolved records
        result = await db.execute(
            delete(ConfidenceLog).where(
                and_(
                    ConfidenceLog.routing_decision == RoutingDecision.hitl,
                    ConfidenceLog.created_at < cutoff_date,
                    ConfidenceLog.hitl_resolved == True
                )
            )
        )
        await db.commit()
        
        logger.info(
            f"Deleted {count_before} resolved HITL items older than {days} days "
            f"(cutoff: {cutoff_date.isoformat()})"
        )
        return count_before
        
    except Exception as e:
        logger.error(f"Error cleaning up HITL data: {e}")
        await db.rollback()
        return 0


async def run_all_retention_jobs(db: AsyncSession) -> dict:
    """Run all retention cleanup jobs.
    
    Called daily by APScheduler via main.py lifespan.
    
    Returns:
        Dictionary with counts of deleted records per category
    """
    logger.info("Starting data retention cleanup jobs...")
    
    results = {
        "chat_history_deleted": await cleanup_chat_history(db),
        "confidence_logs_deleted": await cleanup_confidence_logs(db),
        "hitl_items_deleted": await cleanup_hitl_data(db),
        "timestamp": datetime.utcnow().isoformat(),
    }
    
    logger.info(
        f"Data retention cleanup complete: "
        f"chat_history={results['chat_history_deleted']}, "
        f"confidence_logs={results['confidence_logs_deleted']}, "
        f"hitl_items={results['hitl_items_deleted']}"
    )
    
    return results
