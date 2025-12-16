export type BotStatus = "Empty" | "Processing" | "Ready";

export interface Bot {
    id: string;
    name: string;
    description?: string;
    confidence_threshold: number;
    status: BotStatus;
    created_by: string;
    created_at: string;
    updated_at: string;
    tenant_id: string;
    group_id: string; // Added for group scoping
    doc_count?: number; // Added for UI display
    last_updated?: string; // Added for UI display
}

export interface CreateBotInput {
    name: string;
    description?: string;
    confidence_threshold?: number;
    group_id: string; // Required for group-scoped creation
}

export interface UpdateBotInput {
    name?: string;
    description?: string;
    confidence_threshold?: number;
}

export interface PaginatedBotsResponse {
    bots: Bot[];
    total_count: number;
    limit: number;
    offset: number;
}

export interface ApiErrorResponse {
    detail: string | { error: string; limit: number; current: number };
}
