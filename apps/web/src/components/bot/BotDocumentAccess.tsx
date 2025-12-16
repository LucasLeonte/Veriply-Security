"use client";

import React, { useState, useEffect, useCallback } from "react";
import { Folder, FileText, Check, X, ChevronDown, ChevronRight } from "lucide-react";
import type { Document } from "@/types/document";
import type { Folder as FolderType } from "@/types/folder";
import { botAccessApi } from "@/lib/api/botAccess";
import type { FolderAccessItem, DocumentAccessItem } from "@/types/botAccess";

interface BotDocumentAccessProps {
    botId: string;
    groupId: string;
}

interface DocumentWithAccess extends Document {
    _access: {
        is_allowed: boolean;
        source: string;
    };
}

interface FolderWithDocs {
    folder: FolderType | null;
    documents: DocumentWithAccess[];
    folderAccess: boolean | null; // null = not set, true = allowed, false = denied
    isExpanded: boolean;
}

export function BotDocumentAccess({ botId, groupId }: BotDocumentAccessProps) {
    const [folders, setFolders] = useState<FolderWithDocs[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState("");
    const [savingIds, setSavingIds] = useState<Set<string>>(new Set());

    const loadAccessData = useCallback(async () => {
        try {
            setIsLoading(true);
            setError("");
            const summary = await botAccessApi.getBotAccess(botId);
            
            // Group documents by folder
            const folderMap = new Map<string | null, FolderWithDocs>();
            
            // Process folders
            summary.folders.forEach((folderAccess: FolderAccessItem) => {
                folderMap.set(folderAccess.folder_id, {
                    folder: folderAccess.folder,
                    documents: [],
                    folderAccess: folderAccess.is_allowed,
                    isExpanded: false,
                });
            });

            // Process documents
            summary.documents.forEach((docAccess: DocumentAccessItem) => {
                const folderId = docAccess.document.folder_id || null;
                
                if (!folderMap.has(folderId)) {
                    folderMap.set(folderId, {
                        folder: null,
                        documents: [],
                        folderAccess: null,
                        isExpanded: true, // Expand root by default
                    });
                }

                const docWithAccess: DocumentWithAccess = {
                    ...docAccess.document,
                    _access: {
                        is_allowed: docAccess.is_allowed,
                        source: docAccess.source,
                    }
                };
                folderMap.get(folderId)!.documents.push(docWithAccess);
            });

            setFolders(Array.from(folderMap.values()).sort((a, b) => {
                // Root folder first
                if (!a.folder && b.folder) return -1;
                if (a.folder && !b.folder) return 1;
                // Then alphabetically
                if (!a.folder || !b.folder) return 0;
                return a.folder.name.localeCompare(b.folder.name);
            }));
        } catch (err) {
            setError(err instanceof Error ? err.message : "Failed to load access data");
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
            prev.map((f, i) => (i === index ? { ...f, isExpanded: !f.isExpanded } : f))
        );
    };

    const handleFolderToggle = async (folderId: string, currentAccess: boolean | null) => {
        const newAccess = currentAccess === true ? false : true; // Toggle between true and false
        
        setSavingIds((prev) => new Set(prev).add(folderId));
        try {
            await botAccessApi.setFolderAccess(folderId, { is_allowed: newAccess });
            await loadAccessData(); // Refresh to get updated state
        } catch (err) {
            setError(err instanceof Error ? err.message : "Failed to update folder access");
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
        try {
            await botAccessApi.setDocumentAccess(documentId, { is_allowed: newAccess });
            await loadAccessData(); // Refresh
        } catch (err) {
            setError(err instanceof Error ? err.message : "Failed to update document access");
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
        <div className="space-y-2">
            {folders.map((folderData, index) => {
                const folderId = folderData.folder?.id || "root";
                const isSaving = savingIds.has(folderId);

                return (
                    <div key={folderId} className="border border-slate-200 rounded-lg bg-white">
                        {/* Folder Header */}
                        <div className="flex items-center gap-2 p-3 border-b border-slate-200">
                            <button
                                onClick={() => toggleFolder(index)}
                                className="p-1 hover:bg-slate-100 rounded"
                            >
                                {folderData.isExpanded ? (
                                    <ChevronDown size={16} className="text-slate-500" />
                                ) : (
                                    <ChevronRight size={16} className="text-slate-500" />
                                )}
                            </button>

                            <Folder size={18} className="text-slate-500" />
                            
                            <span className="flex-1 font-medium text-slate-900">
                                {folderData.folder?.name || "All Documents (No Folder)"}
                            </span>

                            <span className="text-xs text-slate-500 mr-2">
                                {folderData.documents.length} doc{folderData.documents.length !== 1 ? "s" : ""}
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
                                    folderData.documents.map((doc: DocumentWithAccess) => {
                                        const access = doc._access;
                                        const docSaving = savingIds.has(doc.id);

                                        return (
                                            <div
                                                key={doc.id}
                                                className="flex items-center gap-3 p-3 hover:bg-slate-50"
                                            >
                                                <FileText size={16} className="text-slate-400" />
                                                
                                                <div className="flex-1 min-w-0">
                                                    <p className="text-sm font-medium text-slate-900 truncate">
                                                        {doc.filename}
                                                    </p>
                                                    <p className="text-xs text-slate-500">
                                                        {access.source === "explicit"
                                                            ? "Explicit access"
                                                            : access.source === "folder"
                                                            ? "Inherited from folder"
                                                            : "Default (denied)"}
                                                    </p>
                                                </div>

                                                <button
                                                    onClick={() =>
                                                        handleDocumentToggle(doc.id, access.is_allowed)
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
                                                            <Check size={14} />
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
                                    })
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
