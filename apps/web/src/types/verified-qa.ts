export interface VerifiedQA {
    id: string;
    tenant_id: string;
    group_id: string;
    bot_id: string | null;
    question_text: string;
    answer_text: string;
    source_citations: Record<string, any> | null;
    approved_by_user_id: string | null;
    approved_at: string;
    updated_by_user_id: string | null;
    deleted_at: string | null;
    created_at: string;
    updated_at: string;
}

export interface VerifiedQAListResponse {
    items: VerifiedQA[];
    total: number;
    page: number;
    limit: number;
    total_pages: number;
}

export interface VerifiedQAUpdate {
    question_text?: string;
    answer_text?: string;
    source_citations?: Record<string, any>;
}
