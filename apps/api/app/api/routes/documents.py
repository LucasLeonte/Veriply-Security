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
    BulkDeleteRequest,
    BulkDeleteResponse,
)
from pydantic import BaseModel
from typing import Optional, List
import os
import inspect
import math
import logging

logger = logging.getLogger(__name__)

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
            uploader_id=current_user.id,
            filename=safe_filename,
            size_bytes=len(content),
            mime_type=file.content_type or "application/octet-stream",
            file_bytes=content,
            title=None,
        )
        uploaded_docs.append(doc)

    try:
        await db.commit()
    except Exception as e:
        await db.rollback()
        logger.exception(f"Failed to commit document to database: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to save document: {str(e)}")
    
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
    # Base query - use group_id instead of bot_id (bot_id field was refactored to group_id)
    base_query = select(Document).where(
        Document.group_id == bot_id,
        Document.tenant_id == tenant_id
    )
    
    # Apply search filter
    if search:
        base_query = base_query.where(Document.title.ilike(f"%{search}%"))
    
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
            bot_id=doc.group_id,  # Use group_id instead of bot_id for backward compatibility
            filename=doc.title,  # Use title directly (property also works)
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
        bot_id=doc.group_id,  # Use group_id instead of bot_id for backward compatibility
        filename=doc.title,
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
    
    # Cannot delete while processing
    if doc.status == "processing":
        raise HTTPException(
            status_code=409,
            detail="Cannot delete document while processing. Please wait."
        )
    
    # Store storage path before deletion
    storage_path = doc.storage_path
    
    # Delete chunks first (explicit deletion for logging/cleanup)
    chunks_query = select(Chunk).where(Chunk.document_id == document_id)
    chunks_result = await db.execute(chunks_query)
    chunks = chunks_result.scalars().all()
    
    for chunk in chunks:
        await db.delete(chunk)
    
    # Delete document record
    await db.delete(doc)
    
    try:
        await db.commit()
        logger.info(f"Deleted document {document_id} with {len(chunks)} chunks")
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to delete document {document_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete document")
    
    # Enqueue async cleanup job for storage (fire-and-forget)
    if storage_path:
        try:
            from app.services.deletion_service import enqueue_storage_cleanup
            enqueue_storage_cleanup(storage_path)
        except Exception as e:
            # Don't fail the request if storage cleanup fails
            logger.warning(f"Failed to enqueue storage cleanup for {storage_path}: {e}")
    
    return None


@documents_router.post("/bulk-delete", response_model=BulkDeleteResponse)
async def bulk_delete_documents(
    request: BulkDeleteRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: UUID = Depends(get_current_tenant),
):
    """Bulk delete documents (max 100 at once, tenant-isolated)."""
    document_ids = request.document_ids
    
    # Validate max 100 documents
    if len(document_ids) > 100:
        raise HTTPException(
            status_code=400,
            detail="Maximum 100 documents can be deleted at once"
        )
    
    if len(document_ids) == 0:
        raise HTTPException(
            status_code=400,
            detail="No documents specified for deletion"
        )
    
    # Verify all documents exist and belong to tenant
    query = select(Document).where(
        Document.id.in_(document_ids),
        Document.tenant_id == tenant_id
    )
    result = await db.execute(query)
    docs = result.scalars().all()
    
    if len(docs) != len(document_ids):
        found_ids = {str(doc.id) for doc in docs}
        missing_ids = [str(doc_id) for doc_id in document_ids if str(doc_id) not in found_ids]
        raise HTTPException(
            status_code=404,
            detail=f"Some documents not found or don't belong to your organization: {missing_ids[:5]}"
        )
    
    # Check for processing documents
    processing_docs = [doc for doc in docs if doc.status == "processing"]
    if processing_docs:
        raise HTTPException(
            status_code=409,
            detail=f"Cannot delete {len(processing_docs)} document(s) that are currently processing"
        )
    
    # Collect storage paths for cleanup
    storage_paths = [doc.storage_path for doc in docs if doc.storage_path]
    
    # Delete all chunks for these documents
    chunks_query = select(Chunk).where(Chunk.document_id.in_(document_ids))
    chunks_result = await db.execute(chunks_query)
    chunks = chunks_result.scalars().all()
    
    for chunk in chunks:
        await db.delete(chunk)
    
    # Delete all documents
    for doc in docs:
        await db.delete(doc)
    
    try:
        await db.commit()
        logger.info(
            f"Bulk deleted {len(docs)} documents with {len(chunks)} total chunks "
            f"by user {current_user.get('sub') if isinstance(current_user, dict) else getattr(current_user, 'id', 'unknown')}"
        )
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to bulk delete documents: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete documents")
    
    # Enqueue async cleanup jobs for storage (fire-and-forget)
    cleanup_count = 0
    if storage_paths:
        try:
            from app.services.deletion_service import enqueue_bulk_storage_cleanup
            cleanup_count = enqueue_bulk_storage_cleanup(storage_paths)
        except Exception as e:
            logger.warning(f"Failed to enqueue bulk storage cleanup: {e}")
    
    return BulkDeleteResponse(
        message=f"Successfully deleted {len(docs)} document(s)",
        queued_count=cleanup_count,
        document_ids=[str(doc_id) for doc_id in document_ids]
    )


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


class MoveDocumentRequest(BaseModel):
    """Request schema for moving a document to a folder"""
    folder_id: Optional[UUID] = None


@documents_router.patch("/{document_id}/move", response_model=DocumentResponse)
async def move_document_to_folder(
    document_id: UUID,
    request: MoveDocumentRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: UUID = Depends(get_current_tenant),
):
    """Move a document to a folder or root (tenant-isolated)."""
    # Verify document exists and belongs to tenant
    query = select(Document).where(
        Document.id == document_id,
        Document.tenant_id == tenant_id
    )
    result = await db.execute(query)
    doc = result.scalar_one_or_none()
    
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Update folder_id
    doc.folder_id = request.folder_id
    
    try:
        await db.commit()
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to move document")
    
    # Refresh to get updated data
    await db.refresh(doc)
    
    # Get chunk count
    chunk_count_query = select(func.count()).where(Chunk.document_id == doc.id)
    chunk_result = await db.execute(chunk_count_query)
    chunk_count = chunk_result.scalar() or 0
    
    return DocumentResponse(
        id=doc.id,
        bot_id=doc.group_id,
        filename=doc.title,
        file_size=doc.size or 0,
        status=doc.status,
        chunk_count=chunk_count,
        created_at=doc.created_at,
        updated_at=doc.updated_at,
        title=doc.title,
        mime_type=doc.mime,
        storage_path=doc.storage_path,
    )


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
