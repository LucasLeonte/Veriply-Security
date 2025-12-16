import {
    DocumentChunk,
    PaginatedDocumentsResponse,
    DocumentDetailResponse,
} from "@/types/document";
import { mockDocumentsApi } from "./mockDocuments";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const USE_MOCK_DATA = process.env.NEXT_PUBLIC_USE_MOCK_DATA === "true";

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

export const documentsApi = {
    /**
     * List documents for a specific bot
     */
    async listDocuments(
        botId: string,
        page: number = 1,
        pageSize: number = 20,
        search?: string
    ): Promise<PaginatedDocumentsResponse> {
        if (USE_MOCK_DATA) {
            return mockDocumentsApi.listDocuments(botId, page, pageSize, search);
        }

        const params = new URLSearchParams({
            page: page.toString(),
            page_size: pageSize.toString(),
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
        if (USE_MOCK_DATA) {
            return mockDocumentsApi.getDocument(documentId);
        }

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
    ): Promise<{ id: string; document_id: string; status: string; queued: boolean }> {
        if (USE_MOCK_DATA) {
            return mockDocumentsApi.uploadDocuments(botId, files);
        }

        const formData = new FormData();
        
        files.forEach((file) => {
            formData.append("files", file);
        });

        const url = `${API_BASE_URL}/api/v1/bots/${botId}/documents`;
        console.log('[Upload] Uploading to:', url);
        console.log('[Upload] Files:', files.map(f => f.name));
        
        const response = await fetchWithAuth(url, {
            method: "POST",
            body: formData,
        });
        
        console.log('[Upload] Response status:', response.status);
        return handleResponse<{ id: string; document_id: string; status: string; queued: boolean }>(response);
    },

    /**
     * Delete a document and all associated chunks/embeddings
     */
    async deleteDocument(documentId: string): Promise<void> {
        if (USE_MOCK_DATA) {
            return mockDocumentsApi.deleteDocument(documentId);
        }

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
     * Delete multiple documents in bulk
     */
    async bulkDeleteDocuments(botId: string, documentIds: string[]): Promise<{
        message: string;
        queued_count: number;
        document_ids: string[];
    }> {
        if (USE_MOCK_DATA) {
            return mockDocumentsApi.bulkDeleteDocuments(botId, documentIds);
        }

        const response = await fetchWithAuth(
            `${API_BASE_URL}/api/v1/documents/bulk-delete`,
            {
                method: "POST",
                body: JSON.stringify({
                    bot_id: botId,
                    document_ids: documentIds,
                }),
            }
        );
        return handleResponse<{
            message: string;
            queued_count: number;
            document_ids: string[];
        }>(response);
    },

    /**
     * Trigger reprocessing of a document
     */
    async reprocessDocument(documentId: string): Promise<{ id: string; status: string; queued: boolean }> {
        if (USE_MOCK_DATA) {
            return mockDocumentsApi.reprocessDocument(documentId);
        }

        const response = await fetchWithAuth(
            `${API_BASE_URL}/api/v1/documents/${documentId}/reprocess`,
            {
                method: "POST",
            }
        );
        return handleResponse<{ id: string; status: string; queued: boolean }>(response);
    },

    /**
     * Get chunks for a specific document
     */
    async getDocumentChunks(
        documentId: string
    ): Promise<{ chunks: DocumentChunk[]; total: number }> {
        if (USE_MOCK_DATA) {
            return mockDocumentsApi.getDocumentChunks(documentId);
        }

        const response = await fetchWithAuth(
            `${API_BASE_URL}/api/v1/documents/${documentId}/chunks`
        );
        return handleResponse<{ chunks: DocumentChunk[]; total: number }>(
            response
        );
    },
};
