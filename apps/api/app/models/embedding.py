from sqlalchemy import Column, Uuid, ForeignKey
from pgvector.sqlalchemy import Vector
from .base import Base

class Embedding(Base):
    __tablename__ = "embeddings"
    id = Column(Uuid, primary_key=True)
    document_id = Column(Uuid, ForeignKey("documents.id"), nullable=False)
    vector = Column(Vector(1536), nullable=False)
