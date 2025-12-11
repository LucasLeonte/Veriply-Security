import { Trash2, Loader2 } from "lucide-react";
import { useState } from "react";

interface DocumentDeleteButtonProps {
    documentId: string;
    documentName: string;
    documentStatus: string;
    isDeleting: boolean;
    onDeleteClick: (documentId: string, documentName: string) => void;
    size?: "sm" | "md" | "lg";
    variant?: "icon" | "text" | "full";
}

export function DocumentDeleteButton({
    documentId,
    documentName,
    documentStatus,
    isDeleting,
    onDeleteClick,
    size = "md",
    variant = "icon",
}: DocumentDeleteButtonProps) {
    const [showTooltip, setShowTooltip] = useState(false);

    // Cannot delete if processing or already deleting
    const isProcessing = documentStatus === "processing";
    const isDisabled = isProcessing || isDeleting;

    const tooltipText = isProcessing
        ? "Cannot delete while processing. Please wait."
        : isDeleting
        ? "Deleting..."
        : "Delete document";

    const handleClick = (e: React.MouseEvent) => {
        e.stopPropagation(); // Prevent row click if button is in a clickable row
        if (!isDisabled) {
            onDeleteClick(documentId, documentName);
        }
    };

    // Size classes
    const sizeClasses = {
        sm: "h-8 px-2 text-xs",
        md: "h-9 px-3 text-sm",
        lg: "h-10 px-4 text-base",
    };

    const iconSizeClasses = {
        sm: "h-3.5 w-3.5",
        md: "h-4 w-4",
        lg: "h-5 w-5",
    };

    // Variant rendering
    if (variant === "icon") {
        return (
            <div className="relative inline-block">
                <button
                    onClick={handleClick}
                    disabled={isDisabled}
                    onMouseEnter={() => setShowTooltip(true)}
                    onMouseLeave={() => setShowTooltip(false)}
                    className={`
                        rounded-lg p-2 transition
                        ${
                            isDisabled
                                ? "cursor-not-allowed opacity-50 text-slate-400"
                                : "text-slate-600 hover:bg-red-50 hover:text-red-600"
                        }
                    `}
                    aria-label={tooltipText}
                    title={tooltipText}
                >
                    {isDeleting ? (
                        <Loader2 className={`${iconSizeClasses[size]} animate-spin`} />
                    ) : (
                        <Trash2 className={iconSizeClasses[size]} />
                    )}
                </button>

                {/* Tooltip */}
                {showTooltip && (
                    <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-3 py-1.5 bg-slate-900 text-white text-xs rounded-lg whitespace-nowrap z-10 pointer-events-none">
                        {tooltipText}
                        <div className="absolute top-full left-1/2 -translate-x-1/2 -mt-1">
                            <div className="border-4 border-transparent border-t-slate-900"></div>
                        </div>
                    </div>
                )}
            </div>
        );
    }

    if (variant === "text") {
        return (
            <button
                onClick={handleClick}
                disabled={isDisabled}
                className={`
                    ${sizeClasses[size]}
                    rounded-lg font-medium transition
                    ${
                        isDisabled
                            ? "cursor-not-allowed opacity-50 text-slate-400"
                            : "text-red-600 hover:bg-red-50"
                    }
                `}
                title={tooltipText}
            >
                {isDeleting ? "Deleting..." : "Delete"}
            </button>
        );
    }

    // Full variant with icon and text
    return (
        <button
            onClick={handleClick}
            disabled={isDisabled}
            className={`
                ${sizeClasses[size]}
                flex items-center gap-2 rounded-lg font-medium transition
                ${
                    isDisabled
                        ? "cursor-not-allowed opacity-50 bg-slate-100 text-slate-400"
                        : "bg-red-600 text-white hover:bg-red-700"
                }
            `}
            title={tooltipText}
        >
            {isDeleting ? (
                <>
                    <Loader2 className={`${iconSizeClasses[size]} animate-spin`} />
                    Deleting...
                </>
            ) : (
                <>
                    <Trash2 className={iconSizeClasses[size]} />
                    Delete
                </>
            )}
        </button>
    );
}
