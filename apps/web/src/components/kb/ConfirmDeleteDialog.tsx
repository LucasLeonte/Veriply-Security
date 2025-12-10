"use client";

import React from "react";
import { AlertCircle } from "lucide-react";

interface ConfirmDeleteDialogProps {
    isOpen: boolean;
    onClose: () => void;
    onConfirm: () => void;
    documentName: string;
    isDeleting?: boolean;
}

export function ConfirmDeleteDialog({
    isOpen,
    onClose,
    onConfirm,
    documentName,
    isDeleting = false,
}: ConfirmDeleteDialogProps) {
    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
            <div className="bg-white rounded-lg shadow-lg w-full max-w-md mx-4">
                {/* Header */}
                <div className="p-6">
                    <div className="flex items-start gap-4">
                        <div className="flex-shrink-0 w-10 h-10 rounded-full bg-red-100 flex items-center justify-center">
                            <AlertCircle size={20} className="text-red-600" />
                        </div>
                        <div className="flex-1">
                            <h2 className="text-lg font-semibold text-slate-900">
                                Delete Document
                            </h2>
                            <p className="text-sm text-slate-600 mt-2">
                                Are you sure you want to delete{" "}
                                <span className="font-medium text-slate-900">
                                    {documentName}
                                </span>
                                ? This action cannot be undone.
                            </p>
                            <p className="text-sm text-slate-600 mt-2">
                                All associated chunks and embeddings will be permanently removed.
                            </p>
                        </div>
                    </div>
                </div>

                {/* Footer */}
                <div className="flex items-center justify-end gap-3 px-6 py-4 bg-slate-50 rounded-b-lg">
                    <button
                        onClick={onClose}
                        disabled={isDeleting}
                        className="px-4 py-2 text-sm font-medium text-slate-700 bg-white border border-slate-300 rounded-md hover:bg-slate-50 transition-colors disabled:opacity-50"
                    >
                        Cancel
                    </button>
                    <button
                        onClick={onConfirm}
                        disabled={isDeleting}
                        className="px-4 py-2 text-sm font-medium text-white bg-red-600 rounded-md hover:bg-red-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        {isDeleting ? "Deleting..." : "Delete Document"}
                    </button>
                </div>
            </div>
        </div>
    );
}
