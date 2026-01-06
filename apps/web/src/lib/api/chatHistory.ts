import { ChatHistoryEntry } from "@/types/chat";
import { getAccessToken } from "@/lib/auth";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

export interface ChatHistoryParams {
    sessionId?: string;
    answerId?: string;
    limit?: number;
    offset?: number;
}

export async function fetchChatHistory(
    botId: string,
    params: ChatHistoryParams = {}
): Promise<ChatHistoryEntry[]> {
    const token = typeof window !== "undefined" ? getAccessToken() : null;
    const query = new URLSearchParams();
    if (params.sessionId) query.append("session_id", params.sessionId);
    if (params.answerId) query.append("answer_id", params.answerId);
    if (params.limit) query.append("limit", String(params.limit));
    if (params.offset) query.append("offset", String(params.offset));

    const response = await fetch(
        `${API_BASE_URL}/api/v1/bots/${botId}/history?${query.toString()}`,
        {
            headers: {
                "Content-Type": "application/json",
                ...(token ? { Authorization: `Bearer ${token}` } : {}),
            },
            credentials: "include",
        }
    );

    if (!response.ok) {
        const text = await response.text().catch(() => "");
        const detail = text || response.statusText;
        const err = new Error(detail);
        (err as any).status = response.status;
        throw err;
    }

    return response.json();
}
