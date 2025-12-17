"use client";

import { DashboardLayout } from "@/components";
import {
    FolderList,
    ReprocessModal,
    BulkReprocessModal,
} from "@/components/kb";
import { useGroup } from "@/contexts/GroupContext";
import { foldersApi } from "@/lib/api/folders";
import { documentsApi } from "@/lib/api/documents";
import { useState, useEffect, useCallback, useRef } from "react";
import type { Folder, FolderStats } from "@/types/folder";
import type { Document } from "@/types/document";
import { DocumentCard } from "@/components/kb/DocumentCard";
import { UploadModal } from "@/components/kb/UploadModal";
import { MoveToFolderModal } from "@/components/kb/MoveToFolderModal";
import { SearchBar } from "@/components/kb/SearchBar";
import { Upload, Folder as FolderIcon } from "lucide-react";

export default function GroupKnowledgeBasePage() {
    const { currentGroup } = useGroup();
    const [folders, setFolders] = useState<Folder[]>([]);
    const [selectedFolderId, setSelectedFolderId] = useState<string | null>(
        null
    );
    const [documents, setDocuments] = useState<Document[]>([]);
    const [folderStats, setFolderStats] = useState<Map<string, FolderStats>>(
        new Map()
    );
    const [isLoading, setIsLoading] = useState(false);
    const [isUploadModalOpen, setIsUploadModalOpen] = useState(false);
    const [searchQuery, setSearchQuery] = useState("");
    const [moveModalOpen, setMoveModalOpen] = useState(false);
    const [documentToMove, setDocumentToMove] = useState<Document | null>(null);
    const [documentToReprocess, setDocumentToReprocess] =
        useState<Document | null>(null);
    const [selectedDocumentIds, setSelectedDocumentIds] = useState<string[]>(
        []
    );
    const [isReprocessModalOpen, setIsReprocessModalOpen] = useState(false);
    const [isBulkReprocessModalOpen, setIsBulkReprocessModalOpen] =
        useState(false);
    const pollingIntervalRef = useRef<NodeJS.Timeout | null>(null);

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
                    setSelectedDocumentIds([]);
                    setFolderStats(
                        buildFolderStats(fetchedFolders, docsResponse.documents)
                    );
                })
                .catch((err) => console.error("Failed to fetch data:", err))
                .finally(() => setIsLoading(false));
        }
    }, [currentGroup?.id]);

    const buildFolderStats = useCallback(
        (fetchedFolders: Folder[], docs: Document[]) => {
            const stats = new Map<string, FolderStats>();
            fetchedFolders.forEach((folder: Folder) => {
                const docCount = docs.filter(
                    (d: Document) => d.folder_id === folder.id
                ).length;
                stats.set(folder.id, { document_count: docCount });
            });
            // For "All Documents" we want the total count across every folder
            stats.set("null", { document_count: docs.length });
            return stats;
        },
        []
    );

    // Poll for document status updates
    useEffect(() => {
        const processingDocIds = documents
            .filter((doc) => doc.status === "processing")
            .map((doc) => doc.id);

        if (processingDocIds.length === 0 || !currentGroup?.id) {
            // Clear polling if no processing documents
            if (pollingIntervalRef.current) {
                clearInterval(pollingIntervalRef.current);
                pollingIntervalRef.current = null;
            }
            return;
        }

        const pollDocuments = async () => {
            try {
                const updatedDocs: Document[] = [];
                for (const docId of processingDocIds) {
                    try {
                        const updated = await documentsApi.getDocument(
                            docId,
                            currentGroup.id
                        );
                        updatedDocs.push(updated as Document);
                    } catch (err) {
                        console.error(
                            `Failed to fetch document ${docId}:`,
                            err
                        );
                    }
                }

                if (updatedDocs.length > 0) {
                    setDocuments((prevDocs) => {
                        const docMap = new Map(
                            prevDocs.map((doc) => [doc.id, doc])
                        );
                        updatedDocs.forEach((doc) => {
                            docMap.set(doc.id, doc);
                        });
                        return Array.from(docMap.values());
                    });
                }
            } catch (err) {
                console.error("Polling error:", err);
            }
        };

        // Immediate poll
        pollDocuments();

        // Set up recurring polls every 2 seconds
        pollingIntervalRef.current = setInterval(pollDocuments, 2000);

        return () => {
            if (pollingIntervalRef.current) {
                clearInterval(pollingIntervalRef.current);
                pollingIntervalRef.current = null;
            }
        };
    }, [documents, currentGroup?.id]);

    // Cleanup on unmount
    useEffect(() => {
        return () => {
            if (pollingIntervalRef.current) {
                clearInterval(pollingIntervalRef.current);
            }
        };
    }, []);

    const handleCreateFolder = async (name: string) => {
        if (!currentGroup?.id) return;
        const newFolder = await foldersApi.createFolder(currentGroup.id, {
            name,
        });
        setFolders((prev) => [...prev, newFolder]);
        setFolderStats((prev) =>
            new Map(prev).set(newFolder.id, { document_count: 0 })
        );
    };

    const handleEditFolder = async (folderId: string, newName: string) => {
        if (!currentGroup?.id) return;
        const updated = await foldersApi.updateFolder(
            currentGroup.id,
            folderId,
            { name: newName }
        );
        setFolders((prev) =>
            prev.map((f) => (f.id === folderId ? updated : f))
        );
    };

    const handleDeleteFolder = async (folderId: string) => {
        if (!currentGroup?.id) return;
        if (!confirm("Delete this folder? Documents will be moved to root."))
            return;

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

        // Upload each file with folder_id (backend handles folder assignment atomically)
        await Promise.all(
            files.map(async (file) => {
                await documentsApi.uploadDocuments(
                    currentGroup.id,
                    [file],
                    undefined,
                    folderId
                );
            })
        );

        // Refresh documents to reflect folder assignments and counts
        const docsResponse = await documentsApi.listDocuments(
            currentGroup.id,
            1,
            100
        );
        setDocuments(docsResponse.documents);
    };

    const handleMoveDocument = async (folderId: string | null) => {
        if (!documentToMove || !currentGroup?.id) return;
        await documentsApi.moveDocumentToFolder(
            documentToMove.id,
            folderId,
            currentGroup.id
        );
        // Update the document in the list
        setDocuments((prev) =>
            prev.map((d) =>
                d.id === documentToMove.id
                    ? { ...d, folder_id: folderId ?? undefined }
                    : d
            )
        );
        setMoveModalOpen(false);
        setDocumentToMove(null);
    };

    const handleOpenMoveModal = (document: Document) => {
        setDocumentToMove(document);
        setMoveModalOpen(true);
    };

    const handleToggleSelection = (documentId: string) => {
        setSelectedDocumentIds((prev) =>
            prev.includes(documentId)
                ? prev.filter((id) => id !== documentId)
                : [...prev, documentId]
        );
    };

    const handleOpenReprocessModal = (document: Document) => {
        setDocumentToReprocess(document);
        setIsReprocessModalOpen(true);
    };

    const handleOpenBulkReprocessModal = () => {
        if (!selectedDocumentIds.length) return;
        const selectedDocs = documents.filter((d) =>
            selectedDocumentIds.includes(d.id)
        );
        const invalid = selectedDocs.filter(
            (d) => !["ready", "failed", "uploaded"].includes(d.status)
        );
        if (invalid.length > 0) {
            alert(
                "Bulk reprocess is only available for Ready, Failed, or Uploaded documents."
            );
            return;
        }
        if (selectedDocumentIds.length > 100) {
            alert("You can reprocess a maximum of 100 documents at once.");
            return;
        }
        setIsBulkReprocessModalOpen(true);
    };

    const handleReprocessDocument = async () => {
        if (!documentToReprocess || !currentGroup?.id) return;

        try {
            await documentsApi.reprocessDocument(
                currentGroup.id,
                documentToReprocess.id
            );

            // Update document status to processing
            setDocuments((prev) =>
                prev.map((d) =>
                    d.id === documentToReprocess.id
                        ? { ...d, status: "processing" }
                        : d
                )
            );

            setIsReprocessModalOpen(false);
            setDocumentToReprocess(null);
        } catch (err) {
            console.error("Failed to reprocess document:", err);
            alert(
                `Failed to reprocess document: ${
                    err instanceof Error ? err.message : "Unknown error"
                }`
            );
        }
    };

    const handleBulkReprocessDocuments = async () => {
        if (!currentGroup?.id || !selectedDocumentIds.length) return;

        try {
            await documentsApi.bulkReprocessDocuments(
                currentGroup.id,
                selectedDocumentIds
            );

            setDocuments((prev) =>
                prev.map((d) =>
                    selectedDocumentIds.includes(d.id)
                        ? { ...d, status: "processing" }
                        : d
                )
            );

            setSelectedDocumentIds([]);
            setIsBulkReprocessModalOpen(false);
        } catch (err) {
            console.error("Failed to bulk reprocess documents:", err);
            alert(
                `Failed to reprocess documents: ${
                    err instanceof Error ? err.message : "Unknown error"
                }`
            );
        }
    };

    const filteredDocuments = documents.filter((doc) => {
        const matchesFolder =
            selectedFolderId === null
                ? true // All Documents shows everything regardless of folder
                : doc.folder_id === selectedFolderId;
        const matchesSearch =
            !searchQuery ||
            doc.filename.toLowerCase().includes(searchQuery.toLowerCase());
        return matchesFolder && matchesSearch;
    });

    // Keep folder stats in sync when docs or folders change
    useEffect(() => {
        setFolderStats(buildFolderStats(folders, documents));
    }, [folders, documents, buildFolderStats]);

    if (!currentGroup) {
        return (
            <DashboardLayout>
                <div className="text-center py-12">
                    <p className="text-slate-600">
                        Please select a group first
                    </p>
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
                        <div className="flex items-center justify-between gap-4 flex-wrap">
                            <SearchBar
                                value={searchQuery}
                                onChange={setSearchQuery}
                                placeholder="Search documents..."
                                className="flex-1 min-w-[220px] max-w-md"
                            />
                            <div className="flex items-center gap-2 flex-wrap justify-end">
                                {selectedDocumentIds.length > 0 && (
                                    <>
                                        <span className="text-sm text-slate-600">
                                            {selectedDocumentIds.length}{" "}
                                            selected
                                        </span>
                                        <button
                                            onClick={
                                                handleOpenBulkReprocessModal
                                            }
                                            className="px-3 py-2 text-sm font-medium text-white bg-amber-600 hover:bg-amber-700 rounded-md transition-colors"
                                        >
                                            Reprocess Selected
                                        </button>
                                        <button
                                            onClick={() =>
                                                setSelectedDocumentIds([])
                                            }
                                            className="px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-100 rounded-md transition-colors"
                                        >
                                            Clear
                                        </button>
                                    </>
                                )}
                                <button
                                    onClick={() => setIsUploadModalOpen(true)}
                                    className="flex items-center gap-2 px-4 py-2 bg-emerald-600 text-white text-sm font-medium rounded-md hover:bg-emerald-700 transition-colors"
                                >
                                    <Upload size={18} />
                                    Upload Documents
                                </button>
                            </div>
                        </div>

                        {/* Document Grid */}
                        {isLoading ? (
                            <div className="text-center py-12 text-slate-500">
                                Loading documents...
                            </div>
                        ) : filteredDocuments.length === 0 ? (
                            <div className="bg-white border border-slate-200 rounded-lg p-12 text-center">
                                <FolderIcon
                                    size={48}
                                    className="text-slate-300 mx-auto mb-4"
                                />
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
                                {filteredDocuments.map((document) => {
                                    const folderName = document.folder_id
                                        ? folders.find(
                                              (f) => f.id === document.folder_id
                                          )?.name
                                        : undefined;

                                    return (
                                        <DocumentCard
                                            key={document.id}
                                            document={document}
                                            onView={() => {}}
                                            onDelete={async () => {
                                                await documentsApi.deleteDocument(
                                                    currentGroup.id,
                                                    document.id
                                                );
                                                setDocuments((prev) =>
                                                    prev.filter(
                                                        (d) =>
                                                            d.id !== document.id
                                                    )
                                                );
                                                setSelectedDocumentIds((prev) =>
                                                    prev.filter(
                                                        (id) =>
                                                            id !== document.id
                                                    )
                                                );
                                            }}
                                            onReprocess={
                                                handleOpenReprocessModal
                                            }
                                            onMove={handleOpenMoveModal}
                                            isSelected={selectedDocumentIds.includes(
                                                document.id
                                            )}
                                            onToggleSelection={
                                                handleToggleSelection
                                            }
                                            folderName={folderName}
                                        />
                                    );
                                })}
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

                {/* Move to Folder Modal */}
                <MoveToFolderModal
                    isOpen={moveModalOpen}
                    onClose={() => {
                        setMoveModalOpen(false);
                        setDocumentToMove(null);
                    }}
                    onMove={handleMoveDocument}
                    folders={folders}
                    documentName={documentToMove?.filename}
                    currentFolderId={documentToMove?.folder_id}
                />

                {/* Reprocess Modal */}
                <BulkReprocessModal
                    isOpen={isBulkReprocessModalOpen}
                    count={selectedDocumentIds.length}
                    onClose={() => setIsBulkReprocessModalOpen(false)}
                    onConfirm={handleBulkReprocessDocuments}
                />

                <ReprocessModal
                    isOpen={isReprocessModalOpen}
                    onClose={() => {
                        setIsReprocessModalOpen(false);
                        setDocumentToReprocess(null);
                    }}
                    onConfirm={handleReprocessDocument}
                    documentName={documentToReprocess?.filename}
                />
            </div>
        </DashboardLayout>
    );
}
