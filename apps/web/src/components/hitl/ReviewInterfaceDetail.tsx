"use client";

import React, { useState } from "react";
import {
    ArrowLeft,
    Clock,
    CheckCircle,
    XCircle,
    ChevronDown,
    ChevronUp,
    ExternalLink,
} from "lucide-react";
import { Checkbox } from "@/components/ui/checkbox";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import type { ReviewQueueItemDetail, ContextChunk } from "@/types/hitl";



interface ReviewInterfaceDetailProps {
    item: ReviewQueueItemDetail;
    onApprove: (edits?: string, addToKB?: boolean) => Promise<void>;
    onReject: (reason?: string) => Promise<void>;
    onBack: () => void;
}

export function ReviewInterfaceDetail({
    item,
    onApprove,
    onReject,
    onBack,
}: ReviewInterfaceDetailProps) {
    const [editedDraft, setEditedDraft] = useState(item.aiDraft);
    const [isEditing, setIsEditing] = useState(false);
    const [isApproving, setIsApproving] = useState(false);
    const [addToKB, setAddToKB] = useState(true);
    const [isRejecting, setIsRejecting] = useState(false);
    const hasEdits = editedDraft !== item.aiDraft;

    const handleApprove = async () => {
        try {
            setIsApproving(true);
            await onApprove(hasEdits ? editedDraft : undefined, addToKB);
        } finally {
            setIsApproving(false);
        }
    };

    const handleReject = async () => {
        try {
            setIsRejecting(true);
            await onReject();
        } finally {
            setIsRejecting(false);
        }
    };

    const confidencePercent = Math.round(item.confidence * 100);
    const confidenceColor =
        item.confidence > 0.75
            ? "text-emerald-700 bg-emerald-100"
            : item.confidence > 0.3
                ? "text-amber-700 bg-amber-100"
                : "text-orange-700 bg-orange-100";

    return (
        <div className="h-screen flex flex-col bg-slate-50">
            {/* Top Bar */}
            <div className="bg-white border-b border-slate-200 px-6 py-4 flex items-center justify-between">
                <div className="flex items-center gap-4">
                    <Button
                        variant="ghost"
                        size="sm"
                        onClick={onBack}
                        className="gap-2"
                    >
                        <ArrowLeft className="w-4 h-4" />
                        Back to Queue
                    </Button>
                    <div className="h-6 w-px bg-slate-300" />
                    <div className="flex items-center gap-3">
                        <span
                            className={cn(
                                "px-3 py-1 rounded-full text-sm font-semibold",
                                confidenceColor
                            )}
                        >
                            {confidencePercent}% Confidence
                        </span>
                        <span className="text-sm text-slate-600">
                            {item.botName}
                        </span>
                        <span className="text-sm text-slate-500 flex items-center gap-1">
                            <Clock className="w-4 h-4" />
                            {item.timeInQueue} in queue
                        </span>
                    </div>
                </div>
                <div className="flex items-center gap-2">
                    <div className="flex items-center gap-2 mr-2">
                        <Checkbox
                            id="add-to-kb-detail"
                            checked={addToKB}
                            onCheckedChange={setAddToKB}
                        />
                        <label
                            htmlFor="add-to-kb-detail"
                            className="text-sm text-slate-600 select-none cursor-pointer"
                        >
                            Add to KB
                        </label>
                    </div>
                    <Button
                        onClick={handleReject}
                        disabled={isRejecting || isApproving}
                        variant="outline"
                        className="text-red-600 hover:text-red-700 hover:bg-red-50"
                    >
                        <XCircle className="w-4 h-4 mr-2" />
                        Reject
                    </Button>
                    <Button
                        onClick={handleApprove}
                        disabled={isApproving || isRejecting}
                        className="bg-emerald-600 hover:bg-emerald-700 text-white"
                    >
                        <CheckCircle className="w-4 h-4 mr-2" />
                        {hasEdits ? "Approve with Edits" : "Approve"}
                    </Button>
                </div>
            </div>

            {/* Split View */}
            <div className="flex-1 grid grid-cols-2 gap-0 overflow-hidden">
                {/* Left Panel - Query and Context */}
                <div className="bg-white border-r border-slate-200 overflow-y-auto">
                    <div className="p-6 space-y-6">
                        {/* User Question */}
                        <div>
                            <h2 className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-2">
                                Customer Question
                            </h2>
                            <p className="text-slate-900 text-lg leading-relaxed">
                                {item.userQuestion}
                            </p>
                        </div>

                        {/* Context Chunks */}
                        <div>
                            <h2 className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-3">
                                Retrieved Context ({item.contextChunks.length})
                            </h2>
                            <ContextChunkList chunks={item.contextChunks} />
                        </div>
                    </div>
                </div>

                {/* Right Panel - Editable Draft */}
                <div className="bg-slate-50 overflow-y-auto">
                    <div className="p-6 space-y-4">
                        <div className="flex items-center justify-between">
                            <h2 className="text-xs font-semibold text-slate-500 uppercase tracking-wide">
                                AI Draft Response
                            </h2>
                            {hasEdits && (
                                <span className="text-xs font-medium text-amber-700 bg-amber-100 px-2 py-1 rounded">
                                    Modified
                                </span>
                            )}
                        </div>

                        <div className="bg-white rounded-lg border-2 border-slate-200 overflow-hidden">
                            <textarea
                                value={editedDraft}
                                onChange={(e) => {
                                    setEditedDraft(e.target.value);
                                    setIsEditing(true);
                                }}
                                className="w-full min-h-[400px] p-4 text-slate-800 text-base leading-relaxed focus:outline-none resize-none font-sans"
                                placeholder="AI draft response..."
                            />
                            {/* Citation highlighting overlay (visual indicator) */}
                            <div className="px-4 pb-3">
                                <p className="text-xs text-slate-500">
                                    <span className="font-medium">Tip:</span>{" "}
                                    Citations in <span className="font-mono bg-amber-50 text-amber-700 px-1 rounded">[Source: ...]</span> format are highlighted
                                </p>
                            </div>
                        </div>

                        {/* Citation Preview */}
                        {editedDraft.match(/\[Source:[^\]]+\]/g) && (
                            <div className="bg-amber-50 rounded-lg border border-amber-200 p-3">
                                <p className="text-xs font-semibold text-amber-900 mb-2">
                                    Citations Found ({editedDraft.match(/\[Source:[^\]]+\]/g)?.length || 0})
                                </p>
                                <div className="space-y-1">
                                    {editedDraft.match(/\[Source:[^\]]+\]/g)?.map((citation, idx) => (
                                        <div key={idx} className="text-xs font-mono text-amber-800">
                                            {citation}
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}

                        {/* Citations */}
                        {item.citations && item.citations.length > 0 && (
                            <div className="bg-white rounded-lg border border-slate-200 p-4">
                                <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-3">
                                    Citations ({item.citations.length})
                                </h3>
                                <div className="space-y-2">
                                    {item.citations.map((citation, idx) => (
                                        <div
                                            key={idx}
                                            className="flex items-center justify-between text-sm"
                                        >
                                            <span className="text-slate-700 truncate">
                                                {citation.source}
                                            </span>
                                            <span className="text-slate-500 ml-2 text-xs">
                                                {Math.round(
                                                    citation.relevance * 100
                                                )}
                                                % relevance
                                            </span>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}

interface ContextChunkListProps {
    chunks: ContextChunk[];
}

function ContextChunkList({ chunks }: ContextChunkListProps) {
    const [expandedChunkIds, setExpandedChunkIds] = useState<Set<string>>(
        new Set()
    );

    const toggleChunk = (chunkId: string) => {
        setExpandedChunkIds((prev) => {
            const next = new Set(prev);
            if (next.has(chunkId)) {
                next.delete(chunkId);
            } else {
                next.add(chunkId);
            }
            return next;
        });
    };

    if (chunks.length === 0) {
        return (
            <div className="text-sm text-slate-500 italic p-4 bg-slate-50 rounded-lg border border-slate-200">
                No context chunks available
            </div>
        );
    }

    return (
        <div className="space-y-3">
            {chunks.map((chunk) => {
                const isExpanded = expandedChunkIds.has(chunk.chunk_id);
                const similarityPercent = Math.round(chunk.similarity * 100);

                return (
                    <div
                        key={chunk.chunk_id}
                        className="bg-slate-50 rounded-lg border border-slate-200 overflow-hidden"
                    >
                        {/* Chunk Header */}
                        <div
                            className="p-3 flex items-center justify-between cursor-pointer hover:bg-slate-100"
                            onClick={() => toggleChunk(chunk.chunk_id)}
                        >
                            <div className="flex-1 min-w-0">
                                <div className="flex items-center gap-2">
                                    <span className="text-sm font-medium text-slate-900 truncate">
                                        {chunk.document_name}
                                    </span>
                                    {chunk.page_number && (
                                        <span className="text-xs text-slate-500">
                                            pg. {chunk.page_number}
                                        </span>
                                    )}
                                    <span className="text-xs font-medium text-emerald-700 bg-emerald-100 px-2 py-0.5 rounded">
                                        {similarityPercent}%
                                    </span>
                                </div>
                                {chunk.section && (
                                    <p className="text-xs text-slate-500 mt-1 truncate">
                                        {chunk.section}
                                    </p>
                                )}
                            </div>
                            <div className="flex items-center gap-2 ml-3">
                                <a
                                    href={`/knowledge-base/documents/${chunk.document_id}`}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="text-sky-600 hover:text-sky-700"
                                    onClick={(e) => e.stopPropagation()}
                                >
                                    <ExternalLink className="w-4 h-4" />
                                </a>
                                {isExpanded ? (
                                    <ChevronUp className="w-4 h-4 text-slate-400" />
                                ) : (
                                    <ChevronDown className="w-4 h-4 text-slate-400" />
                                )}
                            </div>
                        </div>

                        {/* Chunk Content */}
                        {isExpanded && (
                            <div className="px-3 pb-3 pt-0">
                                <div className="bg-white rounded border border-slate-200 p-3">
                                    <p className="text-sm text-slate-700 leading-relaxed whitespace-pre-wrap">
                                        {chunk.text}
                                    </p>
                                </div>
                            </div>
                        )}
                    </div>
                );
            })}
        </div>
    );
}
