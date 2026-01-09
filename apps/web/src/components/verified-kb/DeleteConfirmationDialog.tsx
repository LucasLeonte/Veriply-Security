"use client";

import * as React from "react";
import { AlertTriangle } from "lucide-react";
import type { VerifiedQA } from "@/types/verified-qa";

interface DeleteConfirmationDialogProps {
    entry: VerifiedQA;
    onConfirm: () => Promise<void>;
    onCancel: () => void;
}

export function DeleteConfirmationDialog({
    entry,
    onConfirm,
    onCancel,
}: DeleteConfirmationDialogProps) {
    const [isDeleting, setIsDeleting] = React.useState(false);
    const [error, setError] = React.useState<string>("");

    const handleConfirm = async () => {
        setIsDeleting(true);
        setError("");

        try {
            await onConfirm();
        } catch (err) {
            setError(err instanceof Error ? err.message : "Failed to delete entry");
            setIsDeleting(false);
        }
    };

    return (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg shadow-lg max-w-md w-full mx-4">
                {/* Header */}
                <div className="p-6 border-b border-gray-200 flex items-start gap-4">
                    <div className="flex-shrink-0 flex items-center justify-center h-12 w-12 rounded-full bg-red-100">
                        <AlertTriangle className="text-red-600" size={24} />
                    </div>
                    <div>
                        <h2 className="text-lg font-bold text-gray-900">Delete Entry</h2>
                        <p className="text-sm text-gray-500 mt-1">
                            This action cannot be undone
                        </p>
                    </div>
                </div>

                {/* Body */}
                <div className="p-6 space-y-4">
                    {error && (
                        <div className="p-3 bg-red-100 border border-red-400 text-red-700 rounded">
                            {error}
                        </div>
                    )}

                    <div>
                        <p className="text-sm text-gray-600 mb-2">
                            Are you sure you want to delete this verified entry?
                        </p>
                        <p className="text-sm font-medium text-gray-900">
                            Question: {entry.question_text.substring(0, 100)}
                            {entry.question_text.length > 100 ? "..." : ""}
                        </p>
                    </div>

                    <div className="bg-yellow-50 p-4 rounded-lg">
                        <p className="text-sm text-yellow-800">
                            <strong>Note:</strong> This entry will be removed from verified search results and will no longer be available to users.
                        </p>
                    </div>
                </div>

                {/* Footer */}
                <div className="p-6 border-t border-gray-200 flex justify-end gap-3">
                    <button
                        onClick={onCancel}
                        disabled={isDeleting}
                        className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition disabled:opacity-50"
                    >
                        Cancel
                    </button>
                    <button
                        onClick={handleConfirm}
                        disabled={isDeleting}
                        className="px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 transition disabled:bg-gray-400"
                    >
                        {isDeleting ? "Deleting..." : "Delete Entry"}
                    </button>
                </div>
            </div>
        </div>
    );
}

