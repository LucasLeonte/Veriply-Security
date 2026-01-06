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
