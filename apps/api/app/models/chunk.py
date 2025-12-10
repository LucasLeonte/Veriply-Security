from sqlalchemy import Column, Integer, Uuid, ForeignKey, DateTime, Text, Index
from datetime import datetime
from .base import Base

try:
    from pgvector.sqlalchemy import Vector
except Exception:
    Vector = Text


class Chunk(Base):
    """Document chunk model for processed document segments.

    Fields:
      - id: uuid primary key
      - document_id: FK -> documents.id
      - tenant_id: FK -> tenants.id
      - bot_id: FK -> bots.id (nullable)
      - chunk_index: order index within document
      - text: chunk content
      - vector: pgvector embedding (nullable during processing)
      - metadata_json: JSON/text metadata stored in DB column `metadata`
      - created_at / updated_at timestamps
    """

    __tablename__ = "chunks"

    id = Column(Uuid, primary_key=True, default=lambda: __import__('uuid').uuid4())
    document_id = Column(Uuid, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    tenant_id = Column(Uuid, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=True)
    bot_id = Column(Uuid, ForeignKey("bots.id", ondelete="CASCADE"), nullable=True)
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    page_number = Column(Integer, nullable=True)
    vector = Column(Vector, nullable=True)
    # 'metadata' is reserved on declarative classes — use attribute name metadata_json
    metadata_json = Column('metadata', Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('idx_chunks_document_id', 'document_id'),
        Index('idx_chunks_bot_id', 'bot_id'),
        Index('idx_chunks_bot_document', 'bot_id', 'document_id'),
        {'extend_existing': True},
    )
