"""Simple in-process enqueuer for document processing (development).

Provides `enqueue_document_processing(document_id)` used by the upload flow.
This implementation schedules `process_document` on the running event loop and
returns True immediately. If no loop is running, it runs synchronously.
"""
import asyncio
import logging
from app.workers.document_processor import process_document
from app.workers.group_document_processor import (
    process_group_document,
    process_group_document_reprocess,
)
from app.core.database import AsyncSessionLocal

logger = logging.getLogger(__name__)


def enqueue_document_processing(document_id: str) -> bool:
    async def _runner():
        try:
            async with AsyncSessionLocal() as session:
                await process_document(document_id, db_session=session)
        except Exception as e:
            logger.exception("Background processing failed for %s: %s", document_id, e)

    try:
        loop = asyncio.get_running_loop()
        loop.create_task(_runner())
        return True
    except RuntimeError:
        # No running loop — run synchronously
        try:
            asyncio.run(_runner())
            return True
        except Exception:
            logger.exception("Synchronous processing failed for %s", document_id)
            return False


async def enqueue_document_processing_async(document_id: str) -> bool:
    async with AsyncSessionLocal() as session:
        await process_document(document_id, db_session=session)
    return True


def enqueue_group_document_processing(document_id: str) -> bool:
    """Schedule processing of a group-scoped document on the running loop."""
    async def _runner():
        try:
            async with AsyncSessionLocal() as session:
                await process_group_document(document_id, db_session=session)
        except Exception as e:
            logger.exception("Background group processing failed for %s: %s", document_id, e)

    try:
        loop = asyncio.get_running_loop()
        loop.create_task(_runner())
        return True
    except RuntimeError:
        try:
            asyncio.run(_runner())
            return True
        except Exception:
            logger.exception("Synchronous group processing failed for %s", document_id)
            return False


def enqueue_group_document_reprocessing(document_id: str) -> bool:
    """Schedule reprocessing of an existing group document with rollback safety."""

    async def _runner():
        try:
            async with AsyncSessionLocal() as session:
                await process_group_document_reprocess(document_id, db_session=session)
        except Exception as e:
            logger.exception("Background group reprocessing failed for %s: %s", document_id, e)

    try:
        loop = asyncio.get_running_loop()
        loop.create_task(_runner())
        return True
    except RuntimeError:
        try:
            asyncio.run(_runner())
            return True
        except Exception:
            logger.exception("Synchronous group reprocessing failed for %s", document_id)
            return False

