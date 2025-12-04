"""
Document Chunk Model
Represents chunks/segments of a document after processing and extraction.
"""

from sqlalchemy import Column, String, Uuid, ForeignKey, DateTime, Integer, Text, Index
from datetime import datetime
from .base import Base


class Chunk(Base):
    __tablename__ = "chunks"
    id = Column(Uuid, primary_key=True)
    document_id = Column(Uuid, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    bot_id = Column(Uuid, ForeignKey("bots.id", ondelete="CASCADE"), nullable=False)
    content = Column(Text, nullable=False)
    page_number = Column(Integer, nullable=True)  # For PDFs with multiple pages
    chunk_index = Column(Integer, nullable=False)  # Order within document
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Indexes for efficient queries
    __table_args__ = (
        Index("idx_chunks_document_id", "document_id"),
        Index("idx_chunks_bot_id", "bot_id"),
        Index("idx_chunks_bot_document", "bot_id", "document_id"),
    )
