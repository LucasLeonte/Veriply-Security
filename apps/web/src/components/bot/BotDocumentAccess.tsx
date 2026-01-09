"use client";

import React, { useState, useEffect, useCallback } from "react";
import {
    Folder,
    FileText,
    Check,
    X,
    ChevronDown,
    ChevronRight,
} from "lucide-react";
import type { Document } from "@/types/document";
import { botAccessApi } from "@/lib/api/botAccess";
import type { FolderAccessItem, DocumentAccessItem } from "@/types/botAccess";

interface BotDocumentAccessProps {
    botId: string;
    groupId: string;
}

interface DocumentWithAccess {
    id: string;
    title: string;
    folder_id: string | null;
    _access: {
        is_allowed: boolean;
        has_explicit_access: boolean;
        explicit_allowed: boolean | null;
    };
}

interface FolderInfo {
    id: string;
    name: string;
}

interface FolderWithDocs {
    folder: FolderInfo | null;
    documents: DocumentWithAccess[];
    folderAccess: boolean | null; // null = not set, true = allowed, false = denied
    isExpanded: boolean;
}

export function BotDocumentAccess({ botId, groupId }: BotDocumentAccessProps) {
    const [folders, setFolders] = useState<FolderWithDocs[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState("");
    const [savingIds, setSavingIds] = useState<Set<string>>(new Set());
    const expandedStateRef = React.useRef<Map<string, boolean>>(new Map());
    const containerRef = React.useRef<HTMLDivElement>(null);
    const scrollPosRef = React.useRef<number>(0);

    const getScrollableParent = (): Element | null => {
        let element = containerRef.current?.parentElement;
        while (element) {
            const { overflow, overflowY } = window.getComputedStyle(element);
            if (
                overflow === "auto" ||
                overflow === "scroll" ||
                overflowY === "auto" ||
                overflowY === "scroll"
            ) {
                return element;
            }
            element = element.parentElement;
        }
        return document.documentElement; // fallback to document scroll
    };

    const loadAccessData = useCallback(async () => {
        try {
            setIsLoading(true);
            setError("");
            const summary = await botAccessApi.getBotAccess(botId);

            // Group documents by folder
            const folderMap = new Map<string | null, FolderWithDocs>();

            // Process folders
            summary.folders.forEach((folderAccess: FolderAccessItem) => {
                const wasExpanded =
                    expandedStateRef.current.get(folderAccess.id) ?? false;
                folderMap.set(folderAccess.id, {
                    folder: { id: folderAccess.id, name: folderAccess.name },
                    documents: [],
                    folderAccess: folderAccess.allowed,
                    isExpanded: wasExpanded,
                });
            });

            // Process documents
            summary.documents.forEach((docAccess: DocumentAccessItem) => {
                const folderId = docAccess.folder_id || null;

                if (!folderMap.has(folderId)) {
                    const wasExpanded =
                        expandedStateRef.current.get("root") ?? true;
                    folderMap.set(folderId, {
                        folder: null,
                        documents: [],
                        folderAccess: null,
                        isExpanded: wasExpanded, // Expand root by default or preserve state
                    });
                }

                const docWithAccess: DocumentWithAccess = {
                    id: docAccess.id,
                    title: docAccess.name,
                    folder_id: docAccess.folder_id,
                    _access: {
                        is_allowed: docAccess.allowed,
                        has_explicit_access: docAccess.has_explicit_access,
                        explicit_allowed: docAccess.explicit_allowed,
                    },
                };
                folderMap.get(folderId)!.documents.push(docWithAccess);
            });

            setFolders(
                Array.from(folderMap.values()).sort((a, b) => {
                    // Root folder first
                    if (!a.folder && b.folder) return -1;
                    if (a.folder && !b.folder) return 1;
                    // Then alphabetically
                    if (!a.folder || !b.folder) return 0;
                    return a.folder.name.localeCompare(b.folder.name);
                })
            );
        } catch (err) {
            setError(
                err instanceof Error
                    ? err.message
                    : "Failed to load access data"
            );
        } finally {
            setIsLoading(false);
        }
    }, [botId]);

    // Fetch access summary
    useEffect(() => {
        if (botId && groupId) {
            loadAccessData();
        }
    }, [botId, groupId, loadAccessData]);

    const toggleFolder = (index: number) => {
        setFolders((prev) =>
            prev.map((f, i) => {
                if (i !== index) return f;
                const newExpanded = !f.isExpanded;
                const key = f.folder?.id || "root";
                expandedStateRef.current.set(key, newExpanded);
                return { ...f, isExpanded: newExpanded };
            })
        );
    };

    const handleFolderToggle = async (
        folderId: string,
        currentAccess: boolean | null
    ) => {
        const newAccess = currentAccess === true ? false : true; // Toggle between true and false

        setSavingIds((prev) => new Set(prev).add(folderId));

        // Optimistically update local state
        setFolders((prev) =>
            prev.map((f) => {
                if (f.folder?.id !== folderId) return f;

                // Update folder access and all documents that inherit from it
                const updatedDocs = f.documents.map((doc) => {
                    // If document has no explicit access, update inherited state
                    if (!doc._access.has_explicit_access) {
                        return {
                            ...doc,
                            _access: {
                                ...doc._access,
                                is_allowed: newAccess,
                            },
                        };
                    }
                    return doc;
                });

                return {
                    ...f,
                    folderAccess: newAccess,
                    documents: updatedDocs,
                };
            })
        );

        try {
            await botAccessApi.setFolderAccess(botId, folderId, {
                is_allowed: newAccess,
            });
            // Store scroll position before refresh
            const scrollParent = getScrollableParent();
            scrollPosRef.current = scrollParent?.scrollTop || 0;

            // Refresh data in background to ensure consistency
            await loadAccessData();

            // Restore scroll position after refresh
            requestAnimationFrame(() => {
                if (scrollParent) {
                    scrollParent.scrollTop = scrollPosRef.current;
                }
            });
        } catch (err) {
            setError(
                err instanceof Error
                    ? err.message
                    : "Failed to update folder access"
            );
            // Revert on error
            await loadAccessData();
        } finally {
            setSavingIds((prev) => {
                const newSet = new Set(prev);
                newSet.delete(folderId);
                return newSet;
            });
        }
    };

    const handleDocumentToggle = async (
        documentId: string,
        currentAccess: boolean | null
    ) => {
        const newAccess = currentAccess === true ? false : true;

        setSavingIds((prev) => new Set(prev).add(documentId));

        // Optimistically update local state
        setFolders((prev) =>
            prev.map((f) => ({
                ...f,
                documents: f.documents.map((doc) =>
                    doc.id === documentId
                        ? {
                              ...doc,
                              _access: {
                                  ...doc._access,
                                  is_allowed: newAccess,
                                  has_explicit_access: true,
                                  explicit_allowed: newAccess,
                              },
                          }
                        : doc
                ),
            }))
        );

        try {
            await botAccessApi.setDocumentAccess(botId, documentId, {
                is_allowed: newAccess,
            });
            // Store scroll position before refresh
            const scrollParent = getScrollableParent();
            scrollPosRef.current = scrollParent?.scrollTop || 0;

            // Refresh data in background to ensure consistency
            await loadAccessData();

            // Restore scroll position after refresh
            requestAnimationFrame(() => {
                if (scrollParent) {
                    scrollParent.scrollTop = scrollPosRef.current;
                }
            });
        } catch (err) {
            setError(
                err instanceof Error
                    ? err.message
                    : "Failed to update document access"
            );
            // Revert on error
            loadAccessData();
        } finally {
            setSavingIds((prev) => {
                const newSet = new Set(prev);
                newSet.delete(documentId);
                return newSet;
            });
        }
    };

    if (isLoading) {
        return (
            <div className="text-center py-12 text-slate-500">
                Loading document access settings...
            </div>
        );
    }

    if (error) {
        return (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-sm text-red-600">
                {error}
            </div>
        );
    }

    return (
        <div ref={containerRef} className="space-y-2">
            {folders.map((folderData, index) => {
                const folderId = folderData.folder?.id || "root";
                const isSaving = savingIds.has(folderId);

                return (
                    <div
                        key={folderId}
                        className="border border-slate-200 rounded-lg bg-white"
                    >
                        {/* Folder Header */}
                        <div className="flex items-center gap-2 p-3 border-b border-slate-200">
                            <button
                                onClick={() => toggleFolder(index)}
                                className="p-1 hover:bg-slate-100 rounded"
                            >
                                {folderData.isExpanded ? (
                                    <ChevronDown
                                        size={16}
                                        className="text-slate-500"
                                    />
                                ) : (
                                    <ChevronRight
                                        size={16}
                                        className="text-slate-500"
                                    />
                                )}
                            </button>

                            <Folder size={18} className="text-slate-500" />

                            <span className="flex-1 font-medium text-slate-900">
                                {folderData.folder?.name ||
                                    "All Documents (No Folder)"}
                            </span>

                            <span className="text-xs text-slate-500 mr-2">
                                {folderData.documents.length} doc
                                {folderData.documents.length !== 1 ? "s" : ""}
                            </span>

                            {folderData.folder && (
                                <button
                                    onClick={() =>
                                        handleFolderToggle(
                                            folderData.folder!.id,
                                            folderData.folderAccess
                                        )
                                    }
                                    disabled={isSaving}
                                    className={`flex items-center gap-1 px-3 py-1 text-sm rounded transition-colors ${
                                        isSaving
                                            ? "opacity-50 cursor-not-allowed"
                                            : folderData.folderAccess === true
                                            ? "bg-emerald-100 text-emerald-700 hover:bg-emerald-200"
                                            : folderData.folderAccess === false
                                            ? "bg-red-100 text-red-700 hover:bg-red-200"
                                            : "bg-slate-100 text-slate-700 hover:bg-slate-200"
                                    }`}
                                >
                                    {folderData.folderAccess === true ? (
                                        <>
                                            <Check size={14} />
                                            Allowed
                                        </>
                                    ) : folderData.folderAccess === false ? (
                                        <>
                                            <X size={14} />
                                            Denied
                                        </>
                                    ) : (
                                        "Not Set"
                                    )}
                                </button>
                            )}
                        </div>

                        {/* Documents List */}
                        {folderData.isExpanded && (
                            <div className="divide-y divide-slate-100">
                                {folderData.documents.length === 0 ? (
                                    <div className="p-4 text-sm text-slate-500 text-center">
                                        No documents in this folder
                                    </div>
                                ) : (
                                    folderData.documents.map(
                                        (doc: DocumentWithAccess) => {
                                            const access = doc._access;
                                            const docSaving = savingIds.has(
                                                doc.id
                                            );

                                            return (
                                                <div
                                                    key={doc.id}
                                                    className="flex items-center gap-3 p-3 hover:bg-slate-50"
                                                >
                                                    <FileText
                                                        size={16}
                                                        className="text-slate-400"
                                                    />

                                                    <div className="flex-1 min-w-0">
                                                        <p className="text-sm font-medium text-slate-900 truncate">
                                                            {doc.title}
                                                        </p>
                                                        <p className="text-xs text-slate-500">
                                                            {access.has_explicit_access
                                                                ? "Explicit access"
                                                                : doc.folder_id &&
                                                                  folderData.folderAccess !==
                                                                      null
                                                                ? "Inherited from folder"
                                                                : "Default (denied)"}
                                                        </p>
                                                    </div>

                                                    <button
                                                        onClick={() =>
                                                            handleDocumentToggle(
                                                                doc.id,
                                                                access.is_allowed
                                                            )
                                                        }
                                                        disabled={docSaving}
                                                        className={`flex items-center gap-1 px-3 py-1 text-sm rounded transition-colors ${
                                                            docSaving
                                                                ? "opacity-50 cursor-not-allowed"
                                                                : access.is_allowed
                                                                ? "bg-emerald-100 text-emerald-700 hover:bg-emerald-200"
                                                                : "bg-red-100 text-red-700 hover:bg-red-200"
                                                        }`}
                                                    >
                                                        {access.is_allowed ? (
                                                            <>
                                                                <Check
                                                                    size={14}
                                                                />
                                                                Allowed
                                                            </>
                                                        ) : (
                                                            <>
                                                                <X size={14} />
                                                                Denied
                                                            </>
                                                        )}
                                                    </button>
                                                </div>
                                            );
                                        }
                                    )
                                )}
                            </div>
                        )}
                    </div>
                );
            })}

            {folders.length === 0 && (
                <div className="text-center py-12 text-slate-500">
                    No documents or folders found in this group
                </div>
            )}
        </div>
    );
}
