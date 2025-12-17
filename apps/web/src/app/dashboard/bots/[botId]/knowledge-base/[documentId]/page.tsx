"use client";

import { DashboardLayout } from "@/components";
import { DocumentDetail } from "@/components/kb";
import { useParams, useRouter } from "next/navigation";
import { ArrowLeft } from "lucide-react";
import Link from "next/link";
import { useEffect, useState, useCallback } from "react";
import {
    useDocumentQuery,
    useDocumentChunks,
    useDeleteDocument,
    useReprocessDocument,
} from "@/hooks/useDocumentsQuery";
import { useGroup } from "@/contexts/GroupContext";
import { documentsApi } from "@/lib/api/documents";
import type { Document } from "@/types/document";

export default function DocumentDetailPage() {
    const params = useParams();
    const router = useRouter();
    const botId = params.botId as string;
    const documentId = params.documentId as string;
    const { currentGroup } = useGroup();
    const [localDocument, setLocalDocument] = useState<Document | null>(null);
    const [pollingIntervalRef, setPollingIntervalRef] = useState<NodeJS.Timeout | null>(null);

    // Fetch document details
    const { data: documentData, isLoading, refetch } = useDocumentQuery(documentId);
    
    // Fetch chunks
    const { data: chunksData } = useDocumentChunks(documentId);

    const { mutate: deleteDocument } = useDeleteDocument();
    const { mutate: reprocessDocument } = useReprocessDocument();

    // Update local document when data changes
    useEffect(() => {
        if (documentData) {
            setLocalDocument(documentData);
        }
    }, [documentData]);

    // Poll for document status updates if processing
    useEffect(() => {
        if (!localDocument || localDocument.status !== "processing" || !documentId) {
            // Clear polling if not processing
            if (pollingIntervalRef) {
                clearInterval(pollingIntervalRef);
                setPollingIntervalRef(null);
            }
            return;
        }

        // Immediate poll
        const pollDocument = async () => {
            try {
                const updated = await documentsApi.getDocument(documentId);
                setLocalDocument(updated as Document);
            } catch (err) {
                console.error("Failed to poll document:", err);
            }
        };

        pollDocument();

        // Set up recurring polls every 2 seconds
        const interval = setInterval(pollDocument, 2000);
        setPollingIntervalRef(interval);

        return () => {
            if (interval) {
                clearInterval(interval);
            }
        };
    }, [localDocument?.status, documentId]);

    const handleReprocess = async (docId: string) => {
        try {
            await reprocessDocument(docId);
            // Refresh the document details after reprocess
            refetch();
        } catch (err) {
            console.error("Reprocess failed:", err);
            throw err;
        }
    };

    const handleDelete = async (docId: string) => {
        try {
            await deleteDocument({ groupId: currentGroup.id, documentId: docId });
            // Redirect back to KB list after delete
            router.push(`/dashboard/bots/${botId}/knowledge-base`);
        } catch (err) {
            console.error("Delete failed:", err);
            throw err;
        }
    };

    // Show loading state while fetching
    if (isLoading || !localDocument) {
        return (
            <DashboardLayout>
                <div className="space-y-6">
                    <div className="flex items-center gap-2">
                        <Link
                            href={`/dashboard/bots/${botId}/knowledge-base`}
                            className="flex items-center gap-2 text-sm text-slate-600 hover:text-slate-900 transition-colors"
                        >
                            <ArrowLeft size={16} />
                            Back to Knowledge Base
                        </Link>
                    </div>
                    <div className="flex items-center justify-center py-12">
                        <div className="text-slate-600">Loading document...</div>
                    </div>
                </div>
            </DashboardLayout>
        );
    }

    return (
        <DashboardLayout>
            <div className="space-y-6">
                {/* Breadcrumb / Back Navigation */}
                <div className="flex items-center gap-2">
                    <Link
                        href={`/dashboard/bots/${botId}/knowledge-base`}
                        className="flex items-center gap-2 text-sm text-slate-600 hover:text-slate-900 transition-colors"
                    >
                        <ArrowLeft size={16} />
                        Back to Knowledge Base
                    </Link>
                </div>

                {/* Document Header */}
                <div>
                    <h2 className="text-2xl font-semibold text-slate-900">
                        {localDocument.filename}
                    </h2>
                    <p className="text-sm text-slate-600 mt-1">
                        Document details and management
                    </p>
                </div>

                {/* Document Detail Component */}
                <DocumentDetail
                    document={localDocument}
                    chunks={chunksData?.chunks || []}
                    botId={botId}
                    onReprocess={handleReprocess}
                    onDelete={handleDelete}
                    isLoading={false}
                />
            </div>
        </DashboardLayout>
    );
}
