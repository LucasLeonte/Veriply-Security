from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from app.core.database import get_db
from app.api.v1.auth import get_current_user, get_current_tenant
from app.models.user import User
from app.services.document_service import create_document
from sqlalchemy import select
from app.models.document import Document
from typing import Optional
import os
import inspect

router = APIRouter(prefix="/bots", tags=["documents"])


@router.post("/{bot_id}/documents", status_code=201)
async def upload_document(
    bot_id: UUID,
    file: UploadFile = File(...),
    name: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: UUID = Depends(get_current_tenant),
):
    # Basic validation similar to story requirements; rely on settings where available
    try:
        from app.core.settings import settings  # type: ignore
    except Exception:
        class _S:
            ALLOWED_FILE_TYPES_LIST = ["pdf", "docx", "txt", "csv"]
            MAX_UPLOAD_SIZE_BYTES = 25 * 1024 * 1024
        settings = _S()

    allowed = set(settings.ALLOWED_FILE_TYPES_LIST)
    ext = (file.filename or "").split(".")[-1].lower()
    if ext not in allowed:
        raise HTTPException(status_code=415, detail=f"Unsupported file type: {ext}")

    content = await file.read()
    if len(content) > settings.MAX_UPLOAD_SIZE_BYTES:
        raise HTTPException(status_code=413, detail="File too large")

    safe_filename = os.path.basename(file.filename or "")

    doc, queued = await create_document(
        db=db,
        bot_id=bot_id,
        tenant_id=tenant_id,
        uploader_id=(current_user.get('sub') if isinstance(current_user, dict) else getattr(current_user, 'id', None)),
        filename=safe_filename,
        size_bytes=len(content),
        mime_type=file.content_type or "application/octet-stream",
        file_bytes=content,
        title=name,
    )

    try:
        await db.commit()
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to save document")
    # After commit, enqueue processing so background sessions can see the row
    queued_after = False
    try:
        from app.tasks import enqueue_document_processing  # type: ignore
    except Exception:
        queued_after = False
    else:
        try:
            if inspect.iscoroutinefunction(enqueue_document_processing):
                queued_after = await enqueue_document_processing(str(doc.id))
            else:
                queued_after = enqueue_document_processing(str(doc.id))
        except Exception:
            queued_after = False

    # Return both `id` (primary) and `document_id` for backward compatibility
    return {"id": str(doc.id), "document_id": str(doc.id), "status": doc.status, "queued": bool(queued_after)}



@router.get("/{bot_id}/documents")
async def list_bot_documents(
    bot_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: UUID = Depends(get_current_tenant),
):
    """List documents for a given bot (tenant-isolated)."""
    # Query for documents that belong to this tenant and bot
    q = await db.execute(select(Document).where(Document.bot_id == bot_id).where(Document.tenant_id == tenant_id).order_by(Document.created_at.desc()))
    rows = q.scalars().all()
    result = []
    for d in rows:
        result.append({
            "id": str(d.id),
            "filename": d.filename,
            "status": d.status,
            "storage_path": d.storage_path,
            "created_at": d.created_at.isoformat() if d.created_at else None,
        })
    return result
from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from app.core.database import get_db
from app.api.v1.auth import get_current_user, get_current_tenant
from app.models.user import User
from app.services.document_service import create_document
from sqlalchemy import select
from app.models.document import Document
from typing import Optional
import os

router = APIRouter(prefix="/bots", tags=["documents"])


@router.post("/{bot_id}/documents", status_code=201)
async def upload_document(
    bot_id: UUID,
    file: UploadFile = File(...),
    name: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: UUID = Depends(get_current_tenant),
):
    # Basic validation similar to story requirements; rely on settings where available
    try:
        from app.core.settings import settings  # type: ignore
    except Exception:
        class _S:
            ALLOWED_FILE_TYPES_LIST = ["pdf", "docx", "txt", "csv"]
            MAX_UPLOAD_SIZE_BYTES = 25 * 1024 * 1024
        settings = _S()

    allowed = set(settings.ALLOWED_FILE_TYPES_LIST)
    ext = (file.filename or "").split(".")[-1].lower()
    if ext not in allowed:
        raise HTTPException(status_code=415, detail=f"Unsupported file type: {ext}")

    content = await file.read()
    if len(content) > settings.MAX_UPLOAD_SIZE_BYTES:
        raise HTTPException(status_code=413, detail="File too large")

    safe_filename = os.path.basename(file.filename or "")

    doc, queued = await create_document(
        db=db,
        bot_id=bot_id,
        tenant_id=tenant_id,
        uploader_id=(current_user.get('sub') if isinstance(current_user, dict) else getattr(current_user, 'id', None)),
        filename=safe_filename,
        size_bytes=len(content),
        mime_type=file.content_type or "application/octet-stream",
        file_bytes=content,
        title=name,
    )

    try:
        await db.commit()
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to save document")

    # Return both `id` (primary) and `document_id` for backward compatibility
    return {"id": str(doc.id), "document_id": str(doc.id), "status": doc.status, "queued": bool(queued)}



@router.get("/{bot_id}/documents")
async def list_bot_documents(
    bot_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: UUID = Depends(get_current_tenant),
):
    """List documents for a given bot (tenant-isolated)."""
    # Query for documents that belong to this tenant and bot
    q = await db.execute(select(Document).where(Document.bot_id == bot_id).where(Document.tenant_id == tenant_id).order_by(Document.created_at.desc()))
    rows = q.scalars().all()
    result = []
    for d in rows:
        result.append({
            "id": str(d.id),
            "filename": d.filename,
            "status": d.status,
            "storage_path": d.storage_path,
            "created_at": d.created_at.isoformat() if d.created_at else None,
        })
    return result
