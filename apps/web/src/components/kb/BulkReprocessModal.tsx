"use client";

import React from "react";
import { AlertTriangle, X } from "lucide-react";

interface BulkReprocessModalProps {
    isOpen: boolean;
    count: number;
    onClose: () => void;
    onConfirm: () => void;
}

export function BulkReprocessModal({
    isOpen,
    count,
    onClose,
    onConfirm,
}: BulkReprocessModalProps) {
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
                        <div className="flex-shrink-0 w-10 h-10 rounded-full bg-amber-100 flex items-center justify-center">
                            <AlertTriangle
                                size={20}
                                className="text-amber-600"
                            />
                        </div>
                        <h3 className="text-lg font-semibold text-slate-900">
                            Reprocess {count} document{count === 1 ? "" : "s"}?
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
                        This will replace all chunks and embeddings with fresh
                        data for the selected documents.
                    </p>
                    <p className="text-sm text-slate-600">
                        Documents will move to "Processing" and may finish at
                        different times. Maximum 100 documents per bulk
                        reprocess.
                    </p>
                </div>

                <div className="mb-6 p-3 bg-amber-50 border border-amber-200 rounded-lg">
                    <p className="text-xs text-amber-800">
                        Ensure documents are not currently processing or
                        deleting. Reprocessing cannot start for those states.
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
                        className="px-4 py-2 text-sm font-medium text-white bg-amber-600 hover:bg-amber-700 rounded-md transition-colors"
                    >
                        Reprocess {count} Document{count === 1 ? "" : "s"}
                    </button>
                </div>
            </div>
        </div>
    );
}
