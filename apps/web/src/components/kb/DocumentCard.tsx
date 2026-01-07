"use client";

import React from "react";
import { Document } from "@/types/document";
import {
    FileText,
    MoreVertical,
    CheckCircle,
    AlertCircle,
    Clock,
    Loader,
    User,
    Bot,
    CheckSquare,
    Square,
} from "lucide-react";

interface DocumentCardProps {
    document: Document;
    onView?: (document: Document) => void;
    onDelete?: (document: Document) => void;
    onReprocess?: (document: Document) => void;
    onMove?: (document: Document) => void;
    isSelected?: boolean;
    onToggleSelection?: (documentId: string) => void;
    isDeleting?: boolean;
    folderName?: string;
}

export function DocumentCard({
    document,
    onView,
    onDelete,
    onReprocess,
    onMove,
    isSelected = false,
    onToggleSelection,
    isDeleting = false,
    folderName,
}: DocumentCardProps) {
    const [showMenu, setShowMenu] = React.useState(false);

    const getStatusDisplay = () => {
        // Show deleting status if currently being deleted
        if (isDeleting) {
            return {
                icon: (
                    <Loader
                        size={16}
                        className="text-red-500 animate-spin"
                        aria-hidden="true"
                    />
                ),
                text: "Deleting...",
                className: "text-red-500",
            };
        }

        switch (document.status) {
            case "ready":
            case "processed": // Legacy status - treat as ready
                return {
                    icon: (
                        <CheckCircle
                            size={16}
                            className="text-emerald-600"
                            aria-hidden="true"
                        />
                    ),
                    text: "Ready",
                    className: "text-emerald-600",
                };
            case "uploaded":
                return {
                    icon: (
                        <Clock
                            size={16}
                            className="text-slate-400"
                            aria-hidden="true"
                        />
                    ),
                    text: "Uploaded",
                    className: "text-slate-400",
                };
            case "processing":
                return {
                    icon: (
                        <Loader
                            size={16}
                            className="text-amber-500 animate-spin"
                            aria-hidden="true"
                        />
                    ),
                    text: `Processing${
                        document.processing_progress
                            ? ` ${document.processing_progress}%`
                            : "..."
                    }`,
                    className: "text-amber-500",
                };
            case "failed":
            case "error": // Legacy status - treat as failed
                return {
                    icon: (
                        <AlertCircle
                            size={16}
                            className="text-red-600"
                            aria-hidden="true"
                        />
                    ),
                    text: "Failed",
                    className: "text-red-600",
                };
            case "uploading":
                return {
                    icon: (
                        <Loader
                            size={16}
                            className="text-slate-400 animate-spin"
                            aria-hidden="true"
                        />
                    ),
                    text: "Uploading...",
                    className: "text-slate-400",
                };
            default:
                return {
                    icon: (
                        <Clock
                            size={16}
                            className="text-slate-400"
                            aria-hidden="true"
                        />
                    ),
                    text: document.status,
                    className: "text-slate-400",
                };
        }
    };

    const status = getStatusDisplay();
    const formattedSize =
        typeof document.size === "number" && isFinite(document.size)
            ? (document.size / 1024).toFixed(1) + " KB"
            : "—";
    const uploadDate = new Date(document.created_at).toLocaleDateString(
        "en-US",
        {
            month: "short",
            day: "numeric",
            year: "numeric",
        }
    );

    return (
        <div
            className={`border border-slate-200 rounded-lg p-4 transition-all bg-white ${
                isSelected
                    ? "ring-2 ring-blue-500 shadow-md"
                    : "hover:shadow-md"
            } ${isDeleting ? "opacity-60" : ""}`}
        >
            <div className="flex items-start gap-3">
                {/* Selection Checkbox */}
                {onToggleSelection && (
                    <button
                        onClick={() => onToggleSelection(document.id)}
                        disabled={
                            isDeleting || document.status === "processing"
                        }
                        className="flex-shrink-0 mt-1 p-1 rounded hover:bg-slate-100 disabled:cursor-not-allowed disabled:opacity-50"
                        aria-label={
                            isSelected ? "Deselect document" : "Select document"
                        }
                    >
                        {isSelected ? (
                            <CheckSquare className="h-5 w-5 text-blue-600" />
                        ) : (
                            <Square className="h-5 w-5 text-slate-400" />
                        )}
                    </button>
                )}

                {/* File Icon */}
                <FileText
                    size={24}
                    className="text-slate-400 flex-shrink-0 mt-1"
                    aria-hidden="true"
                />

                {/* Content */}
                <div className="flex-1 min-w-0">
                    {/* File Name */}
                    <button
                        onClick={() => onView?.(document)}
                        disabled={!onView}
                        className="font-medium text-slate-900 truncate text-left w-full hover:text-emerald-600 focus:outline-none focus:text-emerald-600 transition-colors disabled:cursor-default"
                        title={document.filename}
                        aria-label={`View details for ${document.filename}`}
                    >
                        {document.filename}
                    </button>

                    {/* Folder Tag */}
                    {folderName && (
                        <div className="mt-1">
                            <span className="inline-flex items-center gap-1 px-2 py-1 text-xs font-medium bg-blue-100 text-blue-700 rounded-full">
                                📁 {folderName}
                            </span>
                        </div>
                    )}

                    {/* Status and Metadata */}
                    <div className="flex items-center gap-2 mt-1 flex-wrap">
                        <div
                            className={`flex items-center gap-1 text-sm font-medium ${status.className}`}
                        >
                            {status.icon}
                            <span>{status.text}</span>
                        </div>
                        {(document.status === "ready" || document.status === "processed") && (
                            <>
                                <span className="text-slate-300">•</span>
                                <span className="text-sm text-slate-600">
                                    {document.chunk_count} chunks
                                </span>
                            </>
                        )}
                        <span className="text-slate-300">•</span>
                        <span className="text-sm text-slate-600">
                            {formattedSize}
                        </span>
                    </div>

                    {/* Error Message */}
                    {(document.status === "failed" || document.status === "error") && document.error_message && (
                        <p className="text-sm text-red-600 mt-1 line-clamp-1">
                            Error: {document.error_message}
                        </p>
                    )}

                    {/* Provenance Information */}
                    <div className="flex items-center gap-2 mt-2 text-xs text-slate-500">
                        {document.uploader_id && (
                            <div className="flex items-center gap-1">
                                <User size={12} />
                                <span>
                                    Uploaded by User {document.uploader_id}
                                </span>
                            </div>
                        )}
                        {document.bot_id && (
                            <>
                                {document.uploader_id && (
                                    <span className="text-slate-300">•</span>
                                )}
                                <div className="flex items-center gap-1">
                                    <Bot size={12} />
                                    <span>Triggered by Bot</span>
                                </div>
                            </>
                        )}
                    </div>

                    {/* Upload Date */}
                    <p className="text-xs text-slate-500 mt-1">
                        Uploaded {uploadDate}
                    </p>
                </div>

                {/* Actions Menu */}
                <div className="relative flex-shrink-0">
                    <button
                        onClick={() => setShowMenu(!showMenu)}
                        disabled={isDeleting}
                        className="p-2 min-w-[44px] min-h-[44px] flex items-center justify-center hover:bg-slate-100 rounded focus:outline-none focus:ring-2 focus:ring-emerald-500 transition-colors disabled:cursor-not-allowed disabled:opacity-50"
                        aria-label={`Actions for ${document.filename}`}
                        aria-expanded={showMenu}
                        aria-haspopup="true"
                    >
                        <MoreVertical
                            size={18}
                            className="text-slate-500"
                            aria-hidden="true"
                        />
                    </button>

                    {showMenu && (
                        <>
                            {/* Backdrop to close menu */}
                            <div
                                className="fixed inset-0 z-10"
                                onClick={() => setShowMenu(false)}
                                aria-hidden="true"
                            />
                            {/* Menu */}
                            <div
                                className="absolute right-0 mt-1 w-40 bg-white border border-slate-200 rounded-md shadow-lg z-20"
                                role="menu"
                                aria-label="Document actions menu"
                            >
                                {onView && (
                                    <button
                                        onClick={() => {
                                            onView(document);
                                            setShowMenu(false);
                                        }}
                                        className="w-full text-left px-4 py-2 text-sm text-slate-700 hover:bg-slate-50 focus:outline-none focus:bg-slate-50 transition-colors"
                                        role="menuitem"
                                    >
                                        View Details
                                    </button>
                                )}
                                {onReprocess && (
                                    <button
                                        onClick={() => {
                                            if (
                                                document.status ===
                                                    "processing" ||
                                                isDeleting
                                            ) {
                                                return;
                                            }
                                            onReprocess(document);
                                            setShowMenu(false);
                                        }}
                                        disabled={
                                            document.status === "processing" ||
                                            isDeleting
                                        }
                                        title={
                                            document.status === "processing"
                                                ? "Cannot reprocess while processing"
                                                : isDeleting
                                                ? "Cannot reprocess while deleting"
                                                : undefined
                                        }
                                        className="w-full text-left px-4 py-2 text-sm text-slate-700 hover:bg-slate-50 focus:outline-none focus:bg-slate-50 transition-colors disabled:cursor-not-allowed disabled:opacity-60"
                                        role="menuitem"
                                    >
                                        Reprocess
                                    </button>
                                )}
                                {onMove && (
                                    <button
                                        onClick={() => {
                                            onMove(document);
                                            setShowMenu(false);
                                        }}
                                        className="w-full text-left px-4 py-2 text-sm text-slate-700 hover:bg-slate-50 focus:outline-none focus:bg-slate-50 transition-colors"
                                        role="menuitem"
                                    >
                                        Move to Folder
                                    </button>
                                )}
                                {onDelete && (
                                    <button
                                        onClick={() => {
                                            onDelete(document);
                                            setShowMenu(false);
                                        }}
                                        disabled={
                                            document.status === "processing" ||
                                            isDeleting
                                        }
                                        className="w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-red-50 focus:outline-none focus:bg-red-50 transition-colors disabled:cursor-not-allowed disabled:opacity-50"
                                        role="menuitem"
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
