import { Trash2, CheckSquare, Square } from "lucide-react";

interface BulkDeleteToolbarProps {
    selectedCount: number;
    totalCount: number;
    allSelected: boolean;
    onSelectAll: () => void;
    onBulkDelete: () => void;
    disabled?: boolean;
}

export function BulkDeleteToolbar({
    selectedCount,
    totalCount,
    allSelected,
    onSelectAll,
    onBulkDelete,
    disabled = false,
}: BulkDeleteToolbarProps) {
    // Don't show toolbar if no documents
    if (totalCount === 0) {
        return null;
    }

    const isSelectionMode = selectedCount > 0;
    const exceeds100Limit = selectedCount > 100;

    return (
        <div className="bg-white border-b border-slate-200 sticky top-0 z-10">
            <div className="px-6 py-3 flex items-center justify-between gap-4">
                {/* Left side: Select all checkbox */}
                <div className="flex items-center gap-3">
                    <button
                        onClick={onSelectAll}
                        disabled={disabled}
                        className={`
                            flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition
                            ${
                                disabled
                                    ? "cursor-not-allowed opacity-50"
                                    : "hover:bg-slate-100 text-slate-700"
                            }
                        `}
                        aria-label={allSelected ? "Deselect all documents" : "Select all documents"}
                    >
                        {allSelected ? (
                            <CheckSquare className="h-4 w-4 text-blue-600" />
                        ) : (
                            <Square className="h-4 w-4" />
                        )}
                        <span>
                            {allSelected ? "Deselect All" : "Select All"}
                        </span>
                    </button>

                    {/* Selected count indicator */}
                    {isSelectionMode && (
                        <div className="flex items-center gap-2">
                            <div className="h-5 w-px bg-slate-300" />
                            <span className="text-sm text-slate-600">
                                <span className="font-semibold text-slate-900">{selectedCount}</span>
                                {" "}
                                of {totalCount} selected
                            </span>
                        </div>
                    )}
                </div>

                {/* Right side: Bulk actions */}
                {isSelectionMode && (
                    <div className="flex items-center gap-3">
                        {/* Warning if exceeds 100 */}
                        {exceeds100Limit && (
                            <div className="text-sm text-red-600 font-medium">
                                Maximum 100 documents can be deleted at once
                            </div>
                        )}

                        {/* Bulk delete button */}
                        <button
                            onClick={onBulkDelete}
                            disabled={disabled || exceeds100Limit}
                            className={`
                                flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition
                                ${
                                    disabled || exceeds100Limit
                                        ? "cursor-not-allowed opacity-50 bg-red-100 text-red-400"
                                        : "bg-red-600 text-white hover:bg-red-700"
                                }
                            `}
                            aria-label={`Delete ${selectedCount} selected document${selectedCount !== 1 ? "s" : ""}`}
                        >
                            <Trash2 className="h-4 w-4" />
                            <span>
                                Delete {selectedCount} Document{selectedCount !== 1 ? "s" : ""}
                            </span>
                        </button>
                    </div>
                )}
            </div>

            {/* Warning banner when in selection mode */}
            {isSelectionMode && !exceeds100Limit && (
                <div className="px-6 py-2 bg-yellow-50 border-t border-yellow-100">
                    <div className="flex items-start gap-2 text-sm text-yellow-800">
                        <svg
                            className="h-5 w-5 flex-shrink-0 mt-0.5"
                            fill="none"
                            viewBox="0 0 24 24"
                            stroke="currentColor"
                        >
                            <path
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                strokeWidth={2}
                                d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                            />
                        </svg>
                        <span>
                            Bulk deletion is irreversible and will permanently remove the selected documents from your knowledge base.
                        </span>
                    </div>
                </div>
            )}

            {/* Error banner when exceeds 100 */}
            {exceeds100Limit && (
                <div className="px-6 py-2 bg-red-50 border-t border-red-100">
                    <div className="flex items-start gap-2 text-sm text-red-800">
                        <svg
                            className="h-5 w-5 flex-shrink-0 mt-0.5"
                            fill="none"
                            viewBox="0 0 24 24"
                            stroke="currentColor"
                        >
                            <path
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                strokeWidth={2}
                                d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                            />
                        </svg>
                        <span>
                            You have selected <strong>{selectedCount}</strong> documents. 
                            Please reduce your selection to 100 or fewer documents to proceed with bulk deletion.
                        </span>
                    </div>
                </div>
            )}
        </div>
    );
}
