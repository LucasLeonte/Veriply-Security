from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Query
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from app.core.database import get_db
from app.api.v1.auth import get_current_user, get_current_tenant
from app.models.user import User
from app.services.document_service import create_document
from sqlalchemy import select, func
from app.models.document import Document
from app.models.chunk import Chunk
from app.schemas.document import (
    DocumentResponse,
    DocumentUploadResponse,
    DocumentListResponse,
    ChunkResponse,
    ChunkListResponse,
)
from typing import Optional, List
import os
import inspect
import math

# Router for bot-scoped endpoints
router = APIRouter(prefix="/bots", tags=["documents"])

# Router for document-specific endpoints
documents_router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/{bot_id}/documents", status_code=201, response_model=DocumentUploadResponse)
async def upload_document(
    bot_id: UUID,
    files: List[UploadFile] = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: UUID = Depends(get_current_tenant),
):
    """Upload one or multiple documents to a bot's knowledge base."""
    # Basic validation similar to story requirements; rely on settings where available
    try:
        from app.core.settings import settings  # type: ignore
    except Exception:
        class _S:
            ALLOWED_FILE_TYPES_LIST = ["pdf", "docx", "txt", "csv", "md"]
            MAX_UPLOAD_SIZE_BYTES = 10 * 1024 * 1024  # 10MB per file
        settings = _S()

    allowed = set(settings.ALLOWED_FILE_TYPES_LIST)
    
    # Process each file
    uploaded_docs = []
    for file in files:
        ext = (file.filename or "").split(".")[-1].lower()
        if ext not in allowed:
            raise HTTPException(status_code=415, detail=f"Unsupported file type: {ext}")

        content = await file.read()
        
        # Enforce file size limit on backend
        if len(content) > settings.MAX_UPLOAD_SIZE_BYTES:
            raise HTTPException(
                status_code=413, 
                detail=f"File {file.filename} exceeds maximum size of {settings.MAX_UPLOAD_SIZE_BYTES} bytes"
            )

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
            title=None,
        )
        uploaded_docs.append(doc)

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
        for doc in uploaded_docs:
            try:
                if inspect.iscoroutinefunction(enqueue_document_processing):
                    queued_after = await enqueue_document_processing(str(doc.id))
                else:
                    queued_after = enqueue_document_processing(str(doc.id))
            except Exception:
                queued_after = False

    # Return first document (for single upload compatibility)
    first_doc = uploaded_docs[0]
    return DocumentUploadResponse(
        id=first_doc.id,
        document_id=first_doc.id,
        status=first_doc.status,
        queued=bool(queued_after)
    )


@router.get("/{bot_id}/documents", response_model=DocumentListResponse)
async def list_bot_documents(
    bot_id: UUID,
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search by filename"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: UUID = Depends(get_current_tenant),
):
    """List documents for a given bot with pagination and search (tenant-isolated)."""
    # Base query
    base_query = select(Document).where(
        Document.bot_id == bot_id,
        Document.tenant_id == tenant_id
    )
    
    # Apply search filter
    if search:
        base_query = base_query.where(Document.filename.ilike(f"%{search}%"))
    
    # Get total count
    count_query = select(func.count()).select_from(base_query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    # Calculate pagination
    total_pages = math.ceil(total / page_size) if total > 0 else 0
    offset = (page - 1) * page_size
    
    # Get paginated results
    query = base_query.order_by(Document.created_at.desc()).offset(offset).limit(page_size)
    result = await db.execute(query)
    documents = result.scalars().all()
    
    # Get chunk counts for all documents in a single query (fix N+1 problem)
    if documents:
        doc_ids = [doc.id for doc in documents]
        chunk_counts_query = select(
            Chunk.document_id,
            func.count(Chunk.id).label('chunk_count')
        ).where(
            Chunk.document_id.in_(doc_ids)
        ).group_by(Chunk.document_id)
        
        chunk_counts_result = await db.execute(chunk_counts_query)
        chunk_count_map = {row.document_id: row.chunk_count for row in chunk_counts_result}
    else:
        chunk_count_map = {}
    
    # Build response objects
    doc_responses = []
    for doc in documents:
        chunk_count = chunk_count_map.get(doc.id, 0)
        
        doc_responses.append(DocumentResponse(
            id=doc.id,
            bot_id=doc.bot_id,
            filename=doc.filename,
            file_size=doc.size or 0,
            status=doc.status,
            chunk_count=chunk_count,
            created_at=doc.created_at,
            updated_at=doc.updated_at,
            title=doc.title,
            mime_type=doc.mime,
            storage_path=doc.storage_path,
        ))
    
    return DocumentListResponse(
        documents=doc_responses,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


# Document-specific endpoints (not bot-scoped)
@documents_router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: UUID = Depends(get_current_tenant),
):
    """Get a specific document by ID (tenant-isolated)."""
    query = select(Document).where(
        Document.id == document_id,
        Document.tenant_id == tenant_id
    )
    result = await db.execute(query)
    doc = result.scalar_one_or_none()
    
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Get chunk count
    chunk_count_query = select(func.count()).where(Chunk.document_id == doc.id)
    chunk_result = await db.execute(chunk_count_query)
    chunk_count = chunk_result.scalar() or 0
    
    return DocumentResponse(
        id=doc.id,
        bot_id=doc.bot_id,
        filename=doc.filename,
        file_size=doc.size or 0,
        status=doc.status,
        chunk_count=chunk_count,
        created_at=doc.created_at,
        updated_at=doc.updated_at,
        title=doc.title,
        mime_type=doc.mime,
        storage_path=doc.storage_path,
    )


@documents_router.delete("/{document_id}", status_code=204)
async def delete_document(
    document_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: UUID = Depends(get_current_tenant),
):
    """Delete a document and its chunks (tenant-isolated, cascades to chunks)."""
    # Verify document exists and belongs to tenant
    query = select(Document).where(
        Document.id == document_id,
        Document.tenant_id == tenant_id
    )
    result = await db.execute(query)
    doc = result.scalar_one_or_none()
    
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Delete document (chunks cascade automatically via FK constraint)
    await db.delete(doc)
    
    try:
        await db.commit()
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to delete document")
    
    return None


@documents_router.post("/{document_id}/reprocess", status_code=202)
async def reprocess_document(
    document_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: UUID = Depends(get_current_tenant),
):
    """Reprocess a failed or processed document (tenant-isolated)."""
    # Verify document exists and belongs to tenant
    query = select(Document).where(
        Document.id == document_id,
        Document.tenant_id == tenant_id
    )
    result = await db.execute(query)
    doc = result.scalar_one_or_none()
    
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Update status to pending for reprocessing
    doc.status = "pending"
    
    try:
        await db.commit()
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to update document status")
    
    # Enqueue processing job
    queued = False
    try:
        from app.tasks import enqueue_document_processing  # type: ignore
    except Exception:
        pass
    else:
        try:
            if inspect.iscoroutinefunction(enqueue_document_processing):
                queued = await enqueue_document_processing(str(doc.id))
            else:
                queued = enqueue_document_processing(str(doc.id))
        except Exception:
            pass
    
    return {"id": str(doc.id), "status": doc.status, "queued": bool(queued)}


@documents_router.get("/{document_id}/chunks", response_model=ChunkListResponse)
async def get_document_chunks(
    document_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: UUID = Depends(get_current_tenant),
):
    """Get all chunks for a specific document (tenant-isolated via document)."""
    # Verify document exists and belongs to tenant
    doc_query = select(Document).where(
        Document.id == document_id,
        Document.tenant_id == tenant_id
    )
    doc_result = await db.execute(doc_query)
    doc = doc_result.scalar_one_or_none()
    
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Get chunks ordered by index
    chunks_query = select(Chunk).where(
        Chunk.document_id == document_id
    ).order_by(Chunk.chunk_index)
    
    chunks_result = await db.execute(chunks_query)
    chunks = chunks_result.scalars().all()
    
    chunk_responses = [
        ChunkResponse(
            id=chunk.id,
            document_id=chunk.document_id,
            chunk_index=chunk.chunk_index,
            content=chunk.content,
            page_number=chunk.page_number,
            created_at=chunk.created_at,
        )
        for chunk in chunks
    ]
    
    return ChunkListResponse(
        chunks=chunk_responses,
        total=len(chunk_responses),
    )
