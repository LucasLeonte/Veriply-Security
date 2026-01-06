import { UUID } from "crypto";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

export interface EmailIntegration {
    id: string;
    provider: "gmail" | "outlook";
    status: "connected" | "disconnected";
    last_sync_time: string | null;
    created_at: string;
}

export interface ListIntegrationsResponse {
    integrations: EmailIntegration[];
}

export interface GmailMessage {
    id: string;
    threadId: string;
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
export async function listIntegrations(token: string): Promise<ListIntegrationsResponse> {
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
        let errorMessage = "Failed to fetch messages";
        try {
            const errorData = await response.json();
            if (errorData.detail) {
                errorMessage = errorData.detail;
            }
        } catch (e) {
            // ignore JSON parse error
        }
        throw new Error(errorMessage);
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
    const response = await fetch(`${API_BASE_URL}/api/v1/integrations/gmail/import`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ message_id: messageId }),
    });

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
    originalText: string
): Promise<GenerateReplyResponse> {
    const response = await fetch(`${API_BASE_URL}/api/v1/integrations/gmail/generate-reply`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ message_id: messageId, original_text: originalText }),
    });

    if (!response.ok) {
        throw new Error("Failed to generate reply");
    }

    return response.json();
}
