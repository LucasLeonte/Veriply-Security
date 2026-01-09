import { useState } from "react";
import { documentsApi } from "@/lib/api/documents";

// Simple toast utility (can be replaced with a proper toast library like sonner or react-hot-toast)
const toast = {
    success: (message: string) => {
        // TODO: Integrate with toast library
    },
    error: (message: string) => {
        // TODO: Integrate with toast library
    },
};

export interface UseDocumentDeletionReturn {
    deleteDocument: (
        groupId: string,
        documentId: string,
        documentName: string
    ) => Promise<boolean>;
    bulkDeleteDocuments: (
        botId: string,
        documentIds: string[],
        documentNames: string[]
    ) => Promise<boolean>;
    deletingIds: Set<string>;
    isDeleting: boolean;
}

export function useDocumentDeletion(): UseDocumentDeletionReturn {
    const [deletingIds, setDeletingIds] = useState<Set<string>>(new Set());
    const [isDeleting, setIsDeleting] = useState(false);

    const deleteDocument = async (
        groupId: string,
        documentId: string,
        documentName: string
    ): Promise<boolean> => {
        // Add to deleting set
        setDeletingIds((prev) => new Set([...prev, documentId]));
        setIsDeleting(true);

        try {
            await documentsApi.deleteDocument(groupId, documentId);

            // Success
            toast.success("Document deleted successfully");

            // Remove from deleting set
            setDeletingIds((prev) => {
                const newSet = new Set(prev);
                newSet.delete(documentId);
                return newSet;
            });

            return true;
        } catch (error) {
            // Remove from deleting set on error
            setDeletingIds((prev) => {
                const newSet = new Set(prev);
                newSet.delete(documentId);
                return newSet;
            });

            // Error handling
            const errorMessage =
                error instanceof Error ? error.message : "Unknown error";

            if (
                errorMessage.includes("404") ||
                errorMessage.includes("not found")
            ) {
                toast.error("Document no longer exists");
            } else {
                toast.error("Failed to delete document. Please try again.");
            }

            return false;
        } finally {
            setIsDeleting(false);
        }
    };

    const bulkDeleteDocuments = async (
        botId: string,
        documentIds: string[],
        documentNames: string[]
    ): Promise<boolean> => {
        // Validate max 100 documents
        if (documentIds.length > 100) {
            toast.error(
                "Maximum 100 documents can be deleted at once. Please select fewer documents."
            );
            return false;
        }

        // Add all to deleting set
        setDeletingIds((prev) => new Set([...prev, ...documentIds]));
        setIsDeleting(true);

        try {
            const result = await documentsApi.bulkDeleteDocuments(
                botId,
                documentIds
            );

            // Success
            const count = result.queued_count ?? documentIds.length;
            toast.success(`${count} document(s) deleted successfully`);

            // Remove all from deleting set
            setDeletingIds((prev) => {
                const newSet = new Set(prev);
                documentIds.forEach((id) => newSet.delete(id));
                return newSet;
            });

            return true;
        } catch (error) {
            // Remove all from deleting set on error
            setDeletingIds((prev) => {
                const newSet = new Set(prev);
                documentIds.forEach((id) => newSet.delete(id));
                return newSet;
            });

            // Error handling
            const errorMessage =
                error instanceof Error ? error.message : "Unknown error";

            if (
                errorMessage.includes("400") ||
                errorMessage.includes("Bad Request")
            ) {
                toast.error("Maximum 100 documents can be deleted at once");
            } else {
                toast.error(`Failed to delete documents. Please try again.`);
            }

            return false;
        } finally {
            setIsDeleting(false);
        }
    };

    return {
        deleteDocument,
        bulkDeleteDocuments,
        deletingIds,
        isDeleting,
    };
}
