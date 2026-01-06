import { getAccessToken } from "@/lib/auth";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

export type FeedbackType = "positive" | "negative";
export type FeedbackReason =
    | "incorrect"
    | "not_helpful"
    | "incomplete"
    | "harmful"
    | "other";

export interface FeedbackRequest {
    answer_id: string;
    message_id: string;
    type: FeedbackType;
    reason?: FeedbackReason;
    additional_notes?: string;
    session_id?: string;
}

export async function submitFeedback(
    botId: string,
    payload: FeedbackRequest
): Promise<{ feedback_id: string } & Record<string, unknown>> {
    // Attach bearer token from storage when available (login stores tokens, not cookies)
    const token = typeof window !== "undefined" ? getAccessToken() : null;

    const response = await fetch(
        `${API_BASE_URL}/api/v1/bots/${botId}/feedback`,
        {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                ...(token ? { Authorization: `Bearer ${token}` } : {}),
            },
            credentials: "include",
            body: JSON.stringify(payload),
        }
    );

    if (!response.ok) {
        const message = await response.text();
        const error = message || response.statusText;
        const err = new Error(error);
        // Attach status for caller handling
        (err as any).status = response.status;
        throw err;
    }

    return response.json();
}

export async function fetchFeedbackStats(
    botId: string,
    hours = 24
): Promise<any> {
    const token = typeof window !== "undefined" ? getAccessToken() : null;

    const response = await fetch(
        `${API_BASE_URL}/api/v1/bots/${botId}/feedback/stats?hours=${hours}`,
        {
            credentials: "include",
            headers: token ? { Authorization: `Bearer ${token}` } : undefined,
        }
    );

    if (!response.ok) {
        throw new Error("Failed to load feedback stats");
    }

    return response.json();
}