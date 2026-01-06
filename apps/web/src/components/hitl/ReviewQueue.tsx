import React, { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import {
    Clock,
    MessageCircle,
    Mail,
    CheckCircle,
    XCircle,
    Edit2,
    Copy,
    Eye,
    Filter as FilterIcon,
    Loader2,
} from "lucide-react";
import { ReviewQueueItem } from "@/hooks/useHITLQueue";
import { Button } from "@/components/ui/button";
import { useToast } from "@/components/ui/toast";
import { cn } from "@/lib/utils";
import { useKeyboardShortcuts } from "@/hooks/useKeyboardShortcuts";
import { ShortcutHelpModal } from "./ShortcutHelpModal";
import { QueueFilters, FilterState } from "./QueueFilters";

interface ReviewQueueItemCardProps {
    item: ReviewQueueItem;
    isSelected: boolean;
    onSelect: () => void;
    onApprove: (edits?: string) => Promise<void>;
    onReject: (reason?: string) => Promise<void>;
}

export function ReviewQueueItemCard({
    item,
    isSelected,
    onSelect,
    onApprove,
    onReject,
}: ReviewQueueItemCardProps) {
    const router = useRouter();
    const [isApproving, setIsApproving] = useState(false);
    const [isRejecting, setIsRejecting] = useState(false);
    const [editMode, setEditMode] = useState(false);
    const [editedDraft, setEditedDraft] = useState(item.aiDraft);

    // AC3: Approve button disabled until >3s review
    const [reviewTimeElapsed, setReviewTimeElapsed] = useState(0);
    const reviewTimerRef = useRef<NodeJS.Timeout | null>(null);
    const { toast } = useToast();

    // Start 3-second review timer when item is selected
    useEffect(() => {
        if (isSelected) {
            setReviewTimeElapsed(0);
            reviewTimerRef.current = setInterval(() => {
                setReviewTimeElapsed((prev) => prev + 1);
            }, 1000);

            return () => {
                if (reviewTimerRef.current) {
                    clearInterval(reviewTimerRef.current);
                    reviewTimerRef.current = null;
                }
            };
        }
    }, [isSelected]);

    const canApprove = reviewTimeElapsed >= 3; // AC3: Must review for >3 seconds

    const handleApprove = async () => {
        if (!canApprove) return;

        try {
            setIsApproving(true);
            await onApprove(editMode ? editedDraft : undefined);

            // AC3: Success toast on send
            toast({
                title: "Response sent and verified!",
                description: editMode
                    ? "Your edited response has been approved and added to the Verified KB."
                    : "AI draft approved and added to the Verified KB.",
                variant: "success",
            });

            setEditMode(false);
        } catch (error) {
            toast({
                title: "Approval failed",
                description: "Failed to approve the item. Please try again.",
                variant: "error",
            });
        } finally {
            setIsApproving(false);
        }
    };

    const handleReject = async () => {
        try {
            setIsRejecting(true);
            await onReject();
            toast({
                title: "Item rejected",
                description:
                    "The draft has been rejected and removed from the queue.",
                variant: "info",
            });
        } catch (error) {
            toast({
                title: "Rejection failed",
                description: "Failed to reject the item. Please try again.",
                variant: "error",
            });
        } finally {
            setIsRejecting(false);
        }
    };

    const formatTime = (timestamp: string) => {
        const date = new Date(timestamp);
        const now = new Date();
        const diffMs = now.getTime() - date.getTime();
        const diffMins = Math.floor(diffMs / 60000);

        if (diffMins < 1) return "just now";
        if (diffMins < 60) return `${diffMins}m ago`;
        const diffHours = Math.floor(diffMins / 60);
        if (diffHours < 24) return `${diffHours}h ago`;
        return date.toLocaleDateString();
    };

    const confidenceColor = (confidence: number) => {
        if (confidence > 0.75) return "bg-emerald-100 text-emerald-700";
        if (confidence > 0.3) return "bg-amber-100 text-amber-700";
        return "bg-orange-100 text-orange-700";
    };

    const confidenceBar = (confidence: number) => {
        const pct = Math.round(confidence * 100);
        return (
            <div className="flex items-center gap-2 text-xs text-slate-500">
                <span>Confidence:</span>
                <div className="flex-1 min-w-[120px] h-2 rounded-full bg-slate-200">
                    <div
                        className={cn(
                            "h-2 rounded-full",
                            confidence > 0.75
                                ? "bg-emerald-400"
                                : confidence > 0.3
                                ? "bg-amber-400"
                                : "bg-orange-400"
                        )}
                        style={{ width: `${pct}%` }}
                    />
                </div>
                <span className="text-slate-600 font-medium">{pct}%</span>
            </div>
        );
    };

    if (!isSelected) {
        return (
            <div
                onClick={onSelect}
                className="bg-white rounded-xl border border-slate-200 shadow-sm hover:border-slate-300 transition-colors cursor-pointer"
            >
                <div className="p-5">
                    <div className="flex items-center justify-between">
                        <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-3 mb-2">
                                <div
                                    className={cn(
                                        "w-5 h-5 rounded-full flex items-center justify-center",
                                        item.type === "chat"
                                            ? "bg-sky-100"
                                            : "bg-purple-100"
                                    )}
                                >
                                    {item.type === "chat" ? (
                                        <MessageCircle className="w-3 h-3 text-sky-600" />
                                    ) : (
                                        <Mail className="w-3 h-3 text-purple-600" />
                                    )}
                                </div>
                                <span className="text-xs font-medium text-slate-500 uppercase">
                                    {item.type}
                                </span>
                                {confidenceBar(item.confidence)}
                                <span className="text-xs text-slate-500 flex items-center gap-1">
                                    <Clock className="w-3 h-3" />
                                    {formatTime(item.timestamp)}
                                </span>
                            </div>
                            <p className="text-sm text-slate-700 truncate">
                                {item.userQuestion}
                            </p>
                        </div>
                        <Button
                            onClick={(e) => {
                                e.stopPropagation();
                                router.push(`/inbox/${item.id}`);
                            }}
                            variant="outline"
                            size="sm"
                            className="ml-3"
                        >
                            <Eye className="w-4 h-4 mr-1" />
                            Review
                        </Button>
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div
            className="bg-white rounded-xl border-2 border-sky-200 shadow-sm mb-4 overflow-hidden"
            data-item-id={item.id}
        >
            <div className="p-5">
                {/* Item Header */}
                <div className="flex items-start justify-between mb-4">
                    <div className="flex items-center gap-3">
                        <span className="text-xs font-semibold text-amber-700 bg-amber-100 px-2 py-1 rounded-full">
                            Needs Review
                        </span>
                        <span className="text-xs text-slate-500">
                            {formatTime(item.timestamp)} • {item.botName}
                            {formatTime(item.timestamp)} • {item.botName}
                        </span>
                    </div>
                    {confidenceBar(item.confidence)}
                </div>

                {/* Question */}
                <div className="mb-4">
                    <p className="text-xs font-semibold text-slate-500 mb-1 uppercase tracking-wide">
                        Customer Question
                    </p>
                    <p className="text-slate-800 text-base leading-relaxed">
                        {item.userQuestion}
                    </p>
                </div>

                {/* AI Draft - Click to edit */}
                <div
                    className={cn(
                        "bg-slate-50 rounded-lg p-4 mb-4 border transition-all",
                        editMode
                            ? "border-sky-300 ring-2 ring-sky-100"
                            : "border-slate-200 hover:border-slate-300 hover:bg-slate-100/50 cursor-pointer"
                    )}
                    onClick={() => !editMode && setEditMode(true)}
                    data-action="edit"
                >
                    <div className="flex items-center justify-between mb-2">
                        <p className="text-xs font-semibold text-slate-600 flex items-center gap-2">
                            <span className="uppercase">AI Draft</span>
                            {editMode ? (
                                <span className="px-2 py-0.5 rounded-full bg-sky-100 text-sky-700 text-[11px] flex items-center gap-1">
                                    <Edit2 className="w-3 h-3" />
                                    Editing
                                </span>
                            ) : (
                                <span className="px-2 py-0.5 rounded-full bg-slate-200 text-slate-500 text-[11px] flex items-center gap-1">
                                    <Edit2 className="w-3 h-3" />
                                    Click to edit
                                </span>
                            )}
                        </p>
                        {item.citations && item.citations.length > 0 && (
                            <div className="flex items-center gap-2">
                                <span className="text-xs text-slate-500">
                                    Source
                                    {item.citations.length !== 1 ? "s" : ""}
                                </span>
                            </div>
                        )}
                    </div>
                    {editMode ? (
                        <div
                            className="space-y-2"
                            onClick={(e) => e.stopPropagation()}
                        >
                            <textarea
                                value={editedDraft}
                                onChange={(e) => setEditedDraft(e.target.value)}
                                className="w-full p-4 rounded-lg border-2 border-sky-300 bg-white text-slate-700 text-sm leading-relaxed focus:outline-none focus:ring-2 focus:ring-sky-500 focus:border-sky-500 resize-y"
                                rows={8}
                                placeholder="Edit the response here..."
                                autoFocus
                            />
                            <div className="flex items-center justify-between text-xs text-slate-500">
                                <span>{editedDraft.length} characters</span>
                                <span className="text-slate-400">
                                    Click outside or use buttons below
                                </span>
                            </div>
                        </div>
                    ) : (
                        <p className="text-slate-800 text-base leading-relaxed">
                            {item.aiDraft}
                        </p>
                    )}

                    {/* Citations */}
                    {item.citations && item.citations.length > 0 && (
                        <div className="mt-3 pt-3 border-t border-slate-200">
                            <p className="text-xs font-medium text-slate-500 mb-2">
                                SOURCES
                            </p>
                            <div className="space-y-1">
                                {item.citations.map((citation, idx) => (
                                    <div
                                        key={idx}
                                        className="text-xs text-slate-600 flex items-center justify-between"
                                    >
                                        <span className="truncate">
                                            {citation.source}
                                        </span>
                                        <span className="text-slate-500 ml-2">
                                            {Math.round(
                                                citation.relevance * 100
                                            )}
                                            %
                                        </span>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}
                </div>

                {/* Actions - AC 5.5: Include keyboard shortcut badges */}
                <div className="flex items-center gap-2">
                    {!editMode ? (
                        <>
                            <Button
                                onClick={() => {
                                    navigator.clipboard.writeText(item.aiDraft);
                                    toast({
                                        title: "Copied to clipboard",
                                        variant: "info",
                                    });
                                }}
                                variant="outline"
                                size="sm"
                                className="gap-2"
                            >
                                <Copy className="w-4 h-4" />
                                Copy
                            </Button>
                            <div className="flex-1" />
                            {!canApprove && (
                                <span className="text-xs text-amber-600 font-medium">
                                    Review for {3 - reviewTimeElapsed}s more...
                                </span>
                            )}
                            <Button
                                onClick={handleReject}
                                disabled={isRejecting}
                                variant="outline"
                                size="sm"
                                className="text-red-600 hover:text-red-700 hover:bg-red-50 gap-2"
                            >
                                {isRejecting ? (
                                    <Loader2 className="w-4 h-4 animate-spin" />
                                ) : (
                                    <XCircle className="w-4 h-4" />
                                )}
                                {isRejecting ? "Rejecting..." : "Reject"}
                                <kbd className="px-1.5 py-0.5 text-xs bg-slate-100 text-slate-500 rounded">
                                    R
                                </kbd>
                            </Button>
                            <Button
                                onClick={handleApprove}
                                disabled={isApproving || !canApprove}
                                className="bg-emerald-600 hover:bg-emerald-700 text-white gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
                                size="sm"
                                title={
                                    !canApprove
                                        ? "Please review for at least 3 seconds"
                                        : ""
                                }
                            >
                                {isApproving ? (
                                    <Loader2 className="w-4 h-4 animate-spin" />
                                ) : (
                                    <CheckCircle className="w-4 h-4" />
                                )}
                                {isApproving ? "Approving..." : "Approve"}
                                <kbd className="px-1.5 py-0.5 text-xs bg-emerald-700 text-white rounded">
                                    A
                                </kbd>
                            </Button>
                        </>
                    ) : (
                        <>
                            <div className="px-3 py-1.5 bg-amber-50 border border-amber-200 rounded text-xs font-medium text-amber-700">
                                Editing Mode
                            </div>
                            <Button
                                onClick={() => {
                                    setEditMode(false);
                                    setEditedDraft(item.aiDraft);
                                }}
                                variant="outline"
                                size="sm"
                                className="gap-2"
                            >
                                <XCircle className="w-4 h-4" />
                                Cancel
                            </Button>
                            <div className="flex-1" />
                            {!canApprove && (
                                <span className="text-xs text-amber-600 font-medium">
                                    Review for {3 - reviewTimeElapsed}s more...
                                </span>
                            )}
                            <Button
                                onClick={handleReject}
                                disabled={isRejecting}
                                variant="outline"
                                size="sm"
                                className="text-red-600 hover:text-red-700 hover:bg-red-50 gap-2"
                            >
                                {isRejecting ? (
                                    <Loader2 className="w-4 h-4 animate-spin" />
                                ) : (
                                    <XCircle className="w-4 h-4" />
                                )}
                                {isRejecting ? "Rejecting..." : "Reject"}
                                <kbd className="px-1.5 py-0.5 text-xs bg-slate-100 text-slate-500 rounded">
                                    R
                                </kbd>
                            </Button>
                            <Button
                                onClick={handleApprove}
                                disabled={isApproving || !canApprove}
                                className="bg-green-600 hover:bg-green-700 text-white gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
                                size="sm"
                                title={
                                    !canApprove
                                        ? "Please review for at least 3 seconds"
                                        : ""
                                }
                            >
                                {isApproving ? (
                                    <Loader2 className="w-4 h-4 animate-spin" />
                                ) : (
                                    <CheckCircle className="w-4 h-4" />
                                )}
                                {isApproving ? "Approving..." : "Approve"}
                                <kbd className="px-1.5 py-0.5 text-xs bg-green-700 text-white rounded">
                                    A
                                </kbd>
                            </Button>
                        </>
                    )}
                </div>
            </div>
        </div>
    );
}

interface ReviewQueueProps {
    items: ReviewQueueItem[];
    stats: {
        total: number;
        pending: number;
        chat: number;
        email: number;
    };
    isLoading: boolean;
    onApprove: (itemId: string, edits?: string) => Promise<void>;
    onReject: (itemId: string, reason?: string) => Promise<void>;
    sortBy?: string;
    onSortChange?: (sortBy: string) => void;
    filters?: FilterState;
    onFiltersChange?: (filters: FilterState) => void;
}

export function ReviewQueue({
    items,
    stats,
    isLoading,
    onApprove,
    onReject,
    sortBy = "oldest",
    onSortChange,
    filters = {},
    onFiltersChange,
}: ReviewQueueProps) {
    const [selectedId, setSelectedId] = useState<string | null>(
        items.length > 0 ? items[0].id : null
    );
    const [filterType, setFilterType] = useState<"all" | "chat" | "email">(
        "all"
    );
    const [showShortcutHelp, setShowShortcutHelp] = useState(false);
    const [showFilters, setShowFilters] = useState(false);

    const filteredItems = items.filter((item) => {
        if (filterType === "all") return item.status === "pending";
        return item.type === filterType && item.status === "pending";
    });

    // Get selected item index for navigation
    const selectedIndex = filteredItems.findIndex(
        (item) => item.id === selectedId
    );
    const selectedItem =
        selectedIndex >= 0 ? filteredItems[selectedIndex] : null;

    // AC 5.5: Keyboard shortcuts
    useKeyboardShortcuts({
        shortcuts: [
            {
                key: "a",
                description: "Approve current draft",
                action: () => {
                    if (selectedItem) {
                        handleApprove(selectedItem.id);
                    }
                },
                disabled: !selectedItem,
            },
            {
                key: "r",
                description: "Reject current draft",
                action: () => {
                    if (selectedItem) {
                        handleReject(selectedItem.id);
                    }
                },
                disabled: !selectedItem,
            },
            {
                key: "e",
                description: "Focus on edit field",
                action: () => {
                    // This will be handled in ReviewQueueItemCard
                    const editButton = document.querySelector(
                        `[data-item-id="${selectedId}"] [data-action="edit"]`
                    ) as HTMLButtonElement;
                    editButton?.click();
                },
                disabled: !selectedItem,
            },
            {
                key: "n",
                description: "Skip to next item",
                action: () => {
                    if (selectedIndex < filteredItems.length - 1) {
                        setSelectedId(filteredItems[selectedIndex + 1].id);
                    }
                },
                disabled: selectedIndex >= filteredItems.length - 1,
            },
            {
                key: "ArrowLeft",
                description: "Navigate to previous item",
                action: () => {
                    if (selectedIndex > 0) {
                        setSelectedId(filteredItems[selectedIndex - 1].id);
                    }
                },
                disabled: selectedIndex <= 0,
            },
            {
                key: "ArrowRight",
                description: "Navigate to next item",
                action: () => {
                    if (selectedIndex < filteredItems.length - 1) {
                        setSelectedId(filteredItems[selectedIndex + 1].id);
                    }
                },
                disabled: selectedIndex >= filteredItems.length - 1,
            },
            {
                key: "?",
                description: "Show shortcut help",
                action: () => setShowShortcutHelp(!showShortcutHelp),
            },
        ],
        enabled: true,
        ignoreWhenInputFocused: true,
    });

    // AC1: Auto-load next item when current item is removed
    useEffect(() => {
        if (filteredItems.length > 0) {
            // If no item is selected or current selection doesn't exist, select first item
            const selectedExists = filteredItems.some(
                (item) => item.id === selectedId
            );
            if (!selectedExists) {
                setSelectedId(filteredItems[0].id);
            }
        } else {
            setSelectedId(null);
        }
    }, [filteredItems, selectedId]);

    // Wrap approve/reject handlers to ensure next item loads
    const handleApprove = async (itemId: string, edits?: string) => {
        await onApprove(itemId, edits);
        // Auto-load next item is handled by useEffect above
    };

    const handleReject = async (itemId: string, reason?: string) => {
        await onReject(itemId, reason);
        // Auto-load next item is handled by useEffect above
    };

    if (isLoading) {
        return (
            <div className="flex items-center justify-center p-8">
                <div className="text-slate-600">Loading review queue...</div>
            </div>
        );
    }

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="bg-white border-b border-slate-200 px-6 py-4">
                <div className="flex items-center justify-between">
                    <div>
                        <h1 className="text-xl font-semibold text-slate-900">
                            Review Queue
                        </h1>
                        <p className="text-sm text-slate-500 mt-0.5">
                            {/* AC 5.5: Show filtered count in header */}
                            {filteredItems.length} item
                            {filteredItems.length !== 1 ? "s" : ""}
                            {Object.values(filters).filter(Boolean).length > 0
                                ? ` (filtered from ${stats.pending} total)`
                                : " pending review"}
                        </p>
                    </div>
                </div>
            </div>

            <div className="px-6 pb-6">
                {/* Queue Filters */}
                <div className="flex items-center gap-3 mb-6">
                    <button
                        onClick={() => setFilterType("all")}
                        className={cn(
                            "px-3 py-1.5 text-sm font-medium rounded-lg",
                            filterType === "all"
                                ? "bg-sky-100 text-sky-700"
                                : "text-slate-600 hover:bg-slate-100"
                        )}
                    >
                        All ({stats.pending})
                    </button>
                    <button
                        onClick={() => setFilterType("chat")}
                        className={cn(
                            "px-3 py-1.5 text-sm font-medium rounded-lg",
                            filterType === "chat"
                                ? "bg-sky-100 text-sky-700"
                                : "text-slate-600 hover:bg-slate-100"
                        )}
                    >
                        Chat ({stats.chat})
                    </button>
                    <button
                        onClick={() => setFilterType("email")}
                        className={cn(
                            "px-3 py-1.5 text-sm font-medium rounded-lg",
                            filterType === "email"
                                ? "bg-sky-100 text-sky-700"
                                : "text-slate-600 hover:bg-slate-100"
                        )}
                    >
                        Email ({stats.email})
                    </button>
                    <div className="ml-auto flex items-center gap-2">
                        {/* Filters Button (AC 5.5) */}
                        <button
                            onClick={() => setShowFilters(!showFilters)}
                            className={cn(
                                "px-3 py-1.5 text-sm font-medium rounded-lg flex items-center gap-2",
                                showFilters || Object.keys(filters).length > 0
                                    ? "bg-sky-100 text-sky-700"
                                    : "text-slate-600 hover:bg-slate-100 border border-slate-300"
                            )}
                        >
                            <FilterIcon className="w-4 h-4" />
                            Filters
                            {Object.values(filters).filter(Boolean).length >
                                0 && (
                                <span className="px-1.5 py-0.5 text-xs bg-sky-600 text-white rounded-full">
                                    {
                                        Object.values(filters).filter(Boolean)
                                            .length
                                    }
                                </span>
                            )}
                        </button>

                        <span className="text-sm text-slate-500">Sort:</span>
                        <select
                            className="text-sm border-0 bg-transparent text-slate-700 font-medium focus:ring-0 cursor-pointer"
                            value={sortBy}
                            onChange={(e) => onSortChange?.(e.target.value)}
                        >
                            <option value="oldest">Oldest first</option>
                            <option value="newest">Newest first</option>
                            <option value="lowest_confidence">
                                Lowest confidence
                            </option>
                            <option value="highest_confidence">
                                Highest confidence
                            </option>
                        </select>
                    </div>
                </div>

                {/* Filter Panel (AC 5.5) */}
                {showFilters && onFiltersChange && (
                    <div className="mb-6">
                        <QueueFilters
                            filters={filters}
                            onFiltersChange={onFiltersChange}
                            onClose={() => setShowFilters(false)}
                        />
                    </div>
                )}

                {/* Queue Items */}
                {filteredItems.length === 0 ? (
                    <div className="p-8 text-center bg-white rounded-xl border border-dashed border-slate-300">
                        <div className="w-12 h-12 mx-auto mb-4 rounded-full bg-green-100 flex items-center justify-center">
                            <CheckCircle className="w-6 h-6 text-green-600" />
                        </div>
                        <h3 className="text-lg font-medium text-slate-900 mb-1">
                            No items pending review. Nice work!
                        </h3>
                    </div>
                ) : (
                    <div className="space-y-4">
                        {filteredItems.map((item) => (
                            <ReviewQueueItemCard
                                key={item.id}
                                item={item}
                                isSelected={selectedId === item.id}
                                onSelect={() => setSelectedId(item.id)}
                                onApprove={(edits) =>
                                    handleApprove(item.id, edits)
                                }
                                onReject={(reason) =>
                                    handleReject(item.id, reason)
                                }
                            />
                        ))}
                    </div>
                )}
            </div>

            {/* Shortcut Help Modal (AC 5.5) */}
            <ShortcutHelpModal
                isOpen={showShortcutHelp}
                onClose={() => setShowShortcutHelp(false)}
            />
        </div>
    );
}
