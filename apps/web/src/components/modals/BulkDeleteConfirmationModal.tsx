import { Trash2, X, AlertTriangle } from "lucide-react";

interface BulkDeleteConfirmationModalProps {
    isOpen: boolean;
    onClose: () => void;
    onConfirm: () => void;
    selectedCount: number;
    selectedDocuments: Array<{ id: string; name: string }>;
    isDeleting: boolean;
}

export function BulkDeleteConfirmationModal({
    isOpen,
    onClose,
    onConfirm,
    selectedCount,
    selectedDocuments,
    isDeleting,
}: BulkDeleteConfirmationModalProps) {
    if (!isOpen) return null;

    const handleBackdropClick = (e: React.MouseEvent<HTMLDivElement>) => {
        if (e.target === e.currentTarget && !isDeleting) {
            onClose();
        }
    };

    const displayLimit = 5;
    const showDocuments = selectedDocuments.slice(0, displayLimit);
    const remainingCount = selectedCount - displayLimit;

    return (
        <div
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4"
            onClick={handleBackdropClick}
        >
            <div className="relative w-full max-w-lg rounded-lg bg-white shadow-xl max-h-[90vh] flex flex-col">
                {/* Header */}
                <div className="flex items-center justify-between border-b border-slate-200 px-6 py-4">
                    <div className="flex items-center gap-3">
                        <div className="flex h-10 w-10 items-center justify-center rounded-full bg-red-100">
                            <Trash2 className="h-5 w-5 text-red-600" />
                        </div>
                        <h2 className="text-lg font-semibold text-slate-900">
                            Delete {selectedCount} Document{selectedCount !== 1 ? "s" : ""}
                        </h2>
                    </div>
                    <button
                        onClick={onClose}
                        disabled={isDeleting}
                        className="rounded-lg p-2 text-slate-400 transition hover:bg-slate-100 hover:text-slate-600 disabled:cursor-not-allowed disabled:opacity-50"
                        aria-label="Close"
                    >
                        <X className="h-5 w-5" />
                    </button>
                </div>

                {/* Content */}
                <div className="flex-1 overflow-y-auto px-6 py-6">
                    <p className="text-sm text-slate-600">
                        Delete{" "}
                        <span className="font-semibold text-slate-900">
                            {selectedCount} document{selectedCount !== 1 ? "s" : ""}
                        </span>
                        ? This will remove all chunks and embeddings.
                    </p>

                    {/* Warning */}
                    <div className="mt-4 rounded-lg bg-yellow-50 border border-yellow-200 p-3">
                        <div className="flex items-start gap-2">
                            <AlertTriangle className="h-5 w-5 text-yellow-600 flex-shrink-0 mt-0.5" />
                            <div>
                                <p className="text-sm font-medium text-yellow-900">
                                    Warning: This action cannot be undone
                                </p>
                                <p className="mt-1 text-xs text-yellow-800">
                                    All selected documents and their processed data will be
                                    permanently deleted.
                                </p>
                            </div>
                        </div>
                    </div>

                    {/* Document List */}
                    <div className="mt-4">
                        <p className="text-xs font-medium text-slate-700 mb-2">
                            Selected documents:
                        </p>
                        <div className="rounded-lg border border-slate-200 bg-slate-50 p-3 max-h-48 overflow-y-auto">
                            <ul className="space-y-2">
                                {showDocuments.map((doc) => (
                                    <li
                                        key={doc.id}
                                        className="flex items-center gap-2 text-sm text-slate-700"
                                    >
                                        <div className="h-1.5 w-1.5 rounded-full bg-slate-400" />
                                        <span className="truncate">{doc.name}</span>
                                    </li>
                                ))}
                                {remainingCount > 0 && (
                                    <li className="text-sm text-slate-500 italic">
                                        ... and {remainingCount} more
                                    </li>
                                )}
                            </ul>
                        </div>
                    </div>

                    {/* Max limit warning if needed */}
                    {selectedCount > 100 && (
                        <div className="mt-4 rounded-lg bg-red-50 border border-red-200 p-3">
                            <div className="flex items-start gap-2">
                                <X className="h-5 w-5 text-red-600 flex-shrink-0 mt-0.5" />
                                <div>
                                    <p className="text-sm font-medium text-red-900">
                                        Too many documents selected
                                    </p>
                                    <p className="mt-1 text-xs text-red-800">
                                        Maximum 100 documents can be deleted at once. You have
                                        selected {selectedCount} documents. Please deselect{" "}
                                        {selectedCount - 100} document(s).
                                    </p>
                                </div>
                            </div>
                        </div>
                    )}
                </div>

                {/* Footer */}
                <div className="flex items-center justify-end gap-3 border-t border-slate-200 px-6 py-4">
                    <button
                        onClick={onClose}
                        disabled={isDeleting}
                        className="rounded-lg border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-50"
                    >
                        Cancel
                    </button>
                    <button
                        onClick={onConfirm}
                        disabled={isDeleting || selectedCount > 100}
                        className="flex items-center gap-2 rounded-lg bg-red-600 px-4 py-2 text-sm font-medium text-white transition hover:bg-red-700 disabled:cursor-not-allowed disabled:opacity-50"
                    >
                        {isDeleting ? (
                            <>
                                <svg
                                    className="h-4 w-4 animate-spin"
                                    xmlns="http://www.w3.org/2000/svg"
                                    fill="none"
                                    viewBox="0 0 24 24"
                                >
                                    <circle
                                        className="opacity-25"
                                        cx="12"
                                        cy="12"
                                        r="10"
                                        stroke="currentColor"
                                        strokeWidth="4"
                                    ></circle>
                                    <path
                                        className="opacity-75"
                                        fill="currentColor"
                                        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                                    ></path>
                                </svg>
                                Deleting {selectedCount} document
                                {selectedCount !== 1 ? "s" : ""}...
                            </>
                        ) : (
                            <>
                                <Trash2 className="h-4 w-4" />
                                Delete {selectedCount} Document
                                {selectedCount !== 1 ? "s" : ""}
                            </>
                        )}
                    </button>
                </div>
            </div>
        </div>
    );
}
