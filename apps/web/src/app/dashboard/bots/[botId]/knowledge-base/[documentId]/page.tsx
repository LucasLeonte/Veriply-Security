"use client";

import { DashboardLayout } from "@/components";
import { DocumentDetail } from "@/components/kb";
import { useParams, useRouter } from "next/navigation";
import { ArrowLeft } from "lucide-react";
import Link from "next/link";
import { useState } from "react";
import { Document, DocumentChunk } from "@/types/document";

// Mock data for demonstration - replace with actual API calls
const mockDocument: Document = {
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
};

const mockChunks: DocumentChunk[] = [
    {
        id: "chunk-1",
        document_id: "doc-1",
        content: "Welcome to the company! This handbook contains important information about our policies, procedures, and culture.",
        chunk_index: 0,
        created_at: "2025-01-15T14:31:00Z",
    },
    {
        id: "chunk-2",
        document_id: "doc-1",
        content: "Our mission is to provide exceptional service while maintaining a supportive work environment for all employees.",
        chunk_index: 1,
        created_at: "2025-01-15T14:31:00Z",
    },
    {
        id: "chunk-3",
        document_id: "doc-1",
        content: "Employee benefits include health insurance, dental coverage, vision plans, and a 401k with company matching.",
        chunk_index: 2,
        created_at: "2025-01-15T14:31:00Z",
    },
];

export default function DocumentDetailPage() {
    const params = useParams();
    const router = useRouter();
    const botId = params.botId as string;
    const documentId = params.documentId as string;
    const [isLoading, setIsLoading] = useState(false);

    const handleReprocess = async (docId: string) => {
        // TODO: Implement actual reprocess logic
        console.log("Reprocessing document:", docId);
        // Simulate API call
        await new Promise((resolve) => setTimeout(resolve, 1000));
    };

    const handleDelete = async (docId: string) => {
        // TODO: Implement actual delete logic
        console.log("Deleting document:", docId);
        // Redirect back to KB list after delete
        router.push(`/dashboard/bots/${botId}/knowledge-base`);
    };

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
                        {mockDocument.filename}
                    </h2>
                    <p className="text-sm text-slate-600 mt-1">
                        Document details and management
                    </p>
                </div>

                {/* Document Detail Component */}
                <DocumentDetail
                    document={mockDocument}
                    chunks={mockChunks}
                    botId={botId}
                    onReprocess={handleReprocess}
                    onDelete={handleDelete}
                    isLoading={isLoading}
                />
            </div>
        </DashboardLayout>
    );
}
