import { useState, useCallback, useEffect } from "react";
import {
    Document,
    DocumentDetailResponse,
    PaginatedDocumentsResponse,
} from "@/types/document";
import { documentsApi } from "@/lib/api/documents";

/**
 * Hook to fetch documents for a specific bot
 */
export function useDocumentsQuery(
    botId: string,
    limit: number = 20,
    offset: number = 0,
    search?: string
) {
    const [data, setData] = useState<PaginatedDocumentsResponse | null>(null);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<Error | null>(null);

    const refetch = useCallback(async () => {
        if (!botId) return;

        setIsLoading(true);
        setError(null);
        try {
            const result = await documentsApi.listDocuments(
                botId,
                limit,
                offset,
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
    }, [botId, limit, offset, search]);

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
        async (
            botId: string,
            files: File[]
        ): Promise<{ documents: Document[] }> => {
            setIsPending(true);
            setError(null);
            try {
                const result = await documentsApi.uploadDocuments(botId, files);
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

    const mutate = useCallback(async (documentId: string): Promise<void> => {
        setIsPending(true);
        setError(null);
        try {
            await documentsApi.deleteDocument(documentId);
        } catch (err) {
            const error =
                err instanceof Error
                    ? err
                    : new Error("Failed to delete document");
            setError(error);
            throw error;
        } finally {
            setIsPending(false);
        }
    }, []);

    return { mutate, isPending, error };
}

/**
 * Hook to reprocess a document
 */
export function useReprocessDocument() {
    const [isPending, setIsPending] = useState(false);
    const [error, setError] = useState<Error | null>(null);

    const mutate = useCallback(async (documentId: string): Promise<Document> => {
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
    }, []);

    return { mutate, isPending, error };
}

/**
 * Hook to fetch document chunks
 */
export function useDocumentChunks(
    documentId: string,
    limit: number = 50,
    offset: number = 0
) {
    const [data, setData] = useState<{
        chunks: any[];
        total_count: number;
    } | null>(null);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<Error | null>(null);

    const refetch = useCallback(async () => {
        if (!documentId) return;

        setIsLoading(true);
        setError(null);
        try {
            const result = await documentsApi.getDocumentChunks(
                documentId,
                limit,
                offset
            );
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
    }, [documentId, limit, offset]);

    useEffect(() => {
        refetch();
    }, [refetch]);

    return { data, isLoading, error, refetch };
}
