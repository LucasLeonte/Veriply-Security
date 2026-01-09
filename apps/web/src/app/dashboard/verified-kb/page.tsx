"use client";

import { DashboardLayout } from "@/components";
import { useGroup } from "@/contexts/GroupContext";
import { useState, useEffect, useCallback, useRef } from "react";
import { Search, Edit2, Trash2, Calendar, User } from "lucide-react";
import type { VerifiedQA, VerifiedQAListResponse } from "@/types/verified-qa";
import { EditDialog } from "@/components/verified-kb/EditDialog";
import { DeleteConfirmationDialog } from "@/components/verified-kb/DeleteConfirmationDialog";
import { Pagination } from "@/components/verified-kb/Pagination";

export default function VerifiedKBPage() {
    const { currentGroup } = useGroup();
    const [entries, setEntries] = useState<VerifiedQA[]>([]);
    const [isLoading, setIsLoading] = useState(false);
    const [searchQuery, setSearchQuery] = useState("");
    const [debouncedSearchQuery, setDebouncedSearchQuery] = useState("");
    const [currentPage, setCurrentPage] = useState(1);
    const [totalPages, setTotalPages] = useState(1);
    const [totalCount, setTotalCount] = useState(0);
    const [fromDate, setFromDate] = useState<string>("");
    const [toDate, setToDate] = useState<string>("");
    const [creatorFilter, setCreatorFilter] = useState<string>("");
    const [selectedEntry, setSelectedEntry] = useState<VerifiedQA | null>(null);
    const [isEditDialogOpen, setIsEditDialogOpen] = useState(false);
    const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false);
    const [entryToDelete, setEntryToDelete] = useState<VerifiedQA | null>(null);
    const lastFiltersRef = useRef<string>("");
    const abortControllerRef = useRef<AbortController | null>(null);

    const PAGE_SIZE = 20;

    const fetchEntries = useCallback(async () => {
        if (!currentGroup?.id) return;

        const filtersHash = JSON.stringify({ searchQuery: debouncedSearchQuery, fromDate, toDate, creatorFilter });
        const filtersChanged = filtersHash !== lastFiltersRef.current;

        if (filtersChanged && currentPage !== 1) {
            setCurrentPage(1);
            return;
        }

        lastFiltersRef.current = filtersHash;

        abortControllerRef.current?.abort();
        const controller = new AbortController();
        abortControllerRef.current = controller;

        setIsLoading(true);
        try {
            const params = new URLSearchParams({
                group_id: currentGroup.id,
                page: currentPage.toString(),
                limit: PAGE_SIZE.toString(),
            });

            if (debouncedSearchQuery) params.append("search", debouncedSearchQuery);
            if (creatorFilter) params.append("creator_id", creatorFilter);
            if (fromDate) params.append("from_date", fromDate);
            if (toDate) params.append("to_date", toDate);

            const response = await fetch(`/api/v1/verified-qa/search?${params}`, {
                method: "GET",
                credentials: "include",
                signal: controller.signal,
            });

            if (!response.ok) {
                throw new Error("Failed to fetch entries");
            }

            const data: VerifiedQAListResponse = await response.json();
            const normalizedTotalPages = Math.max(1, data.total_pages || 0);
            const nextPage = Math.min(currentPage, normalizedTotalPages);

            if (nextPage !== currentPage) {
                setCurrentPage(nextPage);
                return;
            }

            if (controller.signal.aborted) return;

            setEntries(data.items);
            setTotalCount(data.total);
            setTotalPages(normalizedTotalPages);
        } catch (error) {
            if (error instanceof DOMException && error.name === "AbortError") return;
            console.error("Error fetching verified KB entries:", error);
        } finally {
            if (!controller.signal.aborted) {
                setIsLoading(false);
            }
        }
    }, [currentGroup?.id, currentPage, debouncedSearchQuery, fromDate, toDate, creatorFilter]);

    useEffect(() => {
        fetchEntries();
    }, [fetchEntries]);

    // Debounce search input
    useEffect(() => {
        const t = setTimeout(() => setDebouncedSearchQuery(searchQuery.trim()), 300);
        return () => clearTimeout(t);
    }, [searchQuery]);

    useEffect(() => {
        return () => abortControllerRef.current?.abort();
    }, []);

    const handleEditClick = (entry: VerifiedQA) => {
        setSelectedEntry(entry);
        setIsEditDialogOpen(true);
    };

    const handleDeleteClick = (entry: VerifiedQA) => {
        setEntryToDelete(entry);
        setIsDeleteDialogOpen(true);
    };

    const handleEditSave = async (updatedEntry: VerifiedQA) => {
        if (!currentGroup?.id || !selectedEntry) return;

        const prevEntries = entries;
        // Optimistic update
        setEntries((curr) => curr.map((e) => (e.id === selectedEntry.id ? { ...e, ...updatedEntry } : e)));

        try {
            const response = await fetch(
                `/api/v1/verified-qa/${selectedEntry.id}?group_id=${currentGroup.id}`,
                {
                    method: "PUT",
                    credentials: "include",
                    headers: {
                        "Content-Type": "application/json",
                    },
                    body: JSON.stringify({
                        question_text: updatedEntry.question_text,
                        answer_text: updatedEntry.answer_text,
                        source_citations: updatedEntry.source_citations,
                    }),
                }
            );

            if (!response.ok) {
                throw new Error("Failed to update entry");
            }

            setIsEditDialogOpen(false);
            setSelectedEntry(null);
            await fetchEntries();
        } catch (error) {
            console.error("Error updating entry:", error);
            // Rollback optimistic update
            setEntries(prevEntries);
        }
    };

    const handleDeleteConfirm = async () => {
        if (!currentGroup?.id || !entryToDelete) return;

        try {
            const response = await fetch(
                `/api/v1/verified-qa/${entryToDelete.id}?group_id=${currentGroup.id}`,
                {
                    method: "DELETE",
                    credentials: "include",
                }
            );

            if (!response.ok) {
                throw new Error("Failed to delete entry");
            }

            setIsDeleteDialogOpen(false);
            setEntryToDelete(null);
            await fetchEntries();
        } catch (error) {
            console.error("Error deleting entry:", error);
        }
    };

    const truncateText = (text: string, maxLength: number) => {
        if (text.length > maxLength) {
            return text.substring(0, maxLength) + "...";
        }
        return text;
    };

    const formatDate = (dateString: string) => {
        return new Date(dateString).toLocaleDateString("en-US", {
            year: "numeric",
            month: "short",
            day: "numeric",
        });
    };

    return (
        <DashboardLayout>
            <div className="space-y-6">
                {/* Header */}
                <div className="flex justify-between items-center">
                    <h1 className="text-3xl font-bold">Verified Knowledge Base</h1>
                </div>

                {/* Search and Filters */}
                <div className="bg-white rounded-lg shadow p-6 space-y-4">
                    <div className="flex gap-4">
                        <div className="flex-1 relative">
                            <Search className="absolute left-3 top-3 text-gray-400" size={20} />
                            <input
                                type="text"
                                placeholder="Search by question or answer..."
                                value={searchQuery}
                                onChange={(e) => setSearchQuery(e.target.value)}
                                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                            />
                        </div>
                    </div>

                    {/* Advanced Filters */}
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">
                                From Date
                            </label>
                            <input
                                type="date"
                                value={fromDate}
                                onChange={(e) => setFromDate(e.target.value)}
                                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                            />
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">
                                To Date
                            </label>
                            <input
                                type="date"
                                value={toDate}
                                onChange={(e) => setToDate(e.target.value)}
                                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                            />
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">
                                Creator (User ID)
                            </label>
                            <input
                                type="text"
                                value={creatorFilter}
                                onChange={(e) => setCreatorFilter(e.target.value)}
                                placeholder="Filter by creator UUID"
                                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                            />
                        </div>
                    </div>
                </div>

                {/* Entries List */}
                <div className="bg-white rounded-lg shadow overflow-hidden">
                    {isLoading ? (
                        <div className="p-6 text-center">
                            <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500" />
                            <p className="mt-2 text-gray-600">Loading entries...</p>
                        </div>
                    ) : entries.length === 0 ? (
                        <div className="p-6 text-center">
                            <p className="text-gray-600">No entries found</p>
                        </div>
                    ) : (
                        <>
                            <div className="overflow-x-auto">
                                <table className="w-full">
                                    <thead className="bg-gray-50 border-b border-gray-200">
                                        <tr>
                                            <th className="px-6 py-3 text-left text-sm font-semibold text-gray-700">
                                                Question
                                            </th>
                                            <th className="px-6 py-3 text-left text-sm font-semibold text-gray-700">
                                                Answer
                                            </th>
                                            <th className="px-6 py-3 text-left text-sm font-semibold text-gray-700">
                                                Created
                                            </th>
                                            <th className="px-6 py-3 text-left text-sm font-semibold text-gray-700">
                                                Actions
                                            </th>
                                        </tr>
                                    </thead>
                                    <tbody className="divide-y divide-gray-200">
                                        {entries.map((entry) => (
                                            <tr key={entry.id} className="hover:bg-gray-50 transition">
                                                <td className="px-6 py-4">
                                                    <p className="text-sm font-medium text-gray-900">
                                                        {truncateText(entry.question_text, 60)}
                                                    </p>
                                                </td>
                                                <td className="px-6 py-4">
                                                    <p className="text-sm text-gray-600">
                                                        {truncateText(entry.answer_text, 80)}
                                                    </p>
                                                </td>
                                                <td className="px-6 py-4">
                                                    <div className="flex items-center gap-3 text-sm text-gray-600">
                                                        <div className="flex items-center gap-2">
                                                            <Calendar size={16} />
                                                            {formatDate(entry.created_at)}
                                                        </div>
                                                        <div className="flex items-center gap-2">
                                                            <User size={16} />
                                                            <span title={entry.approved_by_user_id || "Unknown"}>
                                                                {entry.approved_by_user_id ? String(entry.approved_by_user_id).slice(0, 8) : "Unknown"}
                                                            </span>
                                                        </div>
                                                    </div>
                                                </td>
                                                <td className="px-6 py-4">
                                                    <div className="flex gap-2">
                                                        <button
                                                            onClick={() => handleEditClick(entry)}
                                                            className="inline-flex items-center gap-1 px-3 py-1 bg-blue-100 text-blue-700 rounded hover:bg-blue-200 transition"
                                                        >
                                                            <Edit2 size={16} />
                                                            Edit
                                                        </button>
                                                        <button
                                                            onClick={() => handleDeleteClick(entry)}
                                                            className="inline-flex items-center gap-1 px-3 py-1 bg-red-100 text-red-700 rounded hover:bg-red-200 transition"
                                                        >
                                                            <Trash2 size={16} />
                                                            Delete
                                                        </button>
                                                    </div>
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>

                            {/* Pagination */}
                            <Pagination
                                currentPage={currentPage}
                                totalPages={totalPages}
                                totalCount={totalCount}
                                pageSize={PAGE_SIZE}
                                onPageChange={setCurrentPage}
                            />
                        </>
                    )}
                </div>
            </div>

            {/* Dialogs */}
            {isEditDialogOpen && selectedEntry && (
                <EditDialog
                    entry={selectedEntry}
                    onSave={handleEditSave}
                    onClose={() => {
                        setIsEditDialogOpen(false);
                        setSelectedEntry(null);
                    }}
                />
            )}

            {isDeleteDialogOpen && entryToDelete && (
                <DeleteConfirmationDialog
                    entry={entryToDelete}
                    onConfirm={handleDeleteConfirm}
                    onCancel={() => {
                        setIsDeleteDialogOpen(false);
                        setEntryToDelete(null);
                    }}
                />
            )}
        </DashboardLayout>
    );
}
