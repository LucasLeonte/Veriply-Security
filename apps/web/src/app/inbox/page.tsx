"use client";

import { useState, useEffect, useMemo } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { DashboardLayout } from "@/components";
import { ReviewQueue } from "@/components/hitl/ReviewQueue";
import { useHITLQueue, HITLQueueFilters } from "@/hooks/useHITLQueue";
import { useGroup } from "@/contexts/GroupContext";

export default function InboxPage() {
    const router = useRouter();
    const searchParams = useSearchParams();
    const { currentGroup } = useGroup();

    // Initialize state from URL params (AC 5.5: persistent filter state)
    const [sortBy, setSortBy] = useState<string>(
        searchParams.get("sort") || "oldest"
    );
    const [botId, setBotId] = useState<string | undefined>(
        searchParams.get("bot") || undefined
    );
    const [dateFrom, setDateFrom] = useState<string | undefined>(
        searchParams.get("from") || undefined
    );
    const [dateTo, setDateTo] = useState<string | undefined>(
        searchParams.get("to") || undefined
    );
    const [status, setStatus] = useState<"pending" | "in-progress" | undefined>(
        (searchParams.get("status") as "pending" | "in-progress") || undefined
    );

    // Memoize filters object to prevent unnecessary re-fetches
    const filters = useMemo(
        () => ({
            groupId: currentGroup?.id || undefined,
            botId,
            dateFrom,
            dateTo,
            status,
        }),
        [currentGroup?.id, botId, dateFrom, dateTo, status]
    );

    const { items, stats, isLoading, error, approveItem, rejectItem } =
        useHITLQueue(sortBy, filters);

    // Update URL when filters or sort change (AC 5.5)
    useEffect(() => {
        const params = new URLSearchParams();

        if (sortBy && sortBy !== "oldest") {
            params.set("sort", sortBy);
        }
        if (filters.botId) {
            params.set("bot", filters.botId);
        }
        if (filters.dateFrom) {
            params.set("from", filters.dateFrom);
        }
        if (filters.dateTo) {
            params.set("to", filters.dateTo);
        }
        if (filters.status) {
            params.set("status", filters.status);
        }

        const queryString = params.toString();
        const newUrl = queryString ? `/inbox?${queryString}` : "/inbox";

        // Update URL without page reload
        router.replace(newUrl, { scroll: false });
    }, [sortBy, filters, router]);

    if (error) {
        return (
            <DashboardLayout>
                <div className="space-y-6">
                    <h2 className="text-2xl font-semibold text-slate-900">
                        Review Queue
                    </h2>
                    <div className="bg-white rounded-lg border border-red-200 p-6 text-red-600">
                        <p>Error loading review queue: {error.message}</p>
                    </div>
                </div>
            </DashboardLayout>
        );
    }

    const handleFilterChange = (newFilters: Partial<HITLQueueFilters>) => {
        if (newFilters.botId !== undefined) setBotId(newFilters.botId);
        if (newFilters.dateFrom !== undefined) setDateFrom(newFilters.dateFrom);
        if (newFilters.dateTo !== undefined) setDateTo(newFilters.dateTo);
        if (newFilters.status !== undefined) setStatus(newFilters.status);
    };

    return (
        <DashboardLayout>
            <ReviewQueue
                items={items}
                stats={stats}
                isLoading={isLoading}
                onApprove={approveItem}
                onReject={rejectItem}
                sortBy={sortBy}
                onSortChange={setSortBy}
                onFilterChange={handleFilterChange}
            />
        </DashboardLayout>
    );
}
