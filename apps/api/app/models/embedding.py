from sqlalchemy import Column, Uuid, ForeignKey, DateTime, Index
from pgvector.sqlalchemy import Vector
from datetime import datetime
from .base import Base

class Embedding(Base):
    __tablename__ = "embeddings"
    id = Column(Uuid, primary_key=True)
    chunk_id = Column(Uuid, ForeignKey("chunks.id", ondelete="CASCADE"), nullable=False)
    bot_id = Column(Uuid, ForeignKey("bots.id", ondelete="CASCADE"), nullable=False)
    document_id = Column(Uuid, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    vector = Column(Vector(1024), nullable=False)  # bge-m3 produces 1024-dim vectors
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Indexes for efficient vector search with bot isolation
    __table_args__ = (
        Index("idx_embeddings_bot_id", "bot_id"),
        Index("idx_embeddings_chunk_id", "chunk_id"),
        Index("idx_embeddings_document_id", "document_id"),
        Index("idx_embeddings_bot_chunk", "bot_id", "chunk_id"),
    )
