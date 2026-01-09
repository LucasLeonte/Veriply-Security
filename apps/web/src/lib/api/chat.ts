import { BotPublicInfo, ChatMessage } from "@/types/chat";
import { getAccessToken } from "@/lib/auth";

let API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// Ensure we use localhost instead of 127.0.0.1 to allow cookie sharing
if (API_BASE_URL.includes("127.0.0.1")) {
    API_BASE_URL = API_BASE_URL.replace("127.0.0.1", "localhost");
}

/**
 * Fetch public bot information (no authentication required)
 */
export async function getBotPublicInfo(
    botId: string,
    embedOrigin?: string
): Promise<BotPublicInfo> {
    const headers: Record<string, string> = {
        "Content-Type": "application/json",
    };
    if (embedOrigin) {
        headers["X-Embed-Origin"] = embedOrigin;
    }

    const response = await fetch(
        `${API_BASE_URL}/api/v1/bots/${botId}/public`,
        {
            method: "GET",
            headers,
            cache: "no-store", // Disable caching for now, we'll add it later with TTL
        }
    );

    if (!response.ok) {
        let detail = "Failed to fetch bot information";
        try {
            const body = await response.json();
            if (body?.detail) {
                detail = body.detail;
            }
        } catch {
            // ignore parse errors
        }

        if (response.status === 404) {
            throw new Error("Bot not found");
        }
        if (response.status === 403) {
            throw new Error(detail || "Bot is not public");
        }
        throw new Error(detail);
    }

    return response.json();
}

/**
 * Query a bot and stream the response via Server-Sent Events
 */
export async function* streamChatQuery(
    botId: string,
    query: string,
    options?: {
        context?: ChatMessage[];
        contextWindow?: number;
        sessionId?: string;
        messageId?: string;
        embedOrigin?: string;
    }
): AsyncGenerator<
    | { type: "token"; content: string }
    | { type: "metadata"; data: Record<string, unknown> },
    void,
    unknown
> {
    const embedOrigin = options?.embedOrigin ||
        (typeof document !== "undefined"
            ? (() => {
                try {
                    const params = new URLSearchParams(
                        window.location.search || ""
                    );
                    const qp = params.get("embed_origin");
                    if (qp) return qp;
                    // Prefer ancestor origin when referrer is stripped
                    // @ts-ignore: ancestorOrigins exists on window in browsers
                    const ancestor = window.location.ancestorOrigins?.[0];
                    if (ancestor) return ancestor;
                    if (document.referrer) return document.referrer;
                    return window.location.origin;
                } catch {
                    return undefined;
                }
            })()
            : undefined);

    const token = getAccessToken();

    const response = await fetch(
        `${API_BASE_URL}/api/v1/bots/${botId}/chat/query`,
        {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                ...(embedOrigin ? { "X-Embed-Origin": embedOrigin } : {}),
                ...(token ? { "Authorization": `Bearer ${token}` } : {}),
            },
            body: JSON.stringify({
                query,
                stream: true,
                context: options?.context?.map((msg) => ({
                    role: msg.role,
                    content: msg.content,
                    citations: msg.citations,
                    timestamp: msg.timestamp,
                })),
                context_window: options?.contextWindow,
                session_id: options?.sessionId,
                message_id: options?.messageId,
            }),
            credentials: "include",
        }
    );

    if (!response.ok) {
        let detail = response.statusText;
        try {
            const errorBody = await response.json();
            if (errorBody?.detail) {
                detail = errorBody.detail;
            }
        } catch (err) {
            // ignore parse errors
        }
        throw new Error(detail || `Query failed: ${response.status}`);
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
export function loadChatHistory(
    botId: string,
    sessionId: string
): ChatMessage[] {
    if (typeof window === "undefined") return [];

    try {
        const stored = localStorage.getItem(
            `chat_history_${botId}_${sessionId}`
        );
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
export function saveChatHistory(
    botId: string,
    sessionId: string,
    messages: ChatMessage[]
): void {
    if (typeof window === "undefined") return;

    try {
        localStorage.setItem(
            `chat_history_${botId}_${sessionId}`,
            JSON.stringify(messages)
        );

        // Maintain a simple sessions index per bot for this browser
        const indexKey = `chat_session_index_${botId}`;
        const indexRaw = localStorage.getItem(indexKey);
        let index: Array<{
            id: string;
            title: string;
            lastTimestamp: number;
            count: number;
        }> = [];
        if (indexRaw) {
            try {
                index = JSON.parse(indexRaw);
            } catch { }
        }

        const lastTimestamp = messages.length
            ? messages[messages.length - 1].timestamp
            : Date.now();
        const firstUserMsg = messages.find((m) => m.role === "user");
        const title = firstUserMsg?.content?.slice(0, 80) || "Conversation";

        const existingIdx = index.findIndex((i) => i.id === sessionId);
        const entry = {
            id: sessionId,
            title,
            lastTimestamp,
            count: messages.length,
        };
        if (existingIdx >= 0) index[existingIdx] = entry;
        else index.push(entry);
        index.sort((a, b) => b.lastTimestamp - a.lastTimestamp);
        localStorage.setItem(indexKey, JSON.stringify(index));
    } catch (error) {
        console.error("Failed to save chat history:", error);
    }
}

/**
 * Clear chat history for a specific bot
 */
export function clearChatHistory(botId: string, sessionId: string): void {
    if (typeof window === "undefined") return;

    try {
        localStorage.removeItem(`chat_history_${botId}_${sessionId}`);

        // Also remove from index
        const indexKey = `chat_session_index_${botId}`;
        const indexRaw = localStorage.getItem(indexKey);
        if (indexRaw) {
            try {
                const index = JSON.parse(indexRaw) as Array<{ id: string }>;
                const newIndex = index.filter((i) => i.id !== sessionId);
                localStorage.setItem(indexKey, JSON.stringify(newIndex));
            } catch { }
        }
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
    citations?: Array<{ source: string; url?: string }>,
    sessionId?: string
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
                session_id: sessionId,
            }),
        }
    );

    if (!response.ok) {
        // Do not cause infinite retry loops on 4xx; surface a clear message instead
        if (response.status === 404) {
            return {
                success: false,
                message: "Review queue endpoint or bot not found",
            };
        }

        throw new Error(
            `Failed to send to review queue: ${response.statusText}`
        );
    }

    return response.json();
}

export function getUserSessions(
    botId: string
): Array<{ id: string; title: string; lastTimestamp: number; count: number }> {
    if (typeof window === "undefined") return [];
    try {
        const indexKey = `chat_session_index_${botId}`;
        const indexRaw = localStorage.getItem(indexKey);
        if (!indexRaw) return [];
        const index = JSON.parse(indexRaw) as Array<{
            id: string;
            title: string;
            lastTimestamp: number;
            count: number;
        }>;
        return Array.isArray(index) ? index : [];
    } catch (e) {
        console.error("Failed to get user sessions index", e);
        return [];
    }
}
