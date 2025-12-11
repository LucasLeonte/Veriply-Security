"""Document service with group scoping and provenance tracking."""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from uuid import UUID
from datetime import datetime
from pathlib import Path
import logging

from app.models import Document, Chunk, Group
from app.core.settings import settings

logger = logging.getLogger(__name__)


class DocumentGroupService:
    """Service for group-scoped document operations with provenance."""

    @staticmethod
    async def create_document(
        db: AsyncSession,
        tenant_id: UUID,
        group_id: UUID,
        uploader_id: UUID,
        filename: str,
        mime_type: str,
        size_bytes: int,
        storage_path: str,
        bot_id: UUID | None = None,
        title: str | None = None,
    ) -> Document:
        """
        Create a document record in the group KB with provenance.
        
        Args:
            db: Database session
            tenant_id: Tenant ID
            group_id: Group ID
            uploader_id: User who uploaded
            filename: Original filename
            mime_type: MIME type
            size_bytes: File size
            storage_path: Path where file is stored
            bot_id: Optional bot that triggered upload
            title: Optional title (defaults to filename)
            
        Returns:
            Created Document object
        """
        # Verify group exists
        group = await db.scalar(
            select(Group).where(
                (Group.id == group_id) & (Group.tenant_id == tenant_id)
            )
        )
        if not group:
            raise ValueError(f"Group {group_id} not found")

        doc = Document(
            tenant_id=tenant_id,
            group_id=group_id,
            bot_id=bot_id,
            filename=filename,
            title=title or filename,
            mime=mime_type,
            size=size_bytes,
            storage_path=storage_path,
            status="uploaded",
            uploader_id=uploader_id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(doc)
        await db.flush()

        logger.info(
            f"Document created: id={doc.id}, group_id={group_id}, "
            f"uploader_id={uploader_id}, filename={filename}"
        )
        return doc

    @staticmethod
    async def get_document(
        db: AsyncSession, doc_id: UUID, group_id: UUID, tenant_id: UUID
    ) -> Document | None:
        """Get document with group and tenant isolation."""
        return await db.scalar(
            select(Document).where(
                (Document.id == doc_id)
                & (Document.group_id == group_id)
                & (Document.tenant_id == tenant_id)
                & (Document.deleted_at == None)
            )
        )

    @staticmethod
    async def list_group_documents(
        db: AsyncSession,
        group_id: UUID,
        tenant_id: UUID,
        include_deleted: bool = False,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[Document], int]:
        """List documents in group KB."""
        # Build base query
        query = select(Document).where(
            (Document.group_id == group_id) & (Document.tenant_id == tenant_id)
        )

        if not include_deleted:
            query = query.where(Document.deleted_at == None)

        # Count
        count_query = select(func.count(Document.id)).where(
            (Document.group_id == group_id) & (Document.tenant_id == tenant_id)
        )
        if not include_deleted:
            count_query = count_query.where(Document.deleted_at == None)

        total = await db.scalar(count_query)

        # List with pagination
        docs = list(
            await db.scalars(
                query.order_by(Document.created_at.desc())
                .limit(limit)
                .offset(offset)
            )
        )

        return docs, total or 0

    @staticmethod
    async def soft_delete_document(
        db: AsyncSession, doc_id: UUID, group_id: UUID, tenant_id: UUID
    ) -> Document:
        """
        Soft-delete a document (mark deleted_at).
        
        Note: Chunks remain in KB but are orphaned. Document can be
        restored by clearing deleted_at if needed.
        """
        doc = await DocumentGroupService.get_document(db, doc_id, group_id, tenant_id)
        if not doc:
            raise ValueError(f"Document {doc_id} not found")

        doc.deleted_at = datetime.utcnow()
        await db.flush()
        logger.info(f"Document soft-deleted: id={doc_id}, group_id={group_id}")
        return doc

    @staticmethod
    async def hard_delete_document(
        db: AsyncSession, doc_id: UUID, group_id: UUID, tenant_id: UUID
    ) -> bool:
        """
        Permanently delete a document and its chunks.
        
        This is destructive - use with caution (typically for cleanup/admin).
        """
        doc = await db.scalar(
            select(Document).where(
                (Document.id == doc_id)
                & (Document.group_id == group_id)
                & (Document.tenant_id == tenant_id)
            )
        )
        if not doc:
            raise ValueError(f"Document {doc_id} not found")

        await db.delete(doc)
        await db.flush()
        logger.info(f"Document hard-deleted: id={doc_id}, group_id={group_id}")
        return True

    @staticmethod
    async def get_document_chunks(
        db: AsyncSession,
        doc_id: UUID,
        group_id: UUID,
        tenant_id: UUID,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[Chunk], int]:
        """Get all chunks from a document with provenance."""
        # Verify document exists
        doc = await DocumentGroupService.get_document(db, doc_id, group_id, tenant_id)
        if not doc:
            raise ValueError(f"Document {doc_id} not found")

        # Count chunks
        total = await db.scalar(
            select(func.count(Chunk.id)).where(Chunk.document_id == doc_id)
        )

        # List chunks
        chunks = list(
            await db.scalars(
                select(Chunk)
                .where(Chunk.document_id == doc_id)
                .order_by(Chunk.chunk_index)
                .limit(limit)
                .offset(offset)
            )
        )

        return chunks, total or 0

    @staticmethod
    async def update_document_status(
        db: AsyncSession,
        doc_id: UUID,
        group_id: UUID,
        tenant_id: UUID,
        status: str,
    ) -> Document:
        """Update document processing status."""
        doc = await DocumentGroupService.get_document(db, doc_id, group_id, tenant_id)
        if not doc:
            raise ValueError(f"Document {doc_id} not found")

        doc.status = status
        doc.updated_at = datetime.utcnow()
        await db.flush()
        logger.info(f"Document status updated: id={doc_id}, status={status}")
        return doc

    @staticmethod
    async def get_group_kb_stats(
        db: AsyncSession, group_id: UUID, tenant_id: UUID
    ) -> dict:
        """Get KB statistics for a group."""
        # Count documents (active only)
        doc_count = await db.scalar(
            select(func.count(Document.id)).where(
                (Document.group_id == group_id)
                & (Document.tenant_id == tenant_id)
                & (Document.deleted_at == None)
            )
        )

        # Count chunks
        chunk_count = await db.scalar(
            select(func.count(Chunk.id)).where(
                (Chunk.group_id == group_id) & (Chunk.tenant_id == tenant_id)
            )
        )

        # Sum document sizes
        total_size = await db.scalar(
            select(func.sum(Document.size)).where(
                (Document.group_id == group_id)
                & (Document.tenant_id == tenant_id)
                & (Document.deleted_at == None)
            )
        )

        return {
            "documents": doc_count or 0,
            "chunks": chunk_count or 0,
            "total_size_bytes": total_size or 0,
        }

    @staticmethod
    async def get_document_provenance(
        db: AsyncSession, doc_id: UUID, group_id: UUID, tenant_id: UUID
    ) -> dict | None:
        """Get document provenance info (who uploaded, when, from which bot)."""
        doc = await DocumentGroupService.get_document(db, doc_id, group_id, tenant_id)
        if not doc:
            return None

        return {
            "id": str(doc.id),
            "filename": doc.filename,
            "uploader_id": str(doc.uploader_id),
            "bot_id": str(doc.bot_id) if doc.bot_id else None,
            "uploaded_at": doc.created_at.isoformat(),
            "status": doc.status,
            "size_bytes": doc.size,
            "mime_type": doc.mime,
        }
