export interface ChatMessage {
    id: string;
    role: "user" | "assistant";
    content: string;
    timestamp: number;
    citations?: Citation[];
    answerId?: string;
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
    token_count?: number;
    answer_id?: string;
    session_id?: string;
}

export interface ChatHistoryEntry {
    id: string;
    bot_id: string;
    tenant_id: string;
    role: string;
    content: string;
    session_id?: string | null;
    client_message_id?: string | null;
    answer_id?: string | null;
    citations: Citation[];
    created_at: string;
}
