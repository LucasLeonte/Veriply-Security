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
    const canGoPrevious = currentPage > 1;
    const canGoNext = currentPage < totalPages;

    const getPageNumbers = () => {
        const pages: (number | string)[] = [];
        const maxVisible = 5;

        if (totalPages <= maxVisible) {
            // Show all pages if total is small
            for (let i = 1; i <= totalPages; i++) {
                pages.push(i);
            }
        } else {
            // Show first, last, and pages around current
            pages.push(1);

            let start = Math.max(2, currentPage - 1);
            let end = Math.min(totalPages - 1, currentPage + 1);

            if (currentPage <= 3) {
                end = 4;
            } else if (currentPage >= totalPages - 2) {
                start = totalPages - 3;
            }

            if (start > 2) {
                pages.push("...");
            }

            for (let i = start; i <= end; i++) {
                pages.push(i);
            }

            if (end < totalPages - 1) {
                pages.push("...");
            }

            pages.push(totalPages);
        }

        return pages;
    };

    if (totalPages <= 1) return null;

    const pages = getPageNumbers();

    return (
        <nav 
            className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border-t border-slate-200 pt-4" 
            role="navigation"
            aria-label="Pagination"
        >
            {/* Info */}
            <div className="text-sm text-slate-600 order-2 sm:order-1 w-full sm:w-auto" aria-live="polite" aria-atomic="true">
                {totalItems !== undefined && itemsPerPage !== undefined && (
                    <span>
                        Showing {(currentPage - 1) * itemsPerPage + 1} -{" "}
                        {Math.min(currentPage * itemsPerPage, totalItems)} of{" "}
                        {totalItems}
                    </span>
                )}
            </div>

            {/* Pagination Controls */}
            <div className="flex items-center gap-1 order-1 sm:order-2 w-full sm:w-auto overflow-x-auto pb-2 sm:pb-0">\n                {/* Previous Button */}
                {/* Previous Button */}
                <button
                    onClick={() => onPageChange(currentPage - 1)}
                    disabled={!canGoPrevious}
                    className="p-2 min-w-[44px] min-h-[44px] flex items-center justify-center text-slate-700 border border-slate-300 rounded-md hover:bg-slate-50 focus:outline-none focus:ring-2 focus:ring-emerald-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                    aria-label="Previous page"
                >
                    <ChevronLeft size={16} aria-hidden="true" />
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
                            className={`px-3 py-2 min-h-[44px] text-sm font-medium rounded-md focus:outline-none focus:ring-2 focus:ring-emerald-500 transition-colors ${
                                isActive
                                    ? "bg-emerald-600 text-white"
                                    : "text-slate-700 hover:bg-slate-50 border border-slate-300"
                            }`}
                            aria-label={`Page ${pageNumber}`}
                            aria-current={isActive ? "page" : undefined}
                        >
                            {pageNumber}
                        </button>
                    );
                })}

                {/* Next Button */}
                <button
                    onClick={() => onPageChange(currentPage + 1)}
                    disabled={!canGoNext}
                    className="p-2 min-w-[44px] min-h-[44px] flex items-center justify-center text-slate-700 border border-slate-300 rounded-md hover:bg-slate-50 focus:outline-none focus:ring-2 focus:ring-emerald-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                    aria-label="Next page"
                >
                    <ChevronRight size={16} aria-hidden="true" />
                </button>
            </div>
        </nav>
    );
}
