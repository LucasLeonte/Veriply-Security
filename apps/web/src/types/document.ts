export type DocumentStatus = "pending" | "processing" | "processed" | "failed";

export interface Document {
    id: string;
    bot_id: string;
    filename: string;
    file_size: number;
    status: DocumentStatus;
    processing_progress?: number;
    error_message?: string;
    chunk_count: number;
    embedding_count: number;
    uploaded_at: string;
    processed_at?: string;
    uploaded_by: string;
    tenant_id: string;
}

export interface DocumentChunk {
    id: string;
    document_id: string;
    content: string;
    chunk_index: number;
    embedding?: number[];
    created_at: string;
}

export interface UploadDocumentInput {
    file: File;
    bot_id: string;
}

export interface PaginatedDocumentsResponse {
    documents: Document[];
    total_count: number;
    page: number;
    page_size: number;
}

export interface DocumentDetailResponse extends Document {
    chunks?: DocumentChunk[];
}
