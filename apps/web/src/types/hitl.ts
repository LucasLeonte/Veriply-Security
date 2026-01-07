export interface ContextChunk {
    chunk_id: string;
    document_id: string;
    document_name: string;
    section: string | null;
    text: string;
    similarity: number;
    page_number: number | null;
}

export interface ReviewQueueItemDetail {
    id: string;
    type: "chat" | "email";
    timestamp: string;
    userQuestion: string;
    aiDraft: string;
    botName: string;
    confidence: number;
    citations: Array<{
        source: string;
        relevance: number;
    }>;
    contextChunks: ContextChunk[];
    status: string;
    source: string;
    timeInQueue: string;
    metadata?: Record<string, unknown>;
}
