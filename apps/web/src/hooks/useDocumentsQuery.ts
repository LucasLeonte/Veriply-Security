import { useState, useCallback, useEffect, useRef } from "react";
import {
    DocumentDetailResponse,
    PaginatedDocumentsResponse,
} from "@/types/document";
import { documentsApi } from "@/lib/api/documents";

/**
 * Hook to fetch documents for a specific group
 */
export function useDocumentsQuery(
    groupId: string,
    page: number = 1,
    pageSize: number = 20,
    search?: string
) {
    const [data, setData] = useState<PaginatedDocumentsResponse | null>(null);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<Error | null>(null);

    const refetch = useCallback(async () => {
        if (!groupId) return;

        setIsLoading(true);
        setError(null);
        try {
            const result = await documentsApi.listDocuments(
                groupId,
                page,
                pageSize,
                search
            );
            setData(result);
        } catch (err) {
            setError(
                err instanceof Error
                    ? err
                    : new Error("Failed to fetch documents")
            );
        } finally {
            setIsLoading(false);
        }
    }, [groupId, page, pageSize, search]);

    useEffect(() => {
        refetch();
    }, [refetch]);

    return { data, isLoading, error, refetch };
}

/**
 * Hook to fetch a single document with details
 */
export function useDocumentQuery(documentId: string) {
    const [data, setData] = useState<DocumentDetailResponse | null>(null);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<Error | null>(null);

    const refetch = useCallback(async () => {
        if (!documentId) return;

        setIsLoading(true);
        setError(null);
        try {
            const result = await documentsApi.getDocument(documentId);
            setData(result);
        } catch (err) {
            setError(
                err instanceof Error
                    ? err
                    : new Error("Failed to fetch document")
            );
        } finally {
            setIsLoading(false);
        }
    }, [documentId]);

    useEffect(() => {
        refetch();
    }, [refetch]);

    return { data, isLoading, error, refetch };
}

/**
 * Hook to upload documents
 */
export function useUploadDocuments() {
    const [isPending, setIsPending] = useState(false);
    const [error, setError] = useState<Error | null>(null);

    const mutate = useCallback(
        async (params: {
            groupId: string;
            files: File[];
            botId?: string;
            folderId?: string;
        }): Promise<{
            id: string;
            document_id: string;
            status: string;
            queued: boolean;
        }> => {
            setIsPending(true);
            setError(null);
            try {
                const result = await documentsApi.uploadDocuments(
                    params.groupId,
                    params.files,
                    params.botId,
                    params.folderId
                );
                return result;
            } catch (err) {
                const error =
                    err instanceof Error
                        ? err
                        : new Error("Failed to upload documents");
                setError(error);
                throw error;
            } finally {
                setIsPending(false);
            }
        },
        []
    );

    return { mutate, isPending, error };
}

/**
 * Hook to delete a document
 */
export function useDeleteDocument() {
    const [isPending, setIsPending] = useState(false);
    const [error, setError] = useState<Error | null>(null);
    const lastErrorRef = useRef<Error | null>(null);

    const mutate = useCallback(
        async (params: {
            groupId: string;
            documentId: string;
        }): Promise<void> => {
            setIsPending(true);
            setError(null);
            lastErrorRef.current = null;
            try {
                await documentsApi.deleteDocument(
                    params.groupId,
                    params.documentId
                );
            } catch (err) {
                const error =
                    err instanceof Error
                        ? err
                        : new Error("Failed to delete document");
                lastErrorRef.current = error;
                setError(error);
                throw error;
            } finally {
                // Ensure error state is set before clearing pending so tests see it
                if (lastErrorRef.current) {
                    setError(lastErrorRef.current);
                }
                setIsPending(false);
            }
        },
        []
    );

    return { mutate, isPending, error };
}

/**
 * Hook to reprocess a document
 */
export function useReprocessDocument() {
    const [isPending, setIsPending] = useState(false);
    const [error, setError] = useState<Error | null>(null);

    const mutate = useCallback(
        async (
            documentId: string
        ): Promise<{ id: string; status: string; queued: boolean }> => {
            setIsPending(true);
            setError(null);
            try {
                const result = await documentsApi.reprocessDocument(documentId);
                return result;
            } catch (err) {
                const error =
                    err instanceof Error
                        ? err
                        : new Error("Failed to reprocess document");
                setError(error);
                throw error;
            } finally {
                setIsPending(false);
            }
        },
        []
    );

    return { mutate, isPending, error };
}

/**
 * Hook to fetch document chunks
 */
export function useDocumentChunks(documentId: string) {
    const [data, setData] = useState<{
        chunks: unknown[];
        total: number;
    } | null>(null);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<Error | null>(null);

    const refetch = useCallback(async () => {
        if (!documentId) return;

        setIsLoading(true);
        setError(null);
        try {
            const result = await documentsApi.getDocumentChunks(documentId);
            setData(result);
        } catch (err) {
            setError(
                err instanceof Error
                    ? err
                    : new Error("Failed to fetch document chunks")
            );
        } finally {
            setIsLoading(false);
        }
    }, [documentId]);

    useEffect(() => {
        refetch();
    }, [refetch]);

    return { data, isLoading, error, refetch };
}
