"use client";

import { DashboardLayout } from "@/components";
import { KnowledgeBaseList } from "@/components/kb";
import { useParams } from "next/navigation";
import { ArrowLeft } from "lucide-react";
import Link from "next/link";
import { useState } from "react";
import { Document } from "@/types/document";

// Mock data for demonstration - replace with actual API calls
const mockDocuments: Document[] = [
    {
        id: "doc-1",
        bot_id: "bot-123",
        filename: "Employee Handbook 2024.pdf",
        file_size: 131072,
        status: "processed",
        chunk_count: 42,
        embedding_count: 42,
        uploaded_at: "2025-01-15T14:30:00Z",
        processed_at: "2025-01-15T14:32:00Z",
        uploaded_by: "user-1",
        tenant_id: "tenant-1",
    },
    {
        id: "doc-2",
        bot_id: "bot-123",
        filename: "PTO Policy.docx",
        file_size: 45056,
        status: "processing",
        processing_progress: 60,
        chunk_count: 0,
        embedding_count: 0,
        uploaded_at: "2025-01-20T10:15:00Z",
        uploaded_by: "user-1",
        tenant_id: "tenant-1",
    },
    {
        id: "doc-3",
        bot_id: "bot-123",
        filename: "Benefits Guide.pdf",
        file_size: 98304,
        status: "failed",
        error_message: "File corrupted or unreadable",
        chunk_count: 0,
        embedding_count: 0,
        uploaded_at: "2025-01-18T09:00:00Z",
        uploaded_by: "user-1",
        tenant_id: "tenant-1",
    },
];

export default function BotKnowledgeBasePage() {
    const params = useParams();
    const botId = params.botId as string;
    const [documents, setDocuments] = useState<Document[]>(mockDocuments);
    const [isLoading, setIsLoading] = useState(false);

    const handleUpload = async (files: File[]) => {
        // TODO: Implement actual upload logic
        console.log("Uploading files:", files);
        // Simulate API call
        await new Promise((resolve) => setTimeout(resolve, 1000));
    };

    const handleDelete = async (documentId: string) => {
        // TODO: Implement actual delete logic
        console.log("Deleting document:", documentId);
        setDocuments((prev) => prev.filter((doc) => doc.id !== documentId));
    };

    const handleReprocess = async (documentId: string) => {
        // TODO: Implement actual reprocess logic
        console.log("Reprocessing document:", documentId);
        setDocuments((prev) =>
            prev.map((doc) =>
                doc.id === documentId
                    ? { ...doc, status: "processing" as const, processing_progress: 0 }
                    : doc
            )
        );
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
                    documents={documents}
                    totalCount={documents.length}
                    isLoading={isLoading}
                    onUpload={handleUpload}
                    onDelete={handleDelete}
                    onReprocess={handleReprocess}
                />
            </div>
        </DashboardLayout>
    );
}
