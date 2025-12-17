import {
    DocumentChunk,
    PaginatedDocumentsResponse,
    DocumentDetailResponse,
    Document,
} from "@/types/document";
import { mockDocumentsApi } from "./mockDocuments";
import { getAccessToken } from "@/lib/auth";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const USE_MOCK_DATA = process.env.NEXT_PUBLIC_USE_MOCK_DATA === "true";

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
     * List documents for a specific group
     */
    async listDocuments(
        groupId: string,
        page: number = 1,
        pageSize: number = 20,
        search?: string
    ): Promise<PaginatedDocumentsResponse> {
        if (USE_MOCK_DATA) {
            return mockDocumentsApi.listDocuments(
                groupId,
                page,
                pageSize,
                search
            );
        }

        const params = new URLSearchParams({
            page: page.toString(),
            page_size: pageSize.toString(),
        });

        if (search) {
            params.append("search", search);
        }

        const response = await fetchWithAuth(
            `${API_BASE_URL}/api/v1/groups/${groupId}/documents?${params.toString()}`
        );
        // Backend may return an array (non-paginated). Normalize to PaginatedDocumentsResponse.
        const data = await handleResponse<
            PaginatedDocumentsResponse | Document[]
        >(response);
        if (Array.isArray(data)) {
            return {
                documents: data as Document[],
                total: data.length,
                page,
                page_size: pageSize,
                total_pages: Math.max(1, Math.ceil(data.length / pageSize)),
            } satisfies PaginatedDocumentsResponse;
        }
        return data as PaginatedDocumentsResponse;
    },

    /**
     * Get document details including chunks
     */
    async getDocument(
        documentId: string,
        groupId?: string
    ): Promise<DocumentDetailResponse> {
        if (USE_MOCK_DATA) {
            return mockDocumentsApi.getDocument(documentId);
        }

        const url = groupId
            ? `${API_BASE_URL}/api/v1/groups/${groupId}/documents/${documentId}`
            : `${API_BASE_URL}/api/v1/documents/${documentId}`;

        const response = await fetchWithAuth(url);
        return handleResponse<DocumentDetailResponse>(response);
    },

    /**
     * Upload one or more documents to a group's knowledge base
     */
    async uploadDocuments(
        groupId: string,
        files: File[],
        botId?: string,
        folderId?: string
    ): Promise<{
        id: string;
        document_id: string;
        status: string;
        queued: boolean;
    }> {
        if (USE_MOCK_DATA) {
            return mockDocumentsApi.uploadDocuments(groupId, files);
        }

        // Backend expects single file per request, so upload first file
        // TODO: Support batch uploads or loop through files
        if (files.length === 0) {
            throw new Error("No files to upload");
        }

        const formData = new FormData();

        // Backend expects 'file' (singular)
        formData.append("file", files[0]);

        if (botId) {
            formData.append("bot_id", botId);
        }

        if (folderId) {
            formData.append("folder_id", folderId);
        }

        const response = await fetchWithAuth(
            `${API_BASE_URL}/api/v1/groups/${groupId}/documents/upload`,
            {
                method: "POST",
                body: formData,
            }
        );
        return handleResponse<{
            id: string;
            document_id: string;
            status: string;
            queued: boolean;
        }>(response);
    },

    /**
     * Delete a document and all associated chunks/embeddings
     */
    async deleteDocument(groupId: string, documentId: string): Promise<void> {
        if (USE_MOCK_DATA) {
            return mockDocumentsApi.deleteDocument(documentId);
        }

        const response = await fetchWithAuth(
            `${API_BASE_URL}/api/v1/groups/${groupId}/documents/${documentId}`,
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
    async bulkDeleteDocuments(
        botId: string,
        documentIds: string[]
    ): Promise<{
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
     * Trigger reprocessing of a document (group-scoped)
     */
    async reprocessDocument(
        groupId: string,
        documentId: string
    ): Promise<{
        id: string;
        status: string;
        message?: string;
        queued?: boolean;
    }> {
        if (USE_MOCK_DATA) {
            return Promise.resolve({
                id: documentId,
                status: "processing",
                queued: true,
                message: "Reprocess queued",
            });
        }

        const response = await fetchWithAuth(
            `${API_BASE_URL}/api/v1/groups/${groupId}/documents/${documentId}/reprocess`,
            {
                method: "POST",
            }
        );
        return handleResponse<{
            id: string;
            status: string;
            message?: string;
            queued?: boolean;
        }>(response);
    },

    /**
     * Bulk reprocess documents (max 100)
     */
    async bulkReprocessDocuments(
        groupId: string,
        documentIds: string[]
    ): Promise<{
        message: string;
        queued_count: number;
        document_ids: string[];
    }> {
        if (USE_MOCK_DATA) {
            return Promise.resolve({
                message: `Queued ${documentIds.length} document(s) for reprocessing (mock).`,
                queued_count: documentIds.length,
                document_ids: documentIds,
            });
        }

        const response = await fetchWithAuth(
            `${API_BASE_URL}/api/v1/groups/${groupId}/documents/bulk-reprocess`,
            {
                method: "POST",
                body: JSON.stringify({ document_ids: documentIds }),
            }
        );
        return handleResponse<{
            message: string;
            queued_count: number;
            document_ids: string[];
        }>(response);
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
        const data = await handleResponse<
            { chunks: DocumentChunk[]; total: number } | DocumentChunk[]
        >(response);
        if (Array.isArray(data)) {
            return { chunks: data as DocumentChunk[], total: data.length };
        }
        return data as { chunks: DocumentChunk[]; total: number };
    },

    /**
     * Move a document to a folder
     */
    async moveDocumentToFolder(
        documentId: string,
        folderId: string | null,
        groupId: string
    ): Promise<Document> {
        if (USE_MOCK_DATA) {
            return mockDocumentsApi.getDocument(documentId);
        }

        const response = await fetchWithAuth(
            `${API_BASE_URL}/api/v1/documents/${documentId}/move`,
            {
                method: "PATCH",
                body: JSON.stringify({
                    folder_id: folderId,
                }),
            }
        );
        return handleResponse<Document>(response);
    },
};
