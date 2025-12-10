import {
    Document,
    DocumentChunk,
    PaginatedDocumentsResponse,
    DocumentDetailResponse,
} from "@/types/document";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

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
    const headers: Record<string, string> = {
        ...(options.headers as Record<string, string>),
    };

    // Only set Content-Type if not FormData (for file uploads)
    if (!(options.body instanceof FormData)) {
        headers["Content-Type"] = "application/json";
    }

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

export const documentsApi = {
    /**
     * List documents for a specific bot
     */
    async listDocuments(
        botId: string,
        limit: number = 20,
        offset: number = 0,
        search?: string
    ): Promise<PaginatedDocumentsResponse> {
        const params = new URLSearchParams({
            limit: limit.toString(),
            offset: offset.toString(),
        });

        if (search) {
            params.append("search", search);
        }

        const response = await fetchWithAuth(
            `${API_BASE_URL}/api/v1/bots/${botId}/documents?${params.toString()}`
        );
        return handleResponse<PaginatedDocumentsResponse>(response);
    },

    /**
     * Get document details including chunks
     */
    async getDocument(documentId: string): Promise<DocumentDetailResponse> {
        const response = await fetchWithAuth(
            `${API_BASE_URL}/api/v1/documents/${documentId}`
        );
        return handleResponse<DocumentDetailResponse>(response);
    },

    /**
     * Upload one or more documents to a bot's knowledge base
     */
    async uploadDocuments(
        botId: string,
        files: File[]
    ): Promise<{ documents: Document[] }> {
        const formData = new FormData();
        
        files.forEach((file) => {
            formData.append("files", file);
        });

        const response = await fetchWithAuth(
            `${API_BASE_URL}/api/v1/bots/${botId}/documents`,
            {
                method: "POST",
                body: formData,
            }
        );
        return handleResponse<{ documents: Document[] }>(response);
    },

    /**
     * Delete a document and all associated chunks/embeddings
     */
    async deleteDocument(documentId: string): Promise<void> {
        const response = await fetchWithAuth(
            `${API_BASE_URL}/api/v1/documents/${documentId}`,
            {
                method: "DELETE",
            }
        );
        if (!response.ok) {
            throw new Error(`Failed to delete document: ${response.status}`);
        }
    },

    /**
     * Trigger reprocessing of a document
     */
    async reprocessDocument(documentId: string): Promise<Document> {
        const response = await fetchWithAuth(
            `${API_BASE_URL}/api/v1/documents/${documentId}/reprocess`,
            {
                method: "POST",
            }
        );
        return handleResponse<Document>(response);
    },

    /**
     * Get chunks for a specific document
     */
    async getDocumentChunks(
        documentId: string,
        limit: number = 50,
        offset: number = 0
    ): Promise<{ chunks: DocumentChunk[]; total_count: number }> {
        const params = new URLSearchParams({
            limit: limit.toString(),
            offset: offset.toString(),
        });

        const response = await fetchWithAuth(
            `${API_BASE_URL}/api/v1/documents/${documentId}/chunks?${params.toString()}`
        );
        return handleResponse<{ chunks: DocumentChunk[]; total_count: number }>(
            response
        );
    },
};
