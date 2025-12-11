"use client";

import React, { useState } from "react";
import { Document, DocumentChunk } from "@/types/document";
import { CheckCircle, AlertCircle, Clock, Loader, RefreshCw, Trash2 } from "lucide-react";

interface DocumentDetailProps {
    document: Document;
    chunks?: DocumentChunk[];
    botId: string;
    onReprocess: (documentId: string) => Promise<void>;
    onDelete: (documentId: string) => Promise<void>;
    isLoading?: boolean;
}

export function DocumentDetail({
    document,
    chunks = [],
    botId: _botId,
    onReprocess,
    onDelete,
    isLoading = false,
}: DocumentDetailProps) {
    const [activeTab, setActiveTab] = useState<"details" | "chunks" | "actions">("details");
    const [isReprocessing, setIsReprocessing] = useState(false);
    const [isDeleting, setIsDeleting] = useState(false);

    const getStatusDisplay = () => {
        switch (document.status) {
            case "processed":
                return {
                    icon: <CheckCircle size={20} className="text-emerald-600" />,
                    text: "Processed successfully",
                    className: "text-emerald-600",
                };
            case "processing":
                return {
                    icon: <Loader size={20} className="text-amber-500 animate-spin" />,
                    text: `Processing${document.processing_progress ? ` ${document.processing_progress}%` : "..."}`,
                    className: "text-amber-500",
                };
            case "failed":
                return {
                    icon: <AlertCircle size={20} className="text-red-600" />,
                    text: "Processing failed",
                    className: "text-red-600",
                };
            case "pending":
                return {
                    icon: <Clock size={20} className="text-slate-400" />,
                    text: "Pending processing",
                    className: "text-slate-400",
                };
        }
    };

    const status = getStatusDisplay();
    const formattedSize = (document.file_size / 1024).toFixed(1) + " KB";

    const handleReprocess = async () => {
        setIsReprocessing(true);
        try {
            await onReprocess(document.id);
        } catch (err) {
            console.error("Reprocess failed:", err);
        } finally {
            setIsReprocessing(false);
        }
    };

    const handleDelete = async () => {
        if (!confirm(`Are you sure you want to delete ${document.filename}?`)) {
            return;
        }
        setIsDeleting(true);
        try {
            await onDelete(document.id);
        } catch (err) {
            console.error("Delete failed:", err);
        } finally {
            setIsDeleting(false);
        }
    };

    const formatDate = (dateString: string) => {
        const date = new Date(dateString);
        return date.toLocaleString("en-US", {
            month: "short",
            day: "numeric",
            year: "numeric",
            hour: "2-digit",
            minute: "2-digit",
        });
    };

    if (isLoading) {
        return (
            <div className="flex items-center justify-center py-12">
                <Loader size={32} className="text-slate-400 animate-spin" />
            </div>
        );
    }

    return (
        <div className="space-y-6">
            {/* Status Banner */}
            <div className={`flex items-center gap-3 p-4 bg-white border border-slate-200 rounded-lg ${status.className}`}>
                {status.icon}
                <span className="font-medium">{status.text}</span>
            </div>

            {/* Error Message */}
            {document.status === "failed" && document.error_message && (
                <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
                    <p className="text-sm font-medium text-red-900 mb-1">Error Details</p>
                    <p className="text-sm text-red-700">{document.error_message}</p>
                </div>
            )}

            {/* Tabs */}
            <div className="border-b border-slate-200">
                <div className="flex gap-6">
                    <button
                        onClick={() => setActiveTab("details")}
                        className={`px-1 py-3 text-sm font-medium border-b-2 transition-colors ${
                            activeTab === "details"
                                ? "border-emerald-600 text-slate-900"
                                : "border-transparent text-slate-600 hover:text-slate-900"
                        }`}
                    >
                        Details
                    </button>
                    <button
                        onClick={() => setActiveTab("chunks")}
                        className={`px-1 py-3 text-sm font-medium border-b-2 transition-colors ${
                            activeTab === "chunks"
                                ? "border-emerald-600 text-slate-900"
                                : "border-transparent text-slate-600 hover:text-slate-900"
                        }`}
                    >
                        Chunks ({document.chunk_count})
                    </button>
                    <button
                        onClick={() => setActiveTab("actions")}
                        className={`px-1 py-3 text-sm font-medium border-b-2 transition-colors ${
                            activeTab === "actions"
                                ? "border-emerald-600 text-slate-900"
                                : "border-transparent text-slate-600 hover:text-slate-900"
                        }`}
                    >
                        Actions
                    </button>
                </div>
            </div>

            {/* Tab Content */}
            <div className="bg-white rounded-lg border border-slate-200 p-6">
                {activeTab === "details" && (
                    <div className="space-y-6">
                        <div>
                            <h3 className="text-lg font-semibold text-slate-900 mb-4">
                                Document Information
                            </h3>
                            <div className="grid grid-cols-2 gap-6">
                                <div>
                                    <p className="text-sm text-slate-500 mb-1">File name</p>
                                    <p className="text-sm font-medium text-slate-900">{document.filename}</p>
                                </div>
                                <div>
                                    <p className="text-sm text-slate-500 mb-1">File size</p>
                                    <p className="text-sm font-medium text-slate-900">{formattedSize}</p>
                                </div>
                                <div>
                                    <p className="text-sm text-slate-500 mb-1">Uploaded</p>
                                    <p className="text-sm font-medium text-slate-900">
                                        {formatDate(document.created_at)}
                                    </p>
                                </div>
                                <div>
                                    <p className="text-sm text-slate-500 mb-1">Status</p>
                                    <div className={`flex items-center gap-2 ${status.className}`}>
                                        {status.icon}
                                        <p className="text-sm font-medium">{status.text}</p>
                                    </div>
                                </div>
                                <div>
                                    <p className="text-sm text-slate-500 mb-1">Chunks</p>
                                    <p className="text-sm font-medium text-slate-900">
                                        {document.chunk_count} chunks
                                    </p>
                                </div>
                                <div>
                                    <p className="text-sm text-slate-500 mb-1">Last updated</p>
                                    <p className="text-sm font-medium text-slate-900">
                                        {formatDate(document.updated_at)}
                                    </p>
                                </div>
                            </div>
                        </div>
                    </div>
                )}

                {activeTab === "chunks" && (
                    <div className="space-y-4">
                        <h3 className="text-lg font-semibold text-slate-900">
                            Chunks Preview ({chunks.length} total)
                        </h3>
                        {chunks.length === 0 ? (
                            <p className="text-sm text-slate-600">
                                {document.status === "processed"
                                    ? "No chunks available"
                                    : "Chunks will appear after processing completes"}
                            </p>
                        ) : (
                            <div className="space-y-3">
                                {chunks.slice(0, 10).map((chunk) => (
                                    <div
                                        key={chunk.id}
                                        className="p-3 bg-slate-50 rounded-md border border-slate-200"
                                    >
                                        <div className="flex items-center gap-2 mb-2">
                                            <span className="text-xs font-medium text-slate-500">
                                                Chunk {chunk.chunk_index + 1}
                                            </span>
                                        </div>
                                        <p className="text-sm text-slate-700 line-clamp-3">
                                            {chunk.content}
                                        </p>
                                    </div>
                                ))}
                                {chunks.length > 10 && (
                                    <p className="text-sm text-slate-500 text-center py-2">
                                        Showing first 10 of {chunks.length} chunks
                                    </p>
                                )}
                            </div>
                        )}
                    </div>
                )}

                {activeTab === "actions" && (
                    <div className="space-y-6">
                        <div>
                            <h3 className="text-lg font-semibold text-slate-900 mb-4">
                                Document Actions
                            </h3>
                            <div className="space-y-3">
                                <div className="flex items-start justify-between p-4 bg-slate-50 rounded-lg">
                                    <div>
                                        <h4 className="font-medium text-slate-900 mb-1">
                                            Reprocess Document
                                        </h4>
                                        <p className="text-sm text-slate-600">
                                            Re-run the processing pipeline to update chunks and embeddings
                                        </p>
                                    </div>
                                    <button
                                        onClick={handleReprocess}
                                        disabled={isReprocessing || document.status === "processing"}
                                        className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-slate-700 bg-white border border-slate-300 rounded-md hover:bg-slate-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                                    >
                                        <RefreshCw size={16} />
                                        {isReprocessing ? "Reprocessing..." : "Reprocess"}
                                    </button>
                                </div>

                                <div className="flex items-start justify-between p-4 bg-red-50 rounded-lg border border-red-200">
                                    <div>
                                        <h4 className="font-medium text-red-900 mb-1">
                                            Delete Document
                                        </h4>
                                        <p className="text-sm text-red-700">
                                            Permanently remove this document and all associated data
                                        </p>
                                    </div>
                                    <button
                                        onClick={handleDelete}
                                        disabled={isDeleting}
                                        className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-red-600 rounded-md hover:bg-red-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                                    >
                                        <Trash2 size={16} />
                                        {isDeleting ? "Deleting..." : "Delete"}
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}
