import { UUID } from "crypto";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

export interface EmailIntegration {
    id: string;
    provider: "gmail" | "outlook";
    status: "connected" | "disconnected";
    default_reply_bot_id?: string | null;
    last_sync_time: string | null;
    created_at: string;
}

export interface ListIntegrationsResponse {
    integrations: EmailIntegration[];
}

export interface GmailMessage {
    id: string; // thread id from Gmail
    threadId: string; // camelCase thread id for UI convenience
    lastMessageId: string; // most recent message id within the thread
    snippet: string;
    subject: string;
    from: string;
    to: string;
    date: string;
}

export interface ListGmailMessagesResponse {
    messages: GmailMessage[];
}

export interface GenerateReplyResponse {
    reply: string;
}

/**
 * Get authorization URL for Gmail OAuth
 */
export function getGmailAuthUrl(token?: string): string {
    const base = `${API_BASE_URL}/api/v1/integrations/gmail/authorize`;
    if (!token) return base;
    const url = new URL(base);
    // ... existing code ...
    url.searchParams.set("token", token);
    return url.toString();
}

/**
 * Get authorization URL for Outlook OAuth
 */
export function getOutlookAuthUrl(token?: string): string {
    const base = `${API_BASE_URL}/api/v1/integrations/outlook/authorize`;
    if (!token) return base;
    const url = new URL(base);
    url.searchParams.set("token", token);
    return url.toString();
}

/**
 * List all email integrations for the current user
 */
export async function listIntegrations(
    token: string
): Promise<ListIntegrationsResponse> {
    const response = await fetch(`${API_BASE_URL}/api/v1/integrations/list`, {
        method: "GET",
        headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
        },
    });

    if (!response.ok) {
        throw new Error("Failed to fetch integrations");
    }

    return response.json();
}

/**
 * Disconnect an email integration
 */
export async function disconnectIntegration(
    integrationId: string,
    token: string
): Promise<{ message: string }> {
    const response = await fetch(
        `${API_BASE_URL}/api/v1/integrations/${integrationId}`,
        {
            method: "DELETE",
            headers: {
                "Content-Type": "application/json",
                Authorization: `Bearer ${token}`,
            },
        }
    );

    if (!response.ok) {
        throw new Error("Failed to disconnect integration");
    }

    return response.json();
}

/**
 * List Gmail messages
 */
export async function listGmailMessages(
    token: string,
    folder: "INBOX" | "SENT" = "INBOX"
): Promise<ListGmailMessagesResponse> {
    const url = new URL(`${API_BASE_URL}/api/v1/integrations/gmail/messages`);
    url.searchParams.set("folder", folder);

    const response = await fetch(url.toString(), {
        method: "GET",
        headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
        },
    });

    if (!response.ok) {
        let errorMessage = "Failed to fetch Gmail messages";
        try {
            const errorData = await response.json();
            if (errorData.detail) {
                errorMessage = Array.isArray(errorData.detail)
                    ? errorData.detail
                          .map((d: any) => (d.msg ? d.msg : String(d)))
                          .join("; ")
                    : String(errorData.detail);
            }
        } catch (e) {
            // ignore JSON parse error
        }
        throw new Error(errorMessage);
    }

    const data = await response.json();
    const messages = (data.messages || []).map((m: any) => ({
        id: m.id,
        threadId: m.thread_id || m.threadId || m.id,
        lastMessageId: m.last_message_id || m.lastMessageId || m.id,
        snippet: m.snippet,
        subject: m.subject,
        from: m.from,
        to: m.to,
        date: m.date,
    }));

    return { messages };
}

/**
 * Get full Gmail message details
 */
export async function getGmailMessage(
    token: string,
    messageId: string
): Promise<any> {
    const response = await fetch(
        `${API_BASE_URL}/api/v1/integrations/gmail/messages/${messageId}`,
        {
            method: "GET",
            headers: {
                "Content-Type": "application/json",
                Authorization: `Bearer ${token}`,
            },
        }
    );

    if (!response.ok) {
        throw new Error("Failed to fetch message details");
    }

    return response.json();
}

/**
 * Import a Gmail message as a Document
 */
export async function importGmailMessage(
    token: string,
    messageId: string
): Promise<{ message: string; document_id: string }> {
    const response = await fetch(
        `${API_BASE_URL}/api/v1/integrations/gmail/import`,
        {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                Authorization: `Bearer ${token}`,
            },
            body: JSON.stringify({ message_id: messageId }),
        }
    );

    if (!response.ok) {
        throw new Error("Failed to import message");
    }

    return response.json();
}

/**
 * Generate a reply for a Gmail message
 */
export async function generateGmailReply(
    token: string,
    messageId: string,
    originalText: string,
    options?: { botId?: string; subject?: string }
): Promise<GenerateReplyResponse> {
    const body: any = { message_id: messageId, original_text: originalText };
    if (options?.botId) body.bot_id = options.botId;
    if (options?.subject) body.subject = options.subject;

    const response = await fetch(
        `${API_BASE_URL}/api/v1/integrations/gmail/generate-reply`,
        {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                Authorization: `Bearer ${token}`,
            },
            body: JSON.stringify(body),
        }
    );

    if (!response.ok) {
        throw new Error("Failed to generate reply");
    }

    return response.json();
}

/**
 * Set the default reply bot for an email integration
 */
export async function setDefaultReplyBot(
    token: string,
    integrationId: string,
    botId: string | null
): Promise<{ id: string; default_reply_bot_id: string | null }> {
    const response = await fetch(
        `${API_BASE_URL}/api/v1/integrations/${integrationId}/default-reply-bot`,
        {
            method: "PUT",
            headers: {
                "Content-Type": "application/json",
                Authorization: `Bearer ${token}`,
            },
            body: JSON.stringify({ bot_id: botId }),
        }
    );

    if (!response.ok) {
        throw new Error("Failed to set default reply bot");
    }

    return response.json();
}

/**
 * Send a reply email via Gmail
 */
export async function sendGmailReply(
    token: string,
    threadId: string,
    messageId: string,
    to: string,
    subject: string,
    body: string
): Promise<{ message: string; sent_message_id: string }> {
    const response = await fetch(
        `${API_BASE_URL}/api/v1/integrations/gmail/send-reply`,
        {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                Authorization: `Bearer ${token}`,
            },
            body: JSON.stringify({
                thread_id: threadId,
                message_id: messageId,
                to,
                subject,
                body,
            }),
        }
    );

    if (!response.ok) {
        let errorDetail = "Failed to send reply";
        try {
            const errorData = await response.json();
            if (errorData.detail && Array.isArray(errorData.detail)) {
                errorDetail = errorData.detail
                    .map((err: any) => `${err.loc?.join(".")} - ${err.msg}`)
                    .join("; ");
            } else if (errorData.detail) {
                errorDetail = String(errorData.detail);
            }
        } catch (e) {
            // Silently handle parse errors
        }
        throw new Error(errorDetail);
    }

    return response.json();
}
