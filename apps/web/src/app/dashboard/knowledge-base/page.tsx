"use client";

import { DashboardLayout } from "@/components";
import { FolderList } from "@/components/kb";
import { useGroup } from "@/contexts/GroupContext";
import { foldersApi } from "@/lib/api/folders";
import { documentsApi } from "@/lib/api/documents";
import { useState, useEffect } from "react";
import type { Folder, FolderStats } from "@/types/folder";
import type { Document } from "@/types/document";
import { DocumentCard } from "@/components/kb/DocumentCard";
import { UploadModal } from "@/components/kb/UploadModal";
import { SearchBar } from "@/components/kb/SearchBar";
import { Upload, Folder as FolderIcon } from "lucide-react";

export default function GroupKnowledgeBasePage() {
    const { currentGroup } = useGroup();
    const [folders, setFolders] = useState<Folder[]>([]);
    const [selectedFolderId, setSelectedFolderId] = useState<string | null>(null);
    const [documents, setDocuments] = useState<Document[]>([]);
    const [folderStats, setFolderStats] = useState<Map<string, FolderStats>>(new Map());
    const [isLoading, setIsLoading] = useState(false);
    const [isUploadModalOpen, setIsUploadModalOpen] = useState(false);
    const [searchQuery, setSearchQuery] = useState("");

    // Fetch folders
    useEffect(() => {
        if (currentGroup?.id) {
            setIsLoading(true);
            Promise.all([
                foldersApi.listFolders(currentGroup.id),
                documentsApi.listDocuments(currentGroup.id, 1, 100),
            ])
                .then(([fetchedFolders, docsResponse]) => {
                    setFolders(fetchedFolders);
                    setDocuments(docsResponse.documents);
                    
                    // Calculate folder stats
                    const stats = new Map<string, FolderStats>();
                    fetchedFolders.forEach((folder: Folder) => {
                        const docCount = docsResponse.documents.filter(
                            (d: Document) => d.folder_id === folder.id
                        ).length;
                        stats.set(folder.id, { document_count: docCount });
                    });
                    // Count documents without folder
                    const noFolderCount = docsResponse.documents.filter((d: Document) => !d.folder_id).length;
                    stats.set("null", { document_count: noFolderCount });
                    setFolderStats(stats);
                })
                .catch((err) => console.error("Failed to fetch data:", err))
                .finally(() => setIsLoading(false));
        }
    }, [currentGroup?.id]);

    const handleCreateFolder = async (name: string) => {
        if (!currentGroup?.id) return;
        const newFolder = await foldersApi.createFolder(currentGroup.id, { name });
        setFolders((prev) => [...prev, newFolder]);
        setFolderStats((prev) => new Map(prev).set(newFolder.id, { document_count: 0 }));
    };

    const handleEditFolder = async (folderId: string, newName: string) => {
        if (!currentGroup?.id) return;
        const updated = await foldersApi.updateFolder(currentGroup.id, folderId, { name: newName });
        setFolders((prev) =>
            prev.map((f) => (f.id === folderId ? updated : f))
        );
    };

    const handleDeleteFolder = async (folderId: string) => {
        if (!currentGroup?.id) return;
        if (!confirm("Delete this folder? Documents will be moved to root.")) return;
        
        await foldersApi.deleteFolder(currentGroup.id, folderId);
        setFolders((prev) => prev.filter((f) => f.id !== folderId));
        setFolderStats((prev) => {
            const newStats = new Map(prev);
            newStats.delete(folderId);
            return newStats;
        });
        if (selectedFolderId === folderId) {
            setSelectedFolderId(null);
        }
    };

    const handleUpload = async (files: File[], folderId?: string) => {
        if (!currentGroup?.id) return;
        // Upload files
        await Promise.all(
            files.map((file) =>
                documentsApi.uploadDocuments(currentGroup.id, [file], undefined, folderId)
            )
        );
        // Refresh documents
        const docsResponse = await documentsApi.listDocuments(currentGroup.id, 1, 100);
        setDocuments(docsResponse.documents);
    };

    const filteredDocuments = documents.filter((doc) => {
        const matchesFolder = selectedFolderId === null
            ? !doc.folder_id
            : doc.folder_id === selectedFolderId;
        const matchesSearch = !searchQuery ||
            doc.filename.toLowerCase().includes(searchQuery.toLowerCase());
        return matchesFolder && matchesSearch;
    });

    if (!currentGroup) {
        return (
            <DashboardLayout>
                <div className="text-center py-12">
                    <p className="text-slate-600">Please select a group first</p>
                </div>
            </DashboardLayout>
        );
    }

    return (
        <DashboardLayout>
            <div className="space-y-6">
                {/* Header */}
                <div>
                    <h2 className="text-2xl font-semibold text-slate-900">
                        Knowledge Base
                    </h2>
                    <p className="text-sm text-slate-600 mt-1">
                        Manage documents and folders for {currentGroup.name}
                    </p>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
                    {/* Sidebar - Folders */}
                    <div className="lg:col-span-1">
                        <div className="bg-white border border-slate-200 rounded-lg p-4">
                            <FolderList
                                folders={folders}
                                folderStats={folderStats}
                                onCreateFolder={handleCreateFolder}
                                onEditFolder={handleEditFolder}
                                onDeleteFolder={handleDeleteFolder}
                                onSelectFolder={setSelectedFolderId}
                                selectedFolderId={selectedFolderId}
                                isLoading={isLoading}
                            />
                        </div>
                    </div>

                    {/* Main Content - Documents */}
                    <div className="lg:col-span-3 space-y-4">
                        {/* Toolbar */}
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

                        {/* Document Grid */}
                        {isLoading ? (
                            <div className="text-center py-12 text-slate-500">
                                Loading documents...
                            </div>
                        ) : filteredDocuments.length === 0 ? (
                            <div className="bg-white border border-slate-200 rounded-lg p-12 text-center">
                                <FolderIcon size={48} className="text-slate-300 mx-auto mb-4" />
                                <h3 className="text-lg font-medium text-slate-900 mb-2">
                                    No documents
                                </h3>
                                <p className="text-sm text-slate-600">
                                    {selectedFolderId
                                        ? "This folder is empty"
                                        : "Upload documents to get started"}
                                </p>
                            </div>
                        ) : (
                            <div className="grid gap-4">
                                {filteredDocuments.map((document) => (
                                    <DocumentCard
                                        key={document.id}
                                        document={document}
                                        onView={() => {}}
                                        onDelete={async () => {
                                            await documentsApi.deleteDocument(currentGroup.id, document.id);
                                            setDocuments((prev) => prev.filter((d) => d.id !== document.id));
                                        }}
                                        onReprocess={async () => {}}
                                    />
                                ))}
                            </div>
                        )}
                    </div>
                </div>

                {/* Upload Modal */}
                <UploadModal
                    isOpen={isUploadModalOpen}
                    onClose={() => setIsUploadModalOpen(false)}
                    onUpload={handleUpload}
                    folders={folders}
                />
            </div>
        </DashboardLayout>
    );
}
