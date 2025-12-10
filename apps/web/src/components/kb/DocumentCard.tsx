"use client";

import React from "react";
import { Document } from "@/types/document";
import { FileText, MoreVertical, CheckCircle, AlertCircle, Clock, Loader } from "lucide-react";

interface DocumentCardProps {
    document: Document;
    onView?: (document: Document) => void;
    onDelete?: (document: Document) => void;
    onReprocess?: (document: Document) => void;
}

export function DocumentCard({
    document,
    onView,
    onDelete,
    onReprocess,
}: DocumentCardProps) {
    const [showMenu, setShowMenu] = React.useState(false);

    const getStatusDisplay = () => {
        switch (document.status) {
            case "processed":
                return {
                    icon: <CheckCircle size={16} className="text-emerald-600" />,
                    text: "Processed",
                    className: "text-emerald-600",
                };
            case "processing":
                return {
                    icon: <Loader size={16} className="text-amber-500 animate-spin" />,
                    text: `Processing${document.processing_progress ? ` ${document.processing_progress}%` : "..."}`,
                    className: "text-amber-500",
                };
            case "failed":
                return {
                    icon: <AlertCircle size={16} className="text-red-600" />,
                    text: "Failed",
                    className: "text-red-600",
                };
            case "pending":
                return {
                    icon: <Clock size={16} className="text-slate-400" />,
                    text: "Pending",
                    className: "text-slate-400",
                };
        }
    };

    const status = getStatusDisplay();
    const formattedSize = (document.file_size / 1024).toFixed(1) + " KB";
    const uploadDate = new Date(document.uploaded_at).toLocaleDateString("en-US", {
        month: "short",
        day: "numeric",
        year: "numeric",
    });

    return (
        <div className="border border-slate-200 rounded-lg p-4 hover:shadow-md transition-shadow bg-white">
            <div className="flex items-start gap-3">
                {/* File Icon */}
                <FileText size={24} className="text-slate-400 flex-shrink-0 mt-1" />

                {/* Content */}
                <div className="flex-1 min-w-0">
                    {/* File Name */}
                    <h3
                        className="font-medium text-slate-900 truncate cursor-pointer hover:text-emerald-600 transition-colors"
                        onClick={() => onView?.(document)}
                        title={document.filename}
                    >
                        {document.filename}
                    </h3>

                    {/* Status and Metadata */}
                    <div className="flex items-center gap-2 mt-1 flex-wrap">
                        <div className={`flex items-center gap-1 text-sm font-medium ${status.className}`}>
                            {status.icon}
                            <span>{status.text}</span>
                        </div>
                        {document.status === "processed" && (
                            <>
                                <span className="text-slate-300">•</span>
                                <span className="text-sm text-slate-600">
                                    {document.chunk_count} chunks
                                </span>
                            </>
                        )}
                        <span className="text-slate-300">•</span>
                        <span className="text-sm text-slate-600">{formattedSize}</span>
                    </div>

                    {/* Error Message */}
                    {document.status === "failed" && document.error_message && (
                        <p className="text-sm text-red-600 mt-1 line-clamp-1">
                            Error: {document.error_message}
                        </p>
                    )}

                    {/* Upload Date */}
                    <p className="text-xs text-slate-500 mt-1">
                        Uploaded {uploadDate}
                    </p>
                </div>

                {/* Actions Menu */}
                <div className="relative flex-shrink-0">
                    <button
                        onClick={() => setShowMenu(!showMenu)}
                        className="p-1 hover:bg-slate-100 rounded transition-colors"
                        aria-label="Document actions"
                    >
                        <MoreVertical size={18} className="text-slate-500" />
                    </button>

                    {showMenu && (
                        <>
                            {/* Backdrop to close menu */}
                            <div
                                className="fixed inset-0 z-10"
                                onClick={() => setShowMenu(false)}
                            />
                            {/* Menu */}
                            <div className="absolute right-0 mt-1 w-40 bg-white border border-slate-200 rounded-md shadow-lg z-20">
                                {onView && (
                                    <button
                                        onClick={() => {
                                            onView(document);
                                            setShowMenu(false);
                                        }}
                                        className="w-full text-left px-4 py-2 text-sm text-slate-700 hover:bg-slate-50 transition-colors"
                                    >
                                        View Details
                                    </button>
                                )}
                                {onReprocess && document.status !== "processing" && (
                                    <button
                                        onClick={() => {
                                            onReprocess(document);
                                            setShowMenu(false);
                                        }}
                                        className="w-full text-left px-4 py-2 text-sm text-slate-700 hover:bg-slate-50 transition-colors"
                                    >
                                        Reprocess
                                    </button>
                                )}
                                {onDelete && (
                                    <button
                                        onClick={() => {
                                            onDelete(document);
                                            setShowMenu(false);
                                        }}
                                        className="w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-red-50 transition-colors"
                                    >
                                        Delete
                                    </button>
                                )}
                            </div>
                        </>
                    )}
                </div>
            </div>
        </div>
    );
}
