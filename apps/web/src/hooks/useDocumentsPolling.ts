import { useEffect, useRef, useCallback } from "react";
import { Document } from "@/types/document";
import { documentsApi } from "@/lib/api/documents";

interface UseDocumentsPollingProps {
    documents: Document[];
    groupId: string;
    enabled: boolean;
    intervalMs?: number;
    onUpdate: (updatedDocuments: Document[]) => void;
}

/**
 * Hook for polling document status updates in real-time
 * Polls documents that are in "processing" state
 */
export function useDocumentsPolling({
    documents,
    groupId,
    enabled,
    intervalMs = 2000, // Poll every 2 seconds
    onUpdate,
}: UseDocumentsPollingProps) {
    const pollingIntervalRef = useRef<NodeJS.Timeout | null>(null);
    const processingDocsRef = useRef<Set<string>>(new Set());

    // Identify which documents are currently processing
    useEffect(() => {
        const processingIds = new Set(
            documents
                .filter((doc) => doc.status === "processing")
                .map((doc) => doc.id)
        );
        processingDocsRef.current = processingIds;
    }, [documents]);

    // Polling logic
    const pollDocuments = useCallback(async () => {
        if (processingDocsRef.current.size === 0) {
            return;
        }

        try {
            const processingDocIds = Array.from(processingDocsRef.current);
            const updatedDocs: Document[] = [];

            // Fetch status for each processing document
            for (const docId of processingDocIds) {
                try {
                    const updatedDoc = await documentsApi.getDocument(docId);
                    updatedDocs.push(updatedDoc as Document);

                    // Remove from processing set if status changed
                    if (updatedDoc.status !== "processing") {
                        processingDocsRef.current.delete(docId);
                    }
                } catch (err) {
                    // Silently handle fetch errors
                }
            }

            // Notify parent component of updates
            if (updatedDocs.length > 0) {
                onUpdate(updatedDocs);
            }
        } catch (err) {
            // Silently handle polling errors
        }
    }, [onUpdate]);

    // Set up polling interval
    useEffect(() => {
        if (!enabled || !groupId || processingDocsRef.current.size === 0) {
            if (pollingIntervalRef.current) {
                clearInterval(pollingIntervalRef.current);
                pollingIntervalRef.current = null;
            }
            return;
        }

        // Initial poll immediately
        pollDocuments();

        // Set up recurring polls
        pollingIntervalRef.current = setInterval(pollDocuments, intervalMs);

        return () => {
            if (pollingIntervalRef.current) {
                clearInterval(pollingIntervalRef.current);
                pollingIntervalRef.current = null;
            }
        };
    }, [enabled, groupId, pollDocuments, intervalMs]);

    // Cleanup on unmount
    useEffect(() => {
        return () => {
            if (pollingIntervalRef.current) {
                clearInterval(pollingIntervalRef.current);
            }
        };
    }, []);
}
