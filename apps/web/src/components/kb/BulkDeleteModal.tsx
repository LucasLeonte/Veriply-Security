"use client";

import React from "react";
import { AlertTriangle, X } from "lucide-react";

interface BulkDeleteModalProps {
    isOpen: boolean;
    count: number;
    onClose: () => void;
    onConfirm: () => void;
}

export function BulkDeleteModal({
    isOpen,
    count,
    onClose,
    onConfirm,
}: BulkDeleteModalProps) {
    if (!isOpen) return null;

    return (
        <div
            className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4"
            onClick={onClose}
        >
            <div
                className="bg-white rounded-lg shadow-xl max-w-md w-full p-6"
                onClick={(e) => e.stopPropagation()}
            >
                <div className="flex items-start justify-between mb-4">
                    <div className="flex items-center gap-3">
                        <div className="flex-shrink-0 w-10 h-10 rounded-full bg-red-100 flex items-center justify-center">
                            <AlertTriangle size={20} className="text-red-600" />
                        </div>
                        <h3 className="text-lg font-semibold text-slate-900">
                            Delete {count} document{count === 1 ? "" : "s"}?
                        </h3>
                    </div>
                    <button
                        onClick={onClose}
                        className="text-slate-400 hover:text-slate-600 transition-colors"
                        aria-label="Close"
                    >
                        <X size={20} />
                    </button>
                </div>

                <div className="mb-6 space-y-2">
                    <p className="text-sm text-slate-700">
                        This action will permanently delete the selected
                        documents and their associated chunks and embeddings.
                    </p>
                    <p className="text-sm text-slate-600">
                        This cannot be undone. The documents will be removed
                        from your knowledge base immediately.
                    </p>
                </div>

                <div className="mb-6 p-3 bg-red-50 border border-red-200 rounded-lg">
                    <p className="text-xs text-red-800">
                        <strong>Warning:</strong> You are about to delete{" "}
                        {count} document{count === 1 ? "" : "s"}. Please make
                        sure this is intentional.
                    </p>
                </div>

                <div className="flex items-center justify-end gap-3">
                    <button
                        onClick={onClose}
                        className="px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-100 rounded-md transition-colors"
                    >
                        Cancel
                    </button>
                    <button
                        onClick={onConfirm}
                        className="px-4 py-2 text-sm font-medium text-white bg-red-600 hover:bg-red-700 rounded-md transition-colors"
                    >
                        Delete {count} Document{count === 1 ? "" : "s"}
                    </button>
                </div>
            </div>
        </div>
    );
}
