import {
    Bot,
    CreateBotInput,
    UpdateBotInput,
    PaginatedBotsResponse,
} from "@/types/bot";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const BOTS_ENDPOINT = `${API_BASE_URL}/api/v1/bots`;

async function getAuthToken(): Promise<string | null> {
    // Only access localStorage on client-side
    if (typeof window === "undefined") {
        return null;
    }
    return localStorage.getItem("access_token");
}

async function fetchWithAuth(
    url: string,
    options: RequestInit = {}
): Promise<Response> {
    const token = await getAuthToken();
    const headers: any = {
        "Content-Type": "application/json",
        ...options.headers,
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
        const error = await response
            .json()
            .catch(() => ({ detail: "Unknown error" }));
        throw new Error(error.detail || `HTTP ${response.status}`);
    }
    return response.json();
}

export const botsApi = {
    async createBot(data: CreateBotInput): Promise<Bot> {
        const response = await fetchWithAuth(BOTS_ENDPOINT, {
            method: "POST",
            body: JSON.stringify(data),
        });
        return handleResponse<Bot>(response);
    },

    async listBots(
        limit: number = 20,
        offset: number = 0,
        search?: string,
        sortBy: string = "name"
    ): Promise<PaginatedBotsResponse> {
        const params = new URLSearchParams({
            limit: limit.toString(),
            offset: offset.toString(),
            sort_by: sortBy,
        });

        if (search) {
            params.append("search", search);
        }

        const response = await fetchWithAuth(
            `${BOTS_ENDPOINT}?${params.toString()}`
        );
        return handleResponse<PaginatedBotsResponse>(response);
    },

    async getBotDetails(botId: string): Promise<Bot> {
        const response = await fetchWithAuth(`${BOTS_ENDPOINT}/${botId}`);
        return handleResponse<Bot>(response);
    },

    async updateBot(botId: string, data: UpdateBotInput): Promise<Bot> {
        const response = await fetchWithAuth(`${BOTS_ENDPOINT}/${botId}`, {
            method: "PATCH",
            body: JSON.stringify(data),
        });
        return handleResponse<Bot>(response);
    },

    async deleteBot(botId: string): Promise<void> {
        const response = await fetchWithAuth(`${BOTS_ENDPOINT}/${botId}`, {
            method: "DELETE",
        });
        if (!response.ok) {
            throw new Error(`Failed to delete bot: ${response.status}`);
        }
    },

    async duplicateBot(botId: string, name?: string): Promise<Bot> {
        const response = await fetchWithAuth(
            `${BOTS_ENDPOINT}/${botId}/duplicate`,
            {
                method: "POST",
                body: JSON.stringify({ name }),
            }
        );
        return handleResponse<Bot>(response);
    },
};
