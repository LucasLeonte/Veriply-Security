export type DocumentStatus =
    | "uploading"
    | "uploaded"
    | "processing"
    | "ready"
    | "failed";

export interface Document {
    id: string;
    group_id: string; // Group scoping
    bot_id?: string; // Optional - for provenance
    uploader_id: string; // Provenance tracking
    filename: string;
    title?: string;
    mime: string;
    size: number;
    storage_path: string;
    status: DocumentStatus;
    created_at: string;
    updated_at: string;
    deleted_at?: string; // Soft-delete support
    tenant_id: string;
    // Optional frontend-only fields for UI
    chunk_count?: number;
    processing_progress?: number;
    error_message?: string;
    uploader_name?: string; // For UI display
}

export interface DocumentChunk {
    id: string;
    document_id: string;
    content: string;
    chunk_index: number;
    page_number?: number;
    group_id: string;
    source_metadata?: Record<string, any>;
    created_at: string;
}

export interface UploadDocumentInput {
    file: File;
    group_id: string;
    bot_id?: string; // Optional - track which bot triggered upload
    title?: string;
}

export interface PaginatedDocumentsResponse {
    documents: Document[];
    total: number;
    page: number;
    page_size: number;
    total_pages: number;
}

export interface DocumentDetailResponse extends Document {
    chunks?: DocumentChunk[];
}
