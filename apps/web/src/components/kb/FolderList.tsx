"use client";

import React, { useState } from "react";
import { Folder, FolderPlus, Trash2, Edit2, FileText } from "lucide-react";
import type { Folder as FolderType, FolderStats } from "@/types/folder";

interface FolderListProps {
    folders: FolderType[];
    folderStats: Map<string, FolderStats>;
    onCreateFolder: (name: string) => Promise<void>;
    onEditFolder: (folderId: string, newName: string) => Promise<void>;
    onDeleteFolder: (folderId: string) => Promise<void>;
    onSelectFolder: (folderId: string | null) => void;
    selectedFolderId: string | null;
    isLoading?: boolean;
}

export function FolderList({
    folders,
    folderStats,
    onCreateFolder,
    onEditFolder,
    onDeleteFolder,
    onSelectFolder,
    selectedFolderId,
    isLoading = false,
}: FolderListProps) {
    const [isCreating, setIsCreating] = useState(false);
    const [newFolderName, setNewFolderName] = useState("");
    const [editingId, setEditingId] = useState<string | null>(null);
    const [editingName, setEditingName] = useState("");
    const [error, setError] = useState("");

    const handleCreate = async () => {
        if (!newFolderName.trim()) {
            setError("Folder name cannot be empty");
            return;
        }

        try {
            setError("");
            await onCreateFolder(newFolderName.trim());
            setNewFolderName("");
            setIsCreating(false);
        } catch (err) {
            setError(
                err instanceof Error ? err.message : "Failed to create folder"
            );
        }
    };

    const handleEdit = async (folderId: string) => {
        if (!editingName.trim()) {
            setError("Folder name cannot be empty");
            return;
        }

        try {
            setError("");
            await onEditFolder(folderId, editingName.trim());
            setEditingId(null);
            setEditingName("");
        } catch (err) {
            setError(
                err instanceof Error ? err.message : "Failed to edit folder"
            );
        }
    };

    const startEdit = (folder: FolderType) => {
        setEditingId(folder.id);
        setEditingName(folder.name);
        setError("");
    };

    const cancelEdit = () => {
        setEditingId(null);
        setEditingName("");
        setError("");
    };

    return (
        <div className="space-y-2">
            {/* Create Button */}
            <div className="flex items-center justify-end">
                {!isCreating && (
                    <button
                        onClick={() => setIsCreating(true)}
                        className="flex items-center gap-1 text-xs text-emerald-600 hover:text-emerald-700"
                        disabled={isLoading}
                    >
                        <FolderPlus size={14} />
                        New Folder
                    </button>
                )}
            </div>

            {error && (
                <div className="text-xs text-red-600 bg-red-50 border border-red-200 rounded px-2 py-1">
                    {error}
                </div>
            )}

            {/* Create Folder Form */}
            {isCreating && (
                <div className="flex items-center gap-2 p-2 bg-slate-50 rounded border border-slate-200">
                    <Folder size={16} className="text-slate-400" />
                    <input
                        type="text"
                        value={newFolderName}
                        onChange={(e) => setNewFolderName(e.target.value)}
                        onKeyDown={(e) => {
                            if (e.key === "Enter") handleCreate();
                            if (e.key === "Escape") {
                                setIsCreating(false);
                                setNewFolderName("");
                                setError("");
                            }
                        }}
                        placeholder="Folder name"
                        className="flex-1 text-sm bg-white border border-slate-300 rounded px-2 py-1 focus:outline-none focus:ring-2 focus:ring-emerald-500"
                        autoFocus
                    />
                    <button
                        onClick={handleCreate}
                        className="text-xs text-emerald-600 hover:text-emerald-700 font-medium"
                    >
                        Create
                    </button>
                    <button
                        onClick={() => {
                            setIsCreating(false);
                            setNewFolderName("");
                            setError("");
                        }}
                        className="text-xs text-slate-500 hover:text-slate-700"
                    >
                        Cancel
                    </button>
                </div>
            )}

            {/* All Documents (no folder) */}
            <button
                onClick={() => onSelectFolder(null)}
                className={`w-full flex items-center px-3 py-2 text-sm rounded transition-colors ${selectedFolderId === null
                    ? "bg-emerald-50 text-emerald-700 border border-emerald-200"
                    : "hover:bg-slate-50 text-slate-700 border border-transparent"
                    }`}
            >
                <div className="flex items-center gap-2 flex-1">
                    <FileText size={16} />
                    <span>All Documents</span>
                </div>
                <span className="ml-auto text-xs text-slate-500 tabular-nums text-right min-w-[3ch] flex-shrink-0 overflow-hidden">
                    {folderStats.get("null")?.document_count || 0}
                </span>
            </button>

            {/* Folder List */}
            <div className="space-y-1">
                {folders.map((folder) => (
                    <div
                        key={folder.id}
                        className={`group flex items-center gap-2 px-3 py-2 text-sm rounded transition-colors ${selectedFolderId === folder.id
                            ? "bg-emerald-50 text-emerald-700 border border-emerald-200"
                            : "hover:bg-slate-50 text-slate-700 border border-transparent"
                            }`}
                    >
                        {editingId === folder.id ? (
                            // Edit Mode
                            <>
                                <Folder
                                    size={16}
                                    className="text-slate-400 flex-shrink-0"
                                />
                                <input
                                    type="text"
                                    value={editingName}
                                    onChange={(e) =>
                                        setEditingName(e.target.value)
                                    }
                                    onKeyDown={(e) => {
                                        if (e.key === "Enter")
                                            handleEdit(folder.id);
                                        if (e.key === "Escape") cancelEdit();
                                    }}
                                    className="flex-1 text-sm bg-white border border-slate-300 rounded px-2 py-1 focus:outline-none focus:ring-2 focus:ring-emerald-500"
                                    autoFocus
                                />
                                <button
                                    onClick={() => handleEdit(folder.id)}
                                    className="text-xs text-emerald-600 hover:text-emerald-700"
                                >
                                    Save
                                </button>
                                <button
                                    onClick={cancelEdit}
                                    className="text-xs text-slate-500 hover:text-slate-700"
                                >
                                    Cancel
                                </button>
                            </>
                        ) : (
                            // View Mode
                            <>
                                <button
                                    onClick={() => onSelectFolder(folder.id)}
                                    className="flex items-center gap-2 flex-1 min-w-0 text-left"
                                >
                                    <Folder size={16} className="flex-shrink-0" />
                                    <span className="truncate">
                                        {folder.name}
                                    </span>
                                </button>
                                <div className="ml-auto flex items-center gap-2 flex-shrink-0">
                                    <div className="opacity-0 group-hover:opacity-100 flex items-center gap-1">
                                        <button
                                            onClick={() => startEdit(folder)}
                                            className="p-1 hover:bg-slate-200 rounded"
                                            title="Rename folder"
                                        >
                                            <Edit2
                                                size={14}
                                                className="text-slate-500"
                                            />
                                        </button>
                                        <button
                                            onClick={() =>
                                                onDeleteFolder(folder.id)
                                            }
                                            className="p-1 hover:bg-red-100 rounded"
                                            title="Delete folder"
                                        >
                                            <Trash2
                                                size={14}
                                                className="text-red-500"
                                            />
                                        </button>
                                    </div>
                                    <div className="w-6 text-right">
                                        <span className="text-xs text-slate-500 tabular-nums">
                                            {folderStats.get(folder.id)
                                                ?.document_count || 0}
                                        </span>
                                    </div>
                                </div>
                            </>
                        )}
                    </div>
                ))}
            </div>

            {isLoading && (
                <div className="text-xs text-slate-500 text-center py-2">
                    Loading folders...
                </div>
            )}

            {!isLoading && folders.length === 0 && (
                <div className="text-xs text-slate-500 text-center py-4">
                    No folders yet. Create one to organize your documents.
                </div>
            )}
        </div>
    );
}
