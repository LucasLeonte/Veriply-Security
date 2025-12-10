"""Simple in-process enqueuer for document processing (development).

Provides `enqueue_document_processing(document_id)` used by the upload flow.
This implementation schedules `process_document` on the running event loop and
returns True immediately. If no loop is running, it runs synchronously.
"""
import asyncio
import logging
from typing import Optional
from app.workers.document_processor import process_document
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
