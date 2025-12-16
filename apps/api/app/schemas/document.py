from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from enum import Enum


class DocumentStatus(str, Enum):
    """Document processing status"""
    PENDING = "pending"
    PROCESSING = "processing"
    PROCESSED = "processed"
    FAILED = "failed"


class DocumentResponse(BaseModel):
    """Response schema for document details"""
    id: UUID
    bot_id: UUID
    filename: str
    file_size: int
    status: str
    chunk_count: int = 0
    created_at: datetime
    updated_at: datetime
    title: Optional[str] = None
    mime_type: Optional[str] = None
    storage_path: Optional[str] = None

    class Config:
        from_attributes = True


class DocumentUploadResponse(BaseModel):
    """Response schema for document upload"""
    id: UUID
    document_id: UUID  # Backward compatibility
    status: str
    queued: bool


class DocumentListResponse(BaseModel):
    """Response schema for paginated document list"""
    documents: List[DocumentResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class ChunkResponse(BaseModel):
    """Response schema for document chunk"""
    id: UUID
    document_id: UUID
    chunk_index: int
    content: str
    page_number: Optional[int] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class ChunkListResponse(BaseModel):
    """Response schema for document chunks list"""
    chunks: List[ChunkResponse]
    total: int


class BulkDeleteRequest(BaseModel):
    """Request schema for bulk document deletion"""
    document_ids: List[UUID]
    
    class Config:
        json_schema_extra = {
            "example": {
                "document_ids": [
                    "550e8400-e29b-41d4-a716-446655440000",
                    "550e8400-e29b-41d4-a716-446655440001"
                ]
            }
        }


class BulkDeleteResponse(BaseModel):
    """Response schema for bulk document deletion"""
    message: str
    queued_count: int
    document_ids: List[str]
