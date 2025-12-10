export type DocumentStatus = "pending" | "processing" | "processed" | "failed";

export interface Document {
    id: string;
    bot_id: string;
    filename: string;
    file_size: number;
    status: DocumentStatus;
    chunk_count: number;
    created_at: string;
    updated_at: string;
    title?: string;
    mime_type?: string;
    storage_path?: string;
    // Optional frontend-only fields for UI
    processing_progress?: number;
    error_message?: string;
}

export interface DocumentChunk {
    id: string;
    document_id: string;
    content: string;
    chunk_index: number;
    page_number?: number;
    created_at: string;
}

export interface UploadDocumentInput {
    file: File;
    bot_id: string;
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
