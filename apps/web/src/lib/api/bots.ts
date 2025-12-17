import {
    Bot,
    CreateBotInput,
    UpdateBotInput,
    PaginatedBotsResponse,
} from "@/types/bot";
import { mockBotsApi } from "./mockBots";
import { getAccessToken } from "@/lib/auth";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";
const USE_MOCK_DATA = process.env.NEXT_PUBLIC_USE_MOCK_DATA === "true";

// Helper to construct group-scoped bot endpoint
function getBotsEndpoint(groupId: string): string {
    return `${API_BASE_URL}/api/v1/groups/${groupId}/bots`;
}

async function getAuthToken(): Promise<string | null> {
    // Only access localStorage on client-side
    if (typeof window === "undefined") {
        return null;
    }
    return getAccessToken();
}

async function fetchWithAuth(
    url: string,
    options: RequestInit = {}
): Promise<Response> {
    const token = await getAuthToken();
    const headers: Record<string, string> = {
        "Content-Type": "application/json",
        ...(options.headers as Record<string, string>),
    };

    if (token) {
        headers.Authorization = `Bearer ${token}`;
    }

    const response = await fetch(url, {
        ...options,
        headers,
    });

    return response;
}

async function handleResponse<T>(response: Response): Promise<T> {
    if (!response.ok) {
        // Handle 401 Unauthorized - token expired or invalid
        if (response.status === 401) {
            // Clear expired token
            if (typeof window !== "undefined") {
                localStorage.removeItem("access_token");
                // Redirect to login
                window.location.href = "/login?error=session_expired";
            }
            throw new Error("Session expired. Please log in again.");
        }
        
        const error = await response
            .json()
            .catch(() => ({ detail: "Unknown error" }));
        throw new Error(error.detail || `HTTP ${response.status}`);
    }
    return response.json();
}

export const botsApi = {
    async createBot(data: CreateBotInput): Promise<Bot> {
        if (USE_MOCK_DATA) {
            return mockBotsApi.createBot(data);
        }

        const endpoint = getBotsEndpoint(data.group_id);
        const response = await fetchWithAuth(endpoint, {
            method: "POST",
            body: JSON.stringify(data),
        });
        return handleResponse<Bot>(response);
    },

    async listBots(
        groupId: string,
        limit: number = 20,
        offset: number = 0,
        search?: string,
        sortBy: string = "name"
    ): Promise<PaginatedBotsResponse> {
        if (USE_MOCK_DATA) {
            return mockBotsApi.listBots(limit, offset, search, sortBy);
        }

        const endpoint = getBotsEndpoint(groupId);
        const params = new URLSearchParams({
            limit: limit.toString(),
            offset: offset.toString(),
            sort_by: sortBy,
        });

        if (search) {
            params.append("search", search);
        }

        const response = await fetchWithAuth(
            `${endpoint}?${params.toString()}`
        );
        return handleResponse<PaginatedBotsResponse>(response);
    },

    async getBotDetails(groupId: string, botId: string): Promise<Bot> {
        if (USE_MOCK_DATA) {
            return mockBotsApi.getBot(botId);
        }

        const endpoint = getBotsEndpoint(groupId);
        const response = await fetchWithAuth(`${endpoint}/${botId}`);
        return handleResponse<Bot>(response);
    },

    async updateBot(
        groupId: string,
        botId: string,
        data: UpdateBotInput
    ): Promise<Bot> {
        if (USE_MOCK_DATA) {
            return mockBotsApi.updateBot(botId, data);
        }

        const endpoint = getBotsEndpoint(groupId);
        const response = await fetchWithAuth(`${endpoint}/${botId}`, {
            method: "PATCH",
            body: JSON.stringify(data),
        });
        return handleResponse<Bot>(response);
    },

    async uploadBotAvatar(
        groupId: string,
        botId: string,
        file: File
    ): Promise<{ avatar_url: string }> {
        if (USE_MOCK_DATA) {
            return { avatar_url: URL.createObjectURL(file) };
        }

        const endpoint = getBotsEndpoint(groupId);
        const form = new FormData();
        form.append("file", file);

        // Note: using fetch directly to avoid JSON headers
        const token = await getAuthToken();
        const response = await fetch(`${endpoint}/${botId}/avatar`, {
            method: "POST",
            body: form,
            headers: token ? { Authorization: `Bearer ${token}` } : undefined,
        });
        if (!response.ok) {
            const text = await response.text().catch(() => "");
            throw new Error(`Failed to upload avatar: ${response.status} ${text}`);
        }
        return response.json();
    },

    async deleteBot(groupId: string, botId: string): Promise<void> {
        if (USE_MOCK_DATA) {
            return mockBotsApi.deleteBot(botId);
        }

        const endpoint = getBotsEndpoint(groupId);
        const response = await fetchWithAuth(`${endpoint}/${botId}`, {
            method: "DELETE",
        });
        if (!response.ok) {
            throw new Error(`Failed to delete bot: ${response.status}`);
        }
    },

    async duplicateBot(
        groupId: string,
        botId: string,
        name?: string
    ): Promise<Bot> {
        if (USE_MOCK_DATA) {
            return mockBotsApi.duplicateBot(botId, name || "Copy of Bot");
        }

        const endpoint = getBotsEndpoint(groupId);
        const response = await fetchWithAuth(`${endpoint}/${botId}/duplicate`, {
            method: "POST",
            body: JSON.stringify({ name }),
        });
        return handleResponse<Bot>(response);
    },
};
