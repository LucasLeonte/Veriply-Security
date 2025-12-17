"use client";

import React from "react";
import { AlertCircle, X } from "lucide-react";

interface ReprocessModalProps {
    isOpen: boolean;
    onClose: () => void;
    onConfirm: () => void;
    documentName?: string;
}

export function ReprocessModal({
    isOpen,
    onClose,
    onConfirm,
    documentName,
}: ReprocessModalProps) {
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
                {/* Header */}
                <div className="flex items-start justify-between mb-4">
                    <div className="flex items-center gap-3">
                        <div className="flex-shrink-0 w-10 h-10 rounded-full bg-amber-100 flex items-center justify-center">
                            <AlertCircle size={20} className="text-amber-600" />
                        </div>
                        <h3 className="text-lg font-semibold text-slate-900">
                            Reprocess Document
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

                {/* Content */}
                <div className="mb-6">
                    <p className="text-sm text-slate-700 mb-3">
                        Reprocess document{" "}
                        <span className="font-medium text-slate-900">
                            "{documentName || "this document"}"
                        </span>
                        ?
                    </p>
                    <p className="text-sm text-slate-600">
                        This will replace all chunks and embeddings with fresh
                        data. The document will be re-extracted, re-chunked, and
                        re-embedded using the current processing configuration.
                    </p>
                </div>

                {/* Warning */}
                <div className="mb-6 p-3 bg-amber-50 border border-amber-200 rounded-lg">
                    <p className="text-xs text-amber-800">
                        <strong>Note:</strong> The document status will change
                        to "Processing" and existing chunks will be replaced
                        once reprocessing completes.
                    </p>
                </div>

                {/* Actions */}
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
                        Reprocess
                    </button>
                </div>
            </div>
        </div>
    );
}
