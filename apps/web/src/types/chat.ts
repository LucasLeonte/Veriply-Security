export type TrustLevel = "verified" | "ai_generated" | "pending";
export type SourceType = "verified_kb" | "rag" | "hitl";

export interface ChatMessage {
    id: string;
    role: "user" | "assistant";
    content: string;
    timestamp: number;
    citations?: Citation[];
    trustLevel?: TrustLevel;
    confidenceScore?: number;
    sourceType?: SourceType;
    responseId?: string;
}

export interface Citation {
    source: string;
    url?: string;
    document_name?: string;
    document_id?: string;
    chunk_id?: string;
    page_number?: number;
    section?: string | null;
    position?: number;
    text?: string;
    similarity?: number;
}

export interface BotPublicInfo {
    id: string;
    name: string;
    avatar_url?: string;
    welcome_message: string;
    is_public: boolean;
}

export interface ChatQueryRequest {
    query: string;
    context?: ChatMessage[];
    context_window?: number;
    conversation_history?: { role: string; content: string }[];
}

export interface StreamToken {
    token: string;
    done?: boolean;
}

export interface StreamMetadata {
    citations: Citation[];
    confidence?: number;
    chunks_used?: number;
}
