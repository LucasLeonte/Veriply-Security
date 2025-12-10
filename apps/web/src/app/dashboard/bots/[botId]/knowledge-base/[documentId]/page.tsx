"use client";

import { DashboardLayout } from "@/components";
import { DocumentDetail } from "@/components/kb";
import { useParams, useRouter } from "next/navigation";
import { ArrowLeft } from "lucide-react";
import Link from "next/link";
import {
    useDocumentQuery,
    useDocumentChunks,
    useDeleteDocument,
    useReprocessDocument,
} from "@/hooks/useDocumentsQuery";

export default function DocumentDetailPage() {
    const params = useParams();
    const router = useRouter();
    const botId = params.botId as string;
    const documentId = params.documentId as string;

    // Fetch document details
    const { data: documentData, isLoading, refetch } = useDocumentQuery(documentId);
    
    // Fetch chunks
    const { data: chunksData } = useDocumentChunks(documentId, 50, 0);

    const { mutate: deleteDocument } = useDeleteDocument();
    const { mutate: reprocessDocument } = useReprocessDocument();

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
            await deleteDocument(docId);
            // Redirect back to KB list after delete
            router.push(`/dashboard/bots/${botId}/knowledge-base`);
        } catch (err) {
            console.error("Delete failed:", err);
            throw err;
        }
    };

    // Show loading state while fetching
    if (isLoading || !documentData) {
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
                        {documentData.filename}
                    </h2>
                    <p className="text-sm text-slate-600 mt-1">
                        Document details and management
                    </p>
                </div>

                {/* Document Detail Component */}
                <DocumentDetail
                    document={documentData}
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
