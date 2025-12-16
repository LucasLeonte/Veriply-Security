"use client";

import { DashboardLayout } from "@/components";
import { KnowledgeBaseList } from "@/components/kb";
import { useParams } from "next/navigation";
import { ArrowLeft } from "lucide-react";
import Link from "next/link";
import { useState, useEffect } from "react";
import {
    useDocumentsQuery,
    useUploadDocuments,
    useDeleteDocument,
    useReprocessDocument,
} from "@/hooks/useDocumentsQuery";
import { useGroup } from "@/contexts/GroupContext";
import { foldersApi } from "@/lib/api/folders";
import type { Folder } from "@/types/folder";

export default function BotKnowledgeBasePage() {
    const params = useParams();
    const botId = params.botId as string;
    const { currentGroup } = useGroup();
    const groupId = currentGroup?.id;
    const [currentPage, setCurrentPage] = useState(1); // Pages are 1-indexed
    const [searchQuery, setSearchQuery] = useState("");
    const [folders, setFolders] = useState<Folder[]>([]);
    const [foldersLoading, setFoldersLoading] = useState(false);

    const ITEMS_PER_PAGE = 10;

    // Fetch documents with pagination and search
    const { data, isLoading, error, refetch } = useDocumentsQuery(
        groupId || "",
        currentPage,
        ITEMS_PER_PAGE,
        searchQuery || undefined
    );

    const { mutate: uploadDocuments } = useUploadDocuments();
    const { mutate: deleteDocument } = useDeleteDocument();
    const { mutate: reprocessDocument } = useReprocessDocument();

    // Fetch folders for the current group
    useEffect(() => {
        if (currentGroup?.id) {
            setFoldersLoading(true);
            foldersApi
                .listFolders(currentGroup.id)
                .then((fetchedFolders) => setFolders(fetchedFolders))
                .catch((err) => console.error("Failed to fetch folders:", err))
                .finally(() => setFoldersLoading(false));
        }
    }, [currentGroup?.id]);

    const handleUpload = async (files: File[], folderId?: string) => {
        try {
            if (!groupId) {
                throw new Error("Group not selected");
            }

            await uploadDocuments({ groupId, files, botId, folderId });
            // Refresh the list after upload
            refetch();
        } catch (err) {
            console.error("Upload failed:", err);
            throw err;
        }
    };

    const handleDelete = async (documentId: string) => {
        try {
            if (!groupId) {
                throw new Error("Group not selected");
            }

            await deleteDocument({ groupId, documentId });
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

    if (!groupId) {
        return (
            <DashboardLayout>
                <div className="space-y-6">
                    <div className="flex items-center gap-2">
                        <Link
                            href="/dashboard/bots"
                            className="flex items-center gap-2 text-sm text-slate-600 hover:text-slate-900 transition-colors"
                        >
                            <ArrowLeft size={16} />
                            Back to Bots
                        </Link>
                    </div>
                    <div className="bg-white border border-slate-200 rounded-lg p-6 text-center text-slate-600">
                        Please select a group to manage this bot's knowledge
                        base.
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
                    isLoading={isLoading || foldersLoading}
                    error={error?.message}
                    onUpload={handleUpload}
                    onDelete={handleDelete}
                    onReprocess={handleReprocess}
                    folders={folders}
                />
            </div>
        </DashboardLayout>
    );
}
