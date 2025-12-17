"use client";

import React, { useState } from "react";
import { X, AlertCircle, Folder, Loader } from "lucide-react";
import type { Folder as FolderType } from "@/types/folder";

interface MoveToFolderModalProps {
    isOpen: boolean;
    onClose: () => void;
    onMove: (folderId: string | null) => Promise<void>;
    folders?: FolderType[];
    documentName?: string;
    currentFolderId?: string | null;
}

export function MoveToFolderModal({
    isOpen,
    onClose,
    onMove,
    folders = [],
    documentName = "Document",
    currentFolderId,
}: MoveToFolderModalProps) {
    const [selectedFolderId, setSelectedFolderId] = useState<string | null>(
        currentFolderId || null
    );
    const [isMoving, setIsMoving] = useState(false);
    const [error, setError] = useState<string>("");

    const handleMove = async () => {
        setError("");
        setIsMoving(true);

        try {
            await onMove(selectedFolderId);
            onClose();
        } catch (err) {
            setError(
                err instanceof Error ? err.message : "Failed to move document"
            );
        } finally {
            setIsMoving(false);
        }
    };

    const handleClose = () => {
        if (!isMoving) {
            setSelectedFolderId(currentFolderId || null);
            setError("");
            onClose();
        }
    };

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
            <div className="bg-white rounded-lg shadow-lg w-full max-w-sm mx-4">
                {/* Header */}
                <div className="flex items-center justify-between p-6 border-b border-slate-200">
                    <div>
                        <h2 className="text-lg font-semibold text-slate-900">
                            Move to Folder
                        </h2>
                        <p className="text-sm text-slate-600 mt-1">
                            {documentName}
                        </p>
                    </div>
                    <button
                        onClick={handleClose}
                        disabled={isMoving}
                        className="p-2 min-w-[44px] min-h-[44px] flex items-center justify-center text-slate-400 hover:text-slate-600 focus:outline-none focus:ring-2 focus:ring-emerald-500 rounded transition-colors disabled:opacity-50"
                        aria-label="Close dialog"
                    >
                        <X size={20} aria-hidden="true" />
                    </button>
                </div>

                {/* Content */}
                <div className="p-6 space-y-4">
                    {/* Folder Selection */}
                    <div>
                        <label
                            htmlFor="move-folder-select"
                            className="text-sm font-medium text-slate-700 block mb-3"
                        >
                            <Folder size={16} className="inline mr-2" />
                            Select destination
                        </label>
                        <div className="space-y-2 max-h-60 overflow-y-auto border border-slate-200 rounded-lg p-3 bg-slate-50">
                            {/* No folder option */}
                            <button
                                onClick={() => setSelectedFolderId(null)}
                                disabled={isMoving}
                                className={`w-full text-left px-3 py-2 rounded transition-colors text-sm ${
                                    selectedFolderId === null
                                        ? "bg-emerald-100 text-emerald-700 border border-emerald-300"
                                        : "bg-white border border-slate-200 text-slate-700 hover:bg-slate-50"
                                } disabled:opacity-50`}
                            >
                                📄 All Documents (no folder)
                            </button>

                            {/* Folder options */}
                            {folders.map((folder) => (
                                <button
                                    key={folder.id}
                                    onClick={() =>
                                        setSelectedFolderId(folder.id)
                                    }
                                    disabled={isMoving}
                                    className={`w-full text-left px-3 py-2 rounded transition-colors text-sm ${
                                        selectedFolderId === folder.id
                                            ? "bg-emerald-100 text-emerald-700 border border-emerald-300"
                                            : "bg-white border border-slate-200 text-slate-700 hover:bg-slate-50"
                                    } disabled:opacity-50`}
                                >
                                    📁 {folder.name}
                                </button>
                            ))}

                            {folders.length === 0 && (
                                <div className="text-sm text-slate-500 text-center py-4">
                                    No folders available
                                </div>
                            )}
                        </div>
                    </div>

                    {/* Error Message */}
                    {error && (
                        <div className="flex items-start gap-2 p-3 bg-red-50 border border-red-200 rounded-md">
                            <AlertCircle
                                size={16}
                                className="text-red-600 flex-shrink-0 mt-0.5"
                            />
                            <p className="text-sm text-red-600">{error}</p>
                        </div>
                    )}
                </div>

                {/* Footer */}
                <div className="flex items-center justify-end gap-3 p-6 border-t border-slate-200">
                    <button
                        onClick={handleClose}
                        disabled={isMoving}
                        className="px-4 py-2 text-sm font-medium text-slate-700 bg-white border border-slate-300 rounded-md hover:bg-slate-50 transition-colors disabled:opacity-50"
                    >
                        Cancel
                    </button>
                    <button
                        onClick={handleMove}
                        disabled={isMoving}
                        className="px-4 py-2 text-sm font-medium text-white bg-emerald-600 rounded-md hover:bg-emerald-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                    >
                        {isMoving && (
                            <Loader size={16} className="animate-spin" />
                        )}
                        {isMoving ? "Moving..." : "Move"}
                    </button>
                </div>
            </div>
        </div>
    );
}
