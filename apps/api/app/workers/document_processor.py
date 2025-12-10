import argparse
import logging
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from app.lib import storage
from app.lib import embeddings as embeddings_lib
from app.models.document import Document
from app.models.chunk import Chunk
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)


def _simple_text_extractor(file_bytes: bytes, filename: str | None, mime: str | None) -> str:
    """Attempt to extract text using available libraries, otherwise fall back to utf-8 decode.

    This is intentionally conservative: it only uses optional libraries if present.
    """
    # PDF
    if mime and "pdf" in mime.lower() or (filename and filename.lower().endswith(".pdf")):
        try:
            from PyPDF2 import PdfReader
            reader = PdfReader(fileobj=None)
        except Exception:
            # Try reading with PdfReader from bytes
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
                logger.warning("PyPDF2 not available or failed to parse PDF; falling back to binary decode")

    # DOCX
    if filename and filename.lower().endswith(".docx"):
        try:
            from docx import Document as DocxDocument
            import io as _io
            doc = DocxDocument(_io.BytesIO(file_bytes))
            paragraphs = [p.text for p in doc.paragraphs]
            return "\n\n".join(paragraphs)
        except Exception:
            logger.warning("python-docx not available or failed to parse DOCX; falling back to binary decode")

    # Plain text fallback
    try:
        return file_bytes.decode("utf-8")
    except Exception:
        try:
            return file_bytes.decode("latin-1")
        except Exception:
            return ""


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
        i = end - overlap
    return chunks


async def process_document(document_id: str, db_session: Optional[AsyncSession] = None, storage_client=None, embedding_client=None, config=None):
    """Process a single document: download, extract, chunk, embed, persist.

    Expects an `AsyncSession` for `db_session`. If `embedding_client` is not
    provided, falls back to `app.lib.embeddings.get_embedding`.
    """
    logger.info("Processing document %s", document_id)

    if db_session is None:
        raise ValueError("An AsyncSession `db_session` is required")

    # Normalize id to UUID
    try:
        doc_uuid = uuid.UUID(str(document_id))
    except Exception:
        doc_uuid = document_id

    # Load document row
    doc = await db_session.get(Document, doc_uuid)
    if not doc:
        logger.error("Document %s not found", document_id)
        return {"document_id": document_id, "status": "not_found"}

    # mark processing
    doc.status = "processing"
    doc.updated_at = datetime.utcnow()
    await db_session.flush()

    # Download bytes
    try:
        file_bytes = storage.download_bytes(doc.storage_path)
    except Exception as e:
        logger.exception("Failed to download document %s: %s", document_id, e)
        doc.status = "error"
        await db_session.flush()
        return {"document_id": document_id, "status": "download_failed", "error": str(e)}

    # Extract text
    text = _simple_text_extractor(file_bytes, getattr(doc, "filename", None), getattr(doc, "mime", None))
    if not text:
        logger.warning("No text extracted for document %s", document_id)

    # Chunk text
    chunks = _chunk_text(text)

    # Choose embedding function
    embed_fn = None
    if embedding_client:
        embed_fn = embedding_client
    else:
        embed_fn = embeddings_lib.get_embedding

    created = 0
    try:
        for idx, chunk_text in enumerate(chunks):
            vec = None
            try:
                vec = embed_fn(chunk_text)
            except Exception:
                logger.exception("Embedding failed for document %s chunk %d", document_id, idx)

            chunk = Chunk(
                document_id=doc.id,
                tenant_id=doc.tenant_id,
                bot_id=doc.bot_id,
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

        doc.status = "processed"
        doc.updated_at = datetime.utcnow()
        await db_session.flush()
    except Exception as e:
        logger.exception("Failed persisting chunks for document %s: %s", document_id, e)
        doc.status = "error"
        await db_session.flush()
        return {"document_id": document_id, "status": "persist_failed", "error": str(e)}

    return {"document_id": document_id, "status": "processed", "chunks_created": created}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--run-once', action='store_true', help='Run one document and exit')
    parser.add_argument('--document-id', type=str, help='Document id to process')
    args = parser.parse_args()

    if args.run_once and args.document_id:
        print('This entrypoint requires wiring an AsyncSession. Run via a small runner that provides a DB session.')
    else:
        print('No document specified. This is a worker; integrate with enqueuer to run as a service.')


if __name__ == '__main__':
    main()
