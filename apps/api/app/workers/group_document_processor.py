import logging
import os
import io
import uuid
import asyncio
from datetime import datetime
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document
from app.models.chunk import Chunk
from app.services.embedding_service import EmbeddingService, EmbeddingError

logger = logging.getLogger(__name__)


def _simple_text_extractor(file_bytes: bytes, filename: Optional[str], mime: Optional[str]) -> str:
    """Best-effort text extraction for PDF/DOCX/Plain text.

    Falls back to utf-8/latin-1 decode if specialized libs not available.
    """
    # PDF
    if (mime and "pdf" in mime.lower()) or (filename and filename.lower().endswith(".pdf")):
        try:
            from PyPDF2 import PdfReader
            reader = PdfReader(io.BytesIO(file_bytes))
            texts: List[str] = []
            for p in reader.pages:
                try:
                    texts.append(p.extract_text() or "")
                except Exception:
                    texts.append("")
            return "\n\n".join(texts)
        except Exception:
            logger.warning("PyPDF2 unavailable/failed; falling back to plain decode")

    # DOCX
    if filename and filename.lower().endswith(".docx"):
        try:
            from docx import Document as DocxDocument
            doc = DocxDocument(io.BytesIO(file_bytes))
            paragraphs = [p.text for p in doc.paragraphs]
            return "\n\n".join(paragraphs)
        except Exception:
            logger.warning("python-docx unavailable/failed; falling back to plain decode")

    # Plain text fallback
    for enc in ("utf-8", "latin-1"):
        try:
            return file_bytes.decode(enc)
        except Exception:
            pass
    return ""


def _sanitize_text(text: str) -> str:
    """Remove characters that Postgres rejects (e.g., NULs)."""
    return text.replace("\x00", "")


def _chunk_text(text: str, max_words: int = 200, overlap: int = 30) -> List[str]:
    words = text.split()
    if not words:
        return []
    chunks: List[str] = []
    i = 0
    n = len(words)
    while i < n:
        end = min(i + max_words, n)
        chunk = " ".join(words[i:end])
        chunks.append(chunk)
        if end == n:
            break
        i = max(0, end - overlap)
    return chunks


async def _read_file_bytes(storage_path: str) -> bytes:
    """Read bytes from storage path used by group upload.

    Group uploads save under storage/documents/<storage_path> where storage_path
    is like 'groups/<group_id>/documents/<filename>'.
    """
    # Absolute path under project storage
    base = os.path.join(os.getcwd(), "storage", "documents")
    local = os.path.join(base, storage_path.replace("/", os.sep))
    # Perform blocking read in a thread
    def _read() -> bytes:
        with open(local, "rb") as f:
            return f.read()
    return await asyncio.to_thread(_read)


async def _process_bytes(
    doc: Document,
    file_bytes: bytes,
    db_session: AsyncSession,
    embedding_service: Optional[EmbeddingService],
) -> tuple[int, Optional[str]]:
    """Extract, chunk, and embed file bytes into Chunk rows. Returns (created_count, error_code)."""

    raw_text = _simple_text_extractor(file_bytes, getattr(doc, "filename", None), getattr(doc, "mime", None))
    text = _sanitize_text(raw_text)
    chunks = _chunk_text(text)

    own_service = False
    if embedding_service is None:
        embedding_service = EmbeddingService()
        own_service = True

    created = 0
    error_code: Optional[str] = None
    try:
        for idx, chunk_text in enumerate(chunks):
            chunk_text = _sanitize_text(chunk_text)
            if not chunk_text.strip():
                continue

            vec = None
            try:
                vec = await embedding_service.embed_query(chunk_text)
            except EmbeddingError as e:
                logger.warning("Embedding failed for doc %s chunk %d: %s", doc.id, idx, e)
                # store chunk without vector; continue

            chunk = Chunk(
                document_id=doc.id,
                tenant_id=doc.tenant_id,
                group_id=doc.group_id,
                chunk_index=idx,
                content=chunk_text,
                page_number=None,
                vector=vec,
                metadata_json=None,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            db_session.add(chunk)
            created += 1

        await db_session.flush()
    except Exception:
        logger.exception("Persisting chunks failed for document %s", doc.id)
        error_code = "persist_error"
    finally:
        if own_service:
            try:
                await embedding_service.close()  # type: ignore
            except Exception:
                pass

    return created, error_code


async def process_group_document(
    document_id: str | uuid.UUID,
    db_session: AsyncSession,
    embedding_service: Optional[EmbeddingService] = None,
) -> dict:
    """Initial processing of a group-scoped document."""

    try:
        doc_id = uuid.UUID(str(document_id))
    except Exception:
        doc_id = document_id  # type: ignore

    doc = await db_session.get(Document, doc_id)
    if not doc:
        logger.error("Document %s not found", document_id)
        return {"document_id": str(document_id), "status": "not_found"}

    doc.status = "processing"
    doc.updated_at = datetime.utcnow()
    await db_session.flush()
    try:
        await db_session.commit()
    except Exception:
        await db_session.rollback()

    # Read bytes
    try:
        file_bytes = await _read_file_bytes(doc.storage_path or "")
    except Exception as e:
        logger.exception("Failed to read document %s: %s", document_id, e)
        doc.status = "failed"
        doc.updated_at = datetime.utcnow()
        await db_session.flush()
        try:
            await db_session.commit()
        except Exception:
            await db_session.rollback()
        return {"document_id": str(document_id), "status": "failed", "error": "read_error"}

    created, error_code = await _process_bytes(doc, file_bytes, db_session, embedding_service)

    if error_code:
        doc.status = "failed"
        doc.updated_at = datetime.utcnow()
    else:
        doc.status = "ready"
        doc.updated_at = datetime.utcnow()

    await db_session.flush()
    try:
        await db_session.commit()
    except Exception:
        await db_session.rollback()

    if error_code:
        return {"document_id": str(document_id), "status": "failed", "error": error_code}
    return {"document_id": str(document_id), "status": "ready", "chunks_created": created}


async def process_group_document_reprocess(
    document_id: str | uuid.UUID,
    db_session: AsyncSession,
    embedding_service: Optional[EmbeddingService] = None,
) -> dict:
    """Reprocess an existing group document with rollback of old chunks on failure."""

    try:
        doc_id = uuid.UUID(str(document_id))
    except Exception:
        doc_id = document_id  # type: ignore

    doc = await db_session.get(Document, doc_id)
    if not doc:
        logger.error("Document %s not found", document_id)
        return {"document_id": str(document_id), "status": "not_found"}

    doc.status = "processing"
    doc.updated_at = datetime.utcnow()
    await db_session.flush()
    try:
        await db_session.commit()
    except Exception:
        await db_session.rollback()

    # Backup existing chunks for rollback
    existing_chunks = list(
        await db_session.scalars(select(Chunk).where(Chunk.document_id == doc.id))
    )
    backup_chunks = [
        {
            "chunk_index": c.chunk_index,
            "content": c.content,
            "page_number": c.page_number,
            "vector": c.vector,
            "metadata_json": c.metadata_json,
            "created_at": c.created_at,
            "updated_at": c.updated_at,
        }
        for c in existing_chunks
    ]

    # Delete existing chunks (embeddings stored with them)
    for c in existing_chunks:
        await db_session.delete(c)
    await db_session.flush()

    # Read bytes
    try:
        file_bytes = await _read_file_bytes(doc.storage_path or "")
    except Exception as e:
        logger.exception("Failed to read document %s: %s", document_id, e)
        await _restore_chunks(doc, db_session, backup_chunks)
        doc.status = "failed"
        doc.updated_at = datetime.utcnow()
        await db_session.flush()
        try:
            await db_session.commit()
        except Exception:
            await db_session.rollback()
        return {"document_id": str(document_id), "status": "failed", "error": "read_error"}

    created, error_code = await _process_bytes(doc, file_bytes, db_session, embedding_service)

    if error_code:
        await _restore_chunks(doc, db_session, backup_chunks)
        doc.status = "failed"
        doc.updated_at = datetime.utcnow()
    else:
        doc.status = "ready"
        doc.updated_at = datetime.utcnow()

    await db_session.flush()
    try:
        await db_session.commit()
    except Exception:
        await db_session.rollback()

    if error_code:
        return {"document_id": str(document_id), "status": "failed", "error": error_code}
    return {"document_id": str(document_id), "status": "ready", "chunks_created": created}


async def _restore_chunks(doc: Document, db_session: AsyncSession, backup_chunks: list[dict]) -> None:
    """Restore prior chunks after a failed reprocess attempt."""
    for data in backup_chunks:
        db_session.add(
            Chunk(
                document_id=doc.id,
                tenant_id=doc.tenant_id,
                group_id=doc.group_id,
                chunk_index=data["chunk_index"],
                content=data["content"],
                page_number=data["page_number"],
                vector=data["vector"],
                metadata_json=data["metadata_json"],
                created_at=data["created_at"],
                updated_at=data["updated_at"],
            )
        )
    await db_session.flush()
