"use client";

import React, { useState, useEffect } from "react";
import { Document } from "@/types/document";
import { DocumentCard } from "./DocumentCard";
import { SearchBar } from "./SearchBar";
import { Pagination } from "./Pagination";
import { UploadModal } from "./UploadModal";
import { MoveToFolderModal } from "./MoveToFolderModal";
import { ConfirmDeleteDialog } from "./ConfirmDeleteDialog";
import { BulkDeleteToolbar } from "../knowledge-base/BulkDeleteToolbar";
import { BulkDeleteConfirmationModal } from "../modals/BulkDeleteConfirmationModal";
import { DeleteConfirmationModal } from "../modals/DeleteConfirmationModal";
import { useDocumentDeletion } from "@/hooks/useDocumentDeletion";
import { Upload, Loader, FileText } from "lucide-react";
import { useRouter } from "next/navigation";

import type { Folder } from "@/types/folder";
import { documentsApi } from "@/lib/api/documents";
import { useGroup } from "@/contexts/GroupContext";

interface KnowledgeBaseListProps {
    botId: string;
    onUpload: (files: File[], folderId?: string) => Promise<void>;
    onDelete: (documentId: string) => Promise<void>;
    onReprocess: (documentId: string) => Promise<void>;
    onMove?: (document: Document, folderId: string | null) => Promise<void>;
    documents: Document[];
    totalCount: number;
    currentPage: number;
    totalPages: number;
    onPageChange: (page: number) => void;
    onSearchChange?: (search: string) => void;
    isLoading: boolean;
    error?: string | null;
    folders?: Folder[];
}

const ITEMS_PER_PAGE = 10;

export function KnowledgeBaseList({
    botId,
    onUpload,
    onDelete,
    onReprocess,
    onMove,
    documents,
    totalCount,
    currentPage,
    totalPages,
    onPageChange,
    onSearchChange,
    isLoading,
    error,
    folders = [],
}: KnowledgeBaseListProps) {
    const { currentGroup } = useGroup();
    const router = useRouter();
    const [searchQuery, setSearchQuery] = useState("");
    const [isUploadModalOpen, setIsUploadModalOpen] = useState(false);
    const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false);
    const [moveModalOpen, setMoveModalOpen] = useState(false);
    const [documentToDelete, setDocumentToDelete] = useState<Document | null>(
        null
    );
    const [documentToMove, setDocumentToMove] = useState<Document | null>(null);
    const [isDeleting, setIsDeleting] = useState(false);

    // Bulk deletion state
    const [selectedDocumentIds, setSelectedDocumentIds] = useState<Set<string>>(
        new Set()
    );
    const [isBulkDeleteModalOpen, setIsBulkDeleteModalOpen] = useState(false);
    const {
        deleteDocument,
        bulkDeleteDocuments,
        deletingIds,
        isDeleting: isHookDeleting,
    } = useDocumentDeletion();

    // Debounce search and notify parent
    useEffect(() => {
        const timer = setTimeout(() => {
            onSearchChange?.(searchQuery);
        }, 300);
        return () => clearTimeout(timer);
    }, [searchQuery, onSearchChange]);

    // Clear selection when documents change (e.g., pagination, search)
    useEffect(() => {
        setSelectedDocumentIds(new Set());
    }, [documents]);

    const handleViewDocument = (document: Document) => {
        router.push(`/dashboard/bots/${botId}/knowledge-base/${document.id}`);
    };

    const handleDeleteClick = (document: Document) => {
        setDocumentToDelete(document);
        setIsDeleteDialogOpen(true);
    };

    const handleDeleteConfirm = async () => {
        if (!documentToDelete) return;

        setIsDeleting(true);
        try {
            await onDelete(documentToDelete.id);
            setIsDeleteDialogOpen(false);
            setDocumentToDelete(null);
        } catch (err) {
            console.error("Delete failed:", err);
        } finally {
            setIsDeleting(false);
        }
    };

    const handleReprocess = async (document: Document) => {
        try {
            await onReprocess(document.id);
        } catch (err) {
            console.error("Reprocess failed:", err);
        }
    };

    // Bulk selection handlers
    const handleSelectAll = () => {
        if (selectedDocumentIds.size === documents.length) {
            // Deselect all
            setSelectedDocumentIds(new Set());
        } else {
            // Select all on current page
            const allIds = new Set(documents.map((doc) => doc.id));
            setSelectedDocumentIds(allIds);
        }
    };

    const handleToggleSelection = (documentId: string) => {
        const newSelection = new Set(selectedDocumentIds);
        if (newSelection.has(documentId)) {
            newSelection.delete(documentId);
        } else {
            newSelection.add(documentId);
        }
        setSelectedDocumentIds(newSelection);
    };

    const handleBulkDeleteClick = () => {
        setIsBulkDeleteModalOpen(true);
    };

    const handleBulkDeleteConfirm = async () => {
        const documentIds = Array.from(selectedDocumentIds);
        const documentNames = documents
            .filter((doc) => selectedDocumentIds.has(doc.id))
            .map((doc) => doc.filename);

        try {
            await bulkDeleteDocuments(botId, documentIds, documentNames);
            setIsBulkDeleteModalOpen(false);
            setSelectedDocumentIds(new Set());
            // Note: Parent component should refresh document list
        } catch (err) {
            console.error("Bulk delete failed:", err);
        }
    };

    return (
        <div className="space-y-6">
            {/* Header Section */}
            <div className="flex items-center justify-between gap-4">
                <SearchBar
                    value={searchQuery}
                    onChange={setSearchQuery}
                    placeholder="Search documents..."
                    className="flex-1 max-w-md"
                />
                <button
                    onClick={() => setIsUploadModalOpen(true)}
                    className="flex items-center gap-2 px-4 py-2 bg-emerald-600 text-white text-sm font-medium rounded-md hover:bg-emerald-700 transition-colors"
                >
                    <Upload size={18} />
                    Upload Documents
                </button>
            </div>

            {/* Bulk Delete Toolbar */}
            {!isLoading && !error && documents.length > 0 && (
                <BulkDeleteToolbar
                    selectedCount={selectedDocumentIds.size}
                    totalCount={documents.length}
                    allSelected={
                        selectedDocumentIds.size === documents.length &&
                        documents.length > 0
                    }
                    onSelectAll={handleSelectAll}
                    onBulkDelete={handleBulkDeleteClick}
                    disabled={isHookDeleting}
                />
            )}

            {/* Document Count */}
            {!isLoading && (
                <div className="text-sm text-slate-600">
                    Showing {documents.length} of {totalCount} document
                    {totalCount !== 1 ? "s" : ""}
                </div>
            )}

            {/* Loading State */}
            {isLoading && (
                <div className="flex items-center justify-center py-12">
                    <Loader size={32} className="text-slate-400 animate-spin" />
                </div>
            )}

            {/* Error State */}
            {error && !isLoading && (
                <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-sm text-red-600">
                    {error}
                </div>
            )}

            {/* Empty State */}
            {!isLoading && !error && documents.length === 0 && (
                <div className="bg-white border border-slate-200 rounded-lg p-12 text-center">
                    <FileText
                        size={48}
                        className="text-slate-300 mx-auto mb-4"
                    />
                    {searchQuery ? (
                        <>
                            <h3 className="text-lg font-medium text-slate-900 mb-2">
                                No documents found
                            </h3>
                            <p className="text-sm text-slate-600">
                                Try adjusting your search or upload new
                                documents
                            </p>
                        </>
                    ) : (
                        <>
                            <h3 className="text-lg font-medium text-slate-900 mb-2">
                                No documents yet
                            </h3>
                            <p className="text-sm text-slate-600 mb-4">
                                Upload your first document to build your
                                knowledge base
                            </p>
                            <button
                                onClick={() => setIsUploadModalOpen(true)}
                                className="inline-flex items-center gap-2 px-4 py-2 bg-emerald-600 text-white text-sm font-medium rounded-md hover:bg-emerald-700 transition-colors"
                            >
                                <Upload size={18} />
                                Upload Documents
                            </button>
                        </>
                    )}
                </div>
            )}

            {/* Document List */}
            {!isLoading && !error && documents.length > 0 && (
                <div className="space-y-4">
                    {documents.map((document) => {
                        const folderName = document.folder_id
                            ? folders.find((f) => f.id === document.folder_id)
                                  ?.name
                            : undefined;

                        return (
                            <DocumentCard
                                key={document.id}
                                document={document}
                                onView={handleViewDocument}
                                onDelete={handleDeleteClick}
                                onReprocess={handleReprocess}
                                onMove={(doc) => {
                                    setDocumentToMove(doc);
                                    setMoveModalOpen(true);
                                }}
                                isSelected={selectedDocumentIds.has(
                                    document.id
                                )}
                                onToggleSelection={handleToggleSelection}
                                isDeleting={deletingIds.has(document.id)}
                                folderName={folderName}
                            />
                        );
                    })}
                </div>
            )}

            {/* Pagination */}
            {!isLoading && !error && totalPages > 1 && (
                <Pagination
                    currentPage={currentPage}
                    totalPages={totalPages}
                    onPageChange={onPageChange}
                    totalItems={totalCount}
                    itemsPerPage={ITEMS_PER_PAGE}
                />
            )}

            {/* Upload Modal */}
            <UploadModal
                isOpen={isUploadModalOpen}
                onClose={() => setIsUploadModalOpen(false)}
                onUpload={onUpload}
                folders={folders}
            />

            {/* Move to Folder Modal */}
            <MoveToFolderModal
                isOpen={moveModalOpen}
                onClose={() => {
                    setMoveModalOpen(false);
                    setDocumentToMove(null);
                }}
                onMove={async (folderId) => {
                    if (!documentToMove || !currentGroup?.id) return;
                    if (onMove) {
                        await onMove(documentToMove, folderId);
                    } else {
                        await documentsApi.moveDocumentToFolder(
                            documentToMove.id,
                            folderId,
                            currentGroup.id
                        );
                    }
                    setMoveModalOpen(false);
                    setDocumentToMove(null);
                }}
                folders={folders}
                documentName={documentToMove?.filename}
                currentFolderId={documentToMove?.folder_id}
            />

            {/* Delete Confirmation Dialog */}
            <ConfirmDeleteDialog
                isOpen={isDeleteDialogOpen}
                onClose={() => {
                    setIsDeleteDialogOpen(false);
                    setDocumentToDelete(null);
                }}
                onConfirm={handleDeleteConfirm}
                documentName={documentToDelete?.filename || ""}
                isDeleting={isDeleting}
            />

            {/* Bulk Delete Confirmation Modal */}
            <BulkDeleteConfirmationModal
                isOpen={isBulkDeleteModalOpen}
                onClose={() => setIsBulkDeleteModalOpen(false)}
                onConfirm={handleBulkDeleteConfirm}
                selectedCount={selectedDocumentIds.size}
                selectedDocuments={documents
                    .filter((doc) => selectedDocumentIds.has(doc.id))
                    .map((doc) => ({ id: doc.id, name: doc.filename }))}
                isDeleting={isHookDeleting}
            />
        </div>
    );
}
