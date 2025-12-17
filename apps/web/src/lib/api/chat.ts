import { BotPublicInfo, ChatMessage } from "@/types/chat";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

/**
 * Fetch public bot information (no authentication required)
 */
export async function getBotPublicInfo(botId: string): Promise<BotPublicInfo> {
    const response = await fetch(`${API_BASE_URL}/api/v1/bots/${botId}/public`, {
        method: "GET",
        headers: {
            "Content-Type": "application/json",
        },
        cache: "no-store", // Disable caching for now, we'll add it later with TTL
    });

    if (!response.ok) {
        if (response.status === 404) {
            throw new Error("Bot not found");
        }
        if (response.status === 403) {
            throw new Error("Bot is not public");
        }
        throw new Error("Failed to fetch bot information");
    }

    return response.json();
}

/**
 * Query a bot and stream the response via Server-Sent Events
 */
export async function* streamChatQuery(
    botId: string,
    query: string,
    conversationHistory?: { role: string; content: string }[]
): AsyncGenerator<
    { type: "token"; content: string } | { type: "metadata"; data: Record<string, unknown> },
    void,
    unknown
> {
    const response = await fetch(
        `${API_BASE_URL}/api/v1/bots/${botId}/chat/query`,
        {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                query,
                stream: true,
                conversation_history: conversationHistory,
            }),
        }
    );

    if (!response.ok) {
        throw new Error(`Query failed: ${response.statusText}`);
    }

    const reader = response.body?.getReader();
    const decoder = new TextDecoder();

    if (!reader) {
        throw new Error("No response body");
    }

    try {
        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            const chunk = decoder.decode(value, { stream: true });
            const lines = chunk.split("\n");

            for (const line of lines) {
                if (!line.trim() || !line.startsWith("data: ")) continue;

                const data = line.slice(6); // Remove "data: " prefix
                if (data === "[DONE]") continue;

                try {
                    const parsed = JSON.parse(data);
                    if (parsed.token !== undefined) {
                        yield { type: "token", content: parsed.token };
                    } else if (parsed.metadata) {
                        yield { type: "metadata", data: parsed.metadata };
                    }
                } catch (e) {
                    console.error("Failed to parse SSE data:", e);
                }
            }
        }
    } finally {
        reader.releaseLock();
    }
}

/**
 * Load chat history from localStorage for a specific bot
 */
export function loadChatHistory(botId: string): ChatMessage[] {
    if (typeof window === "undefined") return [];

    try {
        const stored = localStorage.getItem(`chat_session_${botId}`);
        if (!stored) return [];
        return JSON.parse(stored);
    } catch (error) {
        console.error("Failed to load chat history:", error);
        return [];
    }
}

/**
 * Save chat history to localStorage for a specific bot
 */
export function saveChatHistory(botId: string, messages: ChatMessage[]): void {
    if (typeof window === "undefined") return;

    try {
        localStorage.setItem(`chat_session_${botId}`, JSON.stringify(messages));
    } catch (error) {
        console.error("Failed to save chat history:", error);
    }
}

/**
 * Clear chat history for a specific bot
 */
export function clearChatHistory(botId: string): void {
    if (typeof window === "undefined") return;

    try {
        localStorage.removeItem(`chat_session_${botId}`);
    } catch (error) {
        console.error("Failed to clear chat history:", error);
    }
}

/**
 * Send a low-confidence message to the review queue for human review
 */
export async function sendToReviewQueue(
    botId: string,
    userQuestion: string,
    aiDraft: string,
    confidence: number,
    citations?: Array<{ source: string; url?: string }>
): Promise<{ success: boolean; message: string }> {
    const response = await fetch(
        `${API_BASE_URL}/api/v1/bots/${botId}/review-queue`,
        {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                user_question: userQuestion,
                ai_draft: aiDraft,
                confidence,
                citations: citations || [],
            }),
        }
    );

    if (!response.ok) {
        throw new Error(`Failed to send to review queue: ${response.statusText}`);
    }

    return response.json();
}
