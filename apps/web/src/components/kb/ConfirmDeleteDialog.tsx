"use client";

import React, { useEffect, useRef } from "react";
import { AlertCircle } from "lucide-react";

interface ConfirmDeleteDialogProps {
    isOpen: boolean;
    onClose: () => void;
    onConfirm: () => void;
    documentName?: string;
    isDeleting?: boolean;
    title?: string;
    description?: string;
}

export function ConfirmDeleteDialog({
    isOpen,
    onClose,
    onConfirm,
    documentName,
    isDeleting = false,
    title = "Delete Document",
    description,
}: ConfirmDeleteDialogProps) {
    const dialogRef = useRef<HTMLDivElement>(null);
    const cancelButtonRef = useRef<HTMLButtonElement>(null);

    // Focus management and escape key handler
    useEffect(() => {
        if (isOpen) {
            const previousFocus = document.activeElement as HTMLElement;

            // Focus cancel button (safer default)
            cancelButtonRef.current?.focus();

            // Escape key handler
            const handleEscape = (e: KeyboardEvent) => {
                if (e.key === "Escape" && !isDeleting) {
                    onClose();
                }
            };

            document.addEventListener("keydown", handleEscape);

            return () => {
                document.removeEventListener("keydown", handleEscape);
                previousFocus?.focus();
            };
        }
    }, [isOpen, isDeleting, onClose]);

    if (!isOpen) return null;

    return (
        <div
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/40"
            onClick={(e) => {
                if (e.target === e.currentTarget && !isDeleting) {
                    onClose();
                }
            }}
        >
            <div
                ref={dialogRef}
                role="dialog"
                aria-modal="true"
                aria-labelledby="delete-dialog-title"
                aria-describedby="delete-dialog-description"
                className="bg-white rounded-lg shadow-lg w-full max-w-md mx-4"
            >
                {/* Header */}
                <div className="p-6">
                    <div className="flex items-start gap-4">
                        <div className="flex-shrink-0 w-10 h-10 rounded-full bg-red-100 flex items-center justify-center">
                            <AlertCircle size={20} className="text-red-600" aria-hidden="true" />
                        </div>
                        <div className="flex-1">
                            <h2 id="delete-dialog-title" className="text-lg font-semibold text-slate-900">
                                {title}
                            </h2>
                            <p id="delete-dialog-description" className="text-sm text-slate-600 mt-2">
                                {description || (
                                    <>
                                        Are you sure you want to delete{" "}
                                        <span className="font-medium text-slate-900">
                                            {documentName}
                                        </span>
                                        ? This action cannot be undone.
                                    </>
                                )}
                            </p>
                            {!description && (
                                <p className="text-sm text-slate-600 mt-2">
                                    All associated chunks and embeddings will be permanently removed.
                                </p>
                            )}
                        </div>
                    </div>
                </div>

                {/* Footer */}
                <div className="flex items-center justify-end gap-3 px-6 py-4 bg-slate-50 rounded-b-lg">
                    <button
                        ref={cancelButtonRef}
                        onClick={onClose}
                        disabled={isDeleting}
                        className="px-4 py-2 text-sm font-medium text-slate-700 bg-white border border-slate-300 rounded-md hover:bg-slate-50 focus:outline-none focus:ring-2 focus:ring-emerald-500 transition-colors disabled:opacity-50"
                        aria-label="Cancel delete"
                    >
                        Cancel
                    </button>
                    <button
                        onClick={onConfirm}
                        disabled={isDeleting}
                        className="px-4 py-2 text-sm font-medium text-white bg-red-600 rounded-md hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                        aria-label={`Delete ${documentName}`}
                    >
                        {isDeleting ? "Deleting..." : title}
                    </button>
                </div>
            </div>
        </div>
    );
}
