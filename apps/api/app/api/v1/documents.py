"""Documents API routes for group-scoped KB management."""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from uuid import UUID
from pathlib import Path
from datetime import datetime
import logging

from app.models import Group, GroupMember, GroupRole
from app.core.auth import get_current_user
from app.core.database import get_db
from app.core.settings import settings
from app.api.v1.schemas import DocumentResponse, ChunkResponse
from app.services.document_group_service import DocumentGroupService
from app.services.audit_service import AuditService
from app import tasks

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/groups/{group_id}/documents", tags=["documents"])


class BulkReprocessRequest(BaseModel):
    document_ids: list[UUID]


async def check_group_access(
    group_id: UUID,
    current_user: dict,
    session: AsyncSession,
    required_role: GroupRole | None = None,
) -> GroupMember:
    """Helper to verify group membership and optionally check role."""
    member = await session.scalar(
        select(GroupMember).where(
            (GroupMember.group_id == group_id)
            & (GroupMember.user_id == UUID(current_user["sub"]))
        )
    )
    if not member:
        raise HTTPException(status_code=403, detail="Not a member of this group")

    if required_role and member.role == GroupRole.OPERATOR:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Requires role: {required_role.value}",
        )

    return member


@router.post("/upload", status_code=status.HTTP_202_ACCEPTED)
async def upload_document(
    group_id: UUID,
    file: UploadFile = File(...),
    bot_id: str | None = Form(None),
    title: str | None = Form(None),
    folder_id: str | None = Form(None),
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    """
    Upload a document to the group's knowledge base.
    
    Returns immediately (202 Accepted) and processes asynchronously.
    Metadata includes: uploader_id, bot_id (optional), group_id, folder_id (optional).
    
    Required permissions: Any group member (Operator+)
    """
    try:
        # Verify group membership (any role)
        await check_group_access(group_id, current_user, session)

        # Verify group exists
        group = await session.scalar(select(Group).where(Group.id == group_id))
        if not group:
            raise HTTPException(status_code=404, detail="Group not found")

        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="File must have a name")

        if file.size and file.size > 100 * 1024 * 1024:  # 100MB limit
            raise HTTPException(status_code=413, detail="File too large (max 100MB)")

        # Save file to storage using local directory
        # Storage path matches DB path: groups/{group_id}/documents/{filename}
        storage_path = f"groups/{group_id}/documents/{file.filename}"
        storage_base = Path("storage") / "documents" / "groups" / str(group_id) / "documents"
        storage_base.mkdir(parents=True, exist_ok=True)
        file_path = storage_base / file.filename

        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)

        # Create document record using service
        new_doc = await DocumentGroupService.create_document(
            db=session,
            tenant_id=UUID(current_user["tenant_id"]),
            group_id=group_id,
            uploader_id=UUID(current_user["sub"]),
            filename=file.filename,
            mime_type=file.content_type or "application/octet-stream",
            size_bytes=len(content),
            storage_path=storage_path,
            title=title or file.filename,
            folder_id=UUID(folder_id) if folder_id else None,
        )

        # Log to audit trail
        await AuditService.log_document_upload(
            db=session,
            actor_id=UUID(current_user["sub"]),
            tenant_id=UUID(current_user["tenant_id"]),
            group_id=group_id,
            document_id=new_doc.id,
            filename=file.filename,
            size_bytes=len(content),
            bot_id=UUID(bot_id) if bot_id else None,
        )

        # Mark as uploaded (will be processed asynchronously)
        await DocumentGroupService.update_document_status(
            db=session,
            doc_id=new_doc.id,
            group_id=group_id,
            tenant_id=UUID(current_user["tenant_id"]),
            status="uploaded",
        )

        await session.commit()

        # Enqueue background processing of the uploaded document
        try:
            tasks.enqueue_group_document_processing(str(new_doc.id))
        except Exception:
            logger.exception("Failed to enqueue group document processing for %s", new_doc.id)

        return {
            "id": str(new_doc.id),
            "filename": new_doc.filename,
            "status": new_doc.status,
            "message": "File uploaded successfully. Processing will begin shortly.",
        }

    except ValueError as e:
        await session.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        await session.rollback()
        logger.exception(f"Error uploading document: {e}")
        raise HTTPException(status_code=500, detail="Failed to upload document")


@router.get("/{doc_id}", response_model=DocumentResponse)
async def get_document(
    group_id: UUID,
    doc_id: UUID,
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    """
    Get document metadata.
    
    User must be a member of the group.
    """
    try:
        # Verify group membership
        await check_group_access(group_id, current_user, session)

        # Get document using service
        doc = await DocumentGroupService.get_document(
            db=session,
            doc_id=doc_id,
            group_id=group_id,
            tenant_id=UUID(current_user["tenant_id"]),
        )

        return doc
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.exception(f"Error retrieving document: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve document")


@router.get("", response_model=list[DocumentResponse])
async def list_documents(
    group_id: UUID,
    include_deleted: bool = False,
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    """
    List documents in the group's knowledge base.
    
    Optionally include soft-deleted documents.
    """
    try:
        # Verify group membership
        await check_group_access(group_id, current_user, session)

        # List documents using service
        docs, total = await DocumentGroupService.list_group_documents(
            db=session,
            group_id=group_id,
            tenant_id=UUID(current_user["tenant_id"]),
            include_deleted=include_deleted,
        )

        return docs
    except Exception as e:
        logger.exception(f"Error listing documents: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve documents")


@router.delete("/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    group_id: UUID,
    doc_id: UUID,
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    """
    Soft-delete a document (marks deleted_at, preserves for audit).
    
    Chunks remain in the KB but are marked as orphaned.
    
    Required permissions: Any group member (Operator+)
    """
    try:
        # Verify group membership (any role can delete their own uploads)
        await check_group_access(group_id, current_user, session)

        # Soft delete using service and retrieve filename for audit
        deleted_doc = await DocumentGroupService.soft_delete_document(
            db=session,
            doc_id=doc_id,
            group_id=group_id,
            tenant_id=UUID(current_user["tenant_id"]),
        )

        # Log to audit trail
        await AuditService.log_document_delete(
            db=session,
            actor_id=UUID(current_user["sub"]),
            tenant_id=UUID(current_user["tenant_id"]),
            group_id=group_id,
            document_id=doc_id,
            filename=deleted_doc.filename,
        )

        await session.commit()

    except ValueError as e:
        await session.rollback()
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        await session.rollback()
        logger.exception(f"Error deleting document: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete document")


@router.get("/{doc_id}/chunks", response_model=list[ChunkResponse])
async def list_document_chunks(
    group_id: UUID,
    doc_id: UUID,
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    """
    List all chunks from a document.
    
    Useful for reviewing processed content and provenance.
    """
    try:

        # Verify group membership
        await check_group_access(group_id, current_user, session)

        # Get document to verify it exists
        await DocumentGroupService.get_document(
            db=session,
            doc_id=doc_id,
            group_id=group_id,
            tenant_id=UUID(current_user["tenant_id"]),
        )

        # List chunks using service
        chunks = await DocumentGroupService.get_document_chunks(
            db=session,
            doc_id=doc_id,
            group_id=group_id,
            tenant_id=UUID(current_user["tenant_id"]),
        )

        return chunks
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.exception(f"Error listing chunks: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve chunks")


@router.post("/bulk-delete", status_code=status.HTTP_204_NO_CONTENT)
async def bulk_delete_documents(
    group_id: UUID,
    payload: BulkReprocessRequest,
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    """Soft-delete multiple documents (max 100) in the group KB."""
    try:
        await check_group_access(group_id, current_user, session)

        if not payload.document_ids:
            raise HTTPException(status_code=400, detail="No document_ids provided")

        if len(payload.document_ids) > 100:
            raise HTTPException(status_code=400, detail="Cannot delete more than 100 documents at once")

        docs = await DocumentGroupService.get_documents_by_ids(
            db=session,
            doc_ids=payload.document_ids,
            group_id=group_id,
            tenant_id=UUID(current_user["tenant_id"]),
        )

        if len(docs) != len(payload.document_ids):
            raise HTTPException(status_code=404, detail="One or more documents not found")

        for d in docs:
            try:
                await DocumentGroupService.soft_delete_document(
                    db=session,
                    doc_id=d.id,
                    group_id=group_id,
                    tenant_id=UUID(current_user["tenant_id"]),
                )
                await AuditService.log_document_delete(
                    db=session,
                    actor_id=UUID(current_user["sub"]),
                    tenant_id=UUID(current_user["tenant_id"]),
                    group_id=group_id,
                    document_id=d.id,
                    filename=d.filename,
                )
            except Exception:
                logger.exception(f"Failed to delete document {d.id}")

        await session.commit()
        return None

    except HTTPException:
        await session.rollback()
        raise
    except Exception as e:
        await session.rollback()
        logger.exception(f"Error bulk deleting documents: {e}")
        raise HTTPException(status_code=500, detail="Failed to bulk delete documents")

@router.post("/bulk-reprocess", status_code=status.HTTP_202_ACCEPTED)
async def bulk_reprocess_documents(
    group_id: UUID,
    payload: BulkReprocessRequest,
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    """Reprocess up to 100 documents in the group knowledge base."""
    try:
        await check_group_access(group_id, current_user, session)

        if not payload.document_ids:
            raise HTTPException(status_code=400, detail="No document_ids provided")

        if len(payload.document_ids) > 100:
            raise HTTPException(status_code=400, detail="Cannot reprocess more than 100 documents at once")

        docs = await DocumentGroupService.get_documents_by_ids(
            db=session,
            doc_ids=payload.document_ids,
            group_id=group_id,
            tenant_id=UUID(current_user["tenant_id"]),
        )

        if len(docs) != len(payload.document_ids):
            raise HTTPException(status_code=404, detail="One or more documents not found")

        invalid_status = [d for d in docs if d.status not in ["ready", "failed", "uploaded"]]
        if invalid_status:
            raise HTTPException(
                status_code=400,
                detail="All documents must be in status ready, failed, or uploaded",
            )

        # Validate source file existence
        base = Path("storage") / "documents"
        for d in docs:
            storage_path = d.storage_path or ""
            local_path = base / storage_path
            if not local_path.exists():
                raise HTTPException(
                    status_code=404,
                    detail=f"Source file not found for document {d.id}",
                )

        # Mark processing
        now_ids = []
        for d in docs:
            d.status = "processing"
            d.updated_at = datetime.utcnow()
            now_ids.append(str(d.id))
        await session.flush()
        await session.commit()

        queued = 0
        for doc_id in now_ids:
            try:
                tasks.enqueue_group_document_reprocessing(doc_id)
                queued += 1
            except Exception:
                logger.exception("Failed to enqueue group document reprocessing for %s", doc_id)

        return {
            "message": f"Queued {queued} document(s) for reprocessing.",
            "queued_count": queued,
            "document_ids": now_ids,
        }

    except HTTPException:
        await session.rollback()
        raise
    except Exception as e:
        await session.rollback()
        logger.exception(f"Error bulk reprocessing documents: {e}")
        raise HTTPException(status_code=500, detail="Failed to bulk reprocess documents")

@router.post("/{doc_id}/reprocess", status_code=status.HTTP_202_ACCEPTED)
async def reprocess_document(
    group_id: UUID,
    doc_id: UUID,
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    """
    Reprocess a document to regenerate chunks and embeddings with rollback.

    Returns immediately (202 Accepted) and processes asynchronously.
    """
    try:
        await check_group_access(group_id, current_user, session)

        doc = await DocumentGroupService.get_document(
            db=session,
            doc_id=doc_id,
            group_id=group_id,
            tenant_id=UUID(current_user["tenant_id"]),
        )

        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")

        if doc.status not in ["ready", "failed", "uploaded"]:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Cannot reprocess document with status '{doc.status}'. "
                    "Only documents with status 'ready', 'failed', or 'uploaded' can be reprocessed."
                ),
            )

        # Ensure source file exists before queuing
        storage_path = doc.storage_path or ""
        base = Path("storage") / "documents"
        local_path = base / storage_path
        if not local_path.exists():
            raise HTTPException(
                status_code=404,
                detail="Source file not found. Cannot reprocess.",
            )

        await DocumentGroupService.update_document_status(
            db=session,
            doc_id=doc_id,
            group_id=group_id,
            tenant_id=UUID(current_user["tenant_id"]),
            status="processing",
        )

        await session.commit()

        try:
            tasks.enqueue_group_document_reprocessing(str(doc_id))
        except Exception:
            logger.exception("Failed to enqueue group document reprocessing for %s", doc_id)

        return {
            "id": str(doc_id),
            "status": "processing",
            "message": "Document queued for reprocessing. This will regenerate all chunks and embeddings.",
            "queued": True,
        }

    except ValueError as e:
        await session.rollback()
        raise HTTPException(status_code=404, detail=str(e))
    except HTTPException:
        await session.rollback()
        raise
    except Exception as e:
        await session.rollback()
        logger.exception(f"Error reprocessing document: {e}")
        raise HTTPException(status_code=500, detail="Failed to reprocess document")