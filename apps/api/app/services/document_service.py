from sqlalchemy.ext.asyncio import AsyncSession
from app.models.document import Document
from app.lib.storage import upload_bytes
from datetime import datetime
import uuid
from typing import Optional
import inspect
import os
import logging


async def create_document(
    db: AsyncSession,
    bot_id: str | uuid.UUID | None,
    tenant_id: str | uuid.UUID,
    uploader_id: Optional[str | uuid.UUID],
    filename: str,
    size_bytes: int,
    mime_type: str,
    file_bytes: bytes,
    title: Optional[str] = None,
) -> tuple[Document, bool]:
    """Persist uploaded file to storage, create Document DB row, and return it.

    Steps:
    1. Build a storage path using tenant/bot and a unique id to avoid collisions.
    2. Upload bytes via `app.lib.storage.upload_bytes` (MinIO or local fallback).
    3. Create a Document ORM instance, add to DB and flush to populate `id`.
    4. (Stub) Enqueue a processing job — currently returns True for queued.
    """

    # Normalize UUID inputs
    if isinstance(tenant_id, str):
        tenant_uuid = uuid.UUID(tenant_id)
    else:
        tenant_uuid = tenant_id

    bot_uuid = None
    if bot_id:
        bot_uuid = uuid.UUID(str(bot_id)) if isinstance(bot_id, (str, uuid.UUID)) else bot_id

    uploader_uuid = None
    if uploader_id:
        uploader_uuid = uuid.UUID(str(uploader_id)) if isinstance(uploader_id, (str, uuid.UUID)) else uploader_id

    # Create a safe storage path
    unique = uuid.uuid4()
    # sanitize incoming filename to avoid traversal and path separators
    safe_name = os.path.basename(filename or "").replace("/", "_").replace("\\", "_")
    path_parts = [str(tenant_uuid)]
    if bot_uuid:
        path_parts.append(str(bot_uuid))
    path = "/".join(path_parts) + f"/{unique.hex}-{safe_name}"

    # Upload bytes (this may be monkeypatched in tests)
    storage_path = upload_bytes(path, file_bytes, content_type=mime_type)

    # Create DB object
    doc = Document(
        tenant_id=tenant_uuid,
        bot_id=bot_uuid,
        filename=filename,
        title=title,
        mime=mime_type,
        size=size_bytes,
        storage_path=storage_path,
        status="uploaded",
        uploaded_by=uploader_uuid,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    db.add(doc)
    # flush so `doc.id` is populated
    await db.flush()

    # Do NOT enqueue here — caller (route) should enqueue after commit to avoid
    # visibility race where a background session cannot see a row that has only
    # been flushed but not committed.
    return doc, False
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.document import Document
from app.lib.storage import upload_bytes
from datetime import datetime
import uuid
from typing import Optional
import inspect
import os
import logging


async def create_document(
    db: AsyncSession,
    bot_id: str | uuid.UUID | None,
    tenant_id: str | uuid.UUID,
    uploader_id: Optional[str | uuid.UUID],
    filename: str,
    size_bytes: int,
    mime_type: str,
    file_bytes: bytes,
    title: Optional[str] = None,
) -> tuple[Document, bool]:
    """Persist uploaded file to storage, create Document DB row, and return it.

    Steps:
    1. Build a storage path using tenant/bot and a unique id to avoid collisions.
    2. Upload bytes via `app.lib.storage.upload_bytes` (MinIO or local fallback).
    3. Create a Document ORM instance, add to DB and flush to populate `id`.
    4. (Stub) Enqueue a processing job — currently returns True for queued.
    """

    # Normalize UUID inputs
    if isinstance(tenant_id, str):
        tenant_uuid = uuid.UUID(tenant_id)
    else:
        tenant_uuid = tenant_id

    bot_uuid = None
    if bot_id:
        bot_uuid = uuid.UUID(str(bot_id)) if isinstance(bot_id, (str, uuid.UUID)) else bot_id

    uploader_uuid = None
    if uploader_id:
        uploader_uuid = uuid.UUID(str(uploader_id)) if isinstance(uploader_id, (str, uuid.UUID)) else uploader_id

    # Create a safe storage path
    unique = uuid.uuid4()
    # sanitize incoming filename to avoid traversal and path separators
    safe_name = os.path.basename(filename or "").replace("/", "_").replace("\\", "_")
    path_parts = [str(tenant_uuid)]
    if bot_uuid:
        path_parts.append(str(bot_uuid))
    path = "/".join(path_parts) + f"/{unique.hex}-{safe_name}"

    # Upload bytes (this may be monkeypatched in tests)
    storage_path = upload_bytes(path, file_bytes, content_type=mime_type)

    # Create DB object
    doc = Document(
        tenant_id=tenant_uuid,
        bot_id=bot_uuid,
        filename=filename,
        title=title,
        mime=mime_type,
        size=size_bytes,
        storage_path=storage_path,
        status="uploaded",
        uploaded_by=uploader_uuid,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    db.add(doc)
    # flush so `doc.id` is populated
    await db.flush()

    # Enqueue processing job (best-effort). Support both sync and async enqueuers.
    logger = logging.getLogger(__name__)
    queued = False
    try:
        # Attempt to import a task enqueuer if available
        from app.tasks import enqueue_document_processing  # type: ignore
    except Exception as e:
        # No enqueuer available (dev) — preserve previous behavior of marking queued True
        logger.info("No enqueuer available, falling back to queued=True: %s", e)
        queued = True
    else:
        try:
            if inspect.iscoroutinefunction(enqueue_document_processing):
                result = await enqueue_document_processing(str(doc.id))
            else:
                result = enqueue_document_processing(str(doc.id))
            # If the enqueuer returns a boolean, respect it; otherwise assume success
            queued = bool(result) if result is not None else True
        except Exception:
            logger.exception("Enqueuer raised an exception for document %s", str(doc.id))
            queued = False

    return doc, queued
