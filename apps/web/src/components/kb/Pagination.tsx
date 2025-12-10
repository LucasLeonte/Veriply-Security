"use client";

import React from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";

interface PaginationProps {
    currentPage: number;
    totalPages: number;
    onPageChange: (page: number) => void;
    totalItems?: number;
    itemsPerPage?: number;
}

export function Pagination({
    currentPage,
    totalPages,
    onPageChange,
    totalItems,
    itemsPerPage,
}: PaginationProps) {
    const canGoPrevious = currentPage > 0;
    const canGoNext = currentPage < totalPages - 1;

    const getPageNumbers = () => {
        const pages: (number | string)[] = [];
        const maxVisible = 5;

        if (totalPages <= maxVisible) {
            // Show all pages if total is small
            for (let i = 0; i < totalPages; i++) {
                pages.push(i);
            }
        } else {
            // Show first, last, and pages around current
            pages.push(0);

            let start = Math.max(1, currentPage - 1);
            let end = Math.min(totalPages - 2, currentPage + 1);

            if (currentPage <= 2) {
                end = 3;
            } else if (currentPage >= totalPages - 3) {
                start = totalPages - 4;
            }

            if (start > 1) {
                pages.push("...");
            }

            for (let i = start; i <= end; i++) {
                pages.push(i);
            }

            if (end < totalPages - 2) {
                pages.push("...");
            }

            pages.push(totalPages - 1);
        }

        return pages;
    };

    if (totalPages <= 1) return null;

    const pages = getPageNumbers();

    return (
        <div className="flex items-center justify-between border-t border-slate-200 pt-4">
            {/* Info */}
            <div className="text-sm text-slate-600">
                {totalItems !== undefined && itemsPerPage !== undefined && (
                    <span>
                        Showing {currentPage * itemsPerPage + 1} -{" "}
                        {Math.min((currentPage + 1) * itemsPerPage, totalItems)} of{" "}
                        {totalItems}
                    </span>
                )}
            </div>

            {/* Pagination Controls */}
            <div className="flex items-center gap-1">
                {/* Previous Button */}
                <button
                    onClick={() => onPageChange(currentPage - 1)}
                    disabled={!canGoPrevious}
                    className="p-2 text-slate-700 border border-slate-300 rounded-md hover:bg-slate-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                    aria-label="Previous page"
                >
                    <ChevronLeft size={16} />
                </button>

                {/* Page Numbers */}
                {pages.map((page, index) => {
                    if (page === "...") {
                        return (
                            <span
                                key={`ellipsis-${index}`}
                                className="px-3 py-2 text-slate-600"
                            >
                                ...
                            </span>
                        );
                    }

                    const pageNumber = page as number;
                    const isActive = pageNumber === currentPage;

                    return (
                        <button
                            key={pageNumber}
                            onClick={() => onPageChange(pageNumber)}
                            className={`px-3 py-2 text-sm font-medium rounded-md transition-colors ${
                                isActive
                                    ? "bg-emerald-600 text-white"
                                    : "text-slate-700 hover:bg-slate-50 border border-slate-300"
                            }`}
                            aria-label={`Page ${pageNumber + 1}`}
                            aria-current={isActive ? "page" : undefined}
                        >
                            {pageNumber + 1}
                        </button>
                    );
                })}

                {/* Next Button */}
                <button
                    onClick={() => onPageChange(currentPage + 1)}
                    disabled={!canGoNext}
                    className="p-2 text-slate-700 border border-slate-300 rounded-md hover:bg-slate-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                    aria-label="Next page"
                >
                    <ChevronRight size={16} />
                </button>
            </div>
        </div>
    );
}
