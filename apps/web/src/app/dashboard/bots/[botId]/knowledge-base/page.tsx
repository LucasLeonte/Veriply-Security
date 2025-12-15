"use client";

import { DashboardLayout } from "@/components";
import { KnowledgeBaseList } from "@/components/kb";
import { useParams } from "next/navigation";
import { ArrowLeft } from "lucide-react";
import Link from "next/link";
import { useState } from "react";
import {
    useDocumentsQuery,
    useUploadDocuments,
    useDeleteDocument,
    useReprocessDocument,
} from "@/hooks/useDocumentsQuery";

export default function BotKnowledgeBasePage() {
    const params = useParams();
    const botId = params.botId as string;
    const [currentPage, setCurrentPage] = useState(1); // Pages are 1-indexed
    const [searchQuery, setSearchQuery] = useState("");

    const ITEMS_PER_PAGE = 10;

    // Fetch documents with pagination and search
    const { data, isLoading, error, refetch } = useDocumentsQuery(
        botId,
        currentPage,
        ITEMS_PER_PAGE,
        searchQuery || undefined
    );

    const { mutate: uploadDocuments } = useUploadDocuments();
    const { mutate: deleteDocument } = useDeleteDocument();
    const { mutate: reprocessDocument } = useReprocessDocument();

    const handleUpload = async (files: File[]) => {
        try {
            await uploadDocuments({ groupId: botId, files, botId });
            // Refresh the list after upload
            refetch();
        } catch (err) {
            console.error("Upload failed:", err);
            throw err;
        }
    };

    const handleDelete = async (documentId: string) => {
        try {
            await deleteDocument({ groupId: botId, documentId });
            // Refresh the list after delete
            refetch();
        } catch (err) {
            console.error("Delete failed:", err);
            throw err;
        }
    };

    const handleReprocess = async (documentId: string) => {
        try {
            await reprocessDocument(documentId);
            // Refresh the list after reprocess
            refetch();
        } catch (err) {
            console.error("Reprocess failed:", err);
            throw err;
        }
    };

    return (
        <DashboardLayout>
            <div className="space-y-6">
                {/* Breadcrumb / Back Navigation */}
                <div className="flex items-center gap-2">
                    <Link
                        href="/dashboard/bots"
                        className="flex items-center gap-2 text-sm text-slate-600 hover:text-slate-900 transition-colors"
                    >
                        <ArrowLeft size={16} />
                        Back to Bots
                    </Link>
                </div>

                {/* Page Header */}
                <div className="flex items-center justify-between">
                    <div>
                        <h2 className="text-2xl font-semibold text-slate-900">
                            Knowledge Base
                        </h2>
                        <p className="text-sm text-slate-600 mt-1">
                            Manage documents for this bot
                        </p>
                    </div>
                </div>

                {/* Knowledge Base List Component */}
                <KnowledgeBaseList
                    botId={botId}
                    documents={data?.documents || []}
                    totalCount={data?.total || 0}
                    currentPage={currentPage}
                    totalPages={data?.total_pages || 0}
                    onPageChange={setCurrentPage}
                    onSearchChange={setSearchQuery}
                    isLoading={isLoading}
                    error={error?.message}
                    onUpload={handleUpload}
                    onDelete={handleDelete}
                    onReprocess={handleReprocess}
                />
            </div>
        </DashboardLayout>
    );
}
