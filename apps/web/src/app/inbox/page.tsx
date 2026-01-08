"use client";

import { useState, useEffect } from "react";
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
    const [filters, setFilters] = useState<HITLQueueFilters>({
        groupId: currentGroup?.id || undefined,
        botId: searchParams.get("bot") || undefined,
        dateFrom: searchParams.get("from") || undefined,
        dateTo: searchParams.get("to") || undefined,
        status:
            (searchParams.get("status") as "pending" | "in-progress") ||
            undefined,
    });

    const { items, stats, isLoading, error, approveItem, rejectItem } =
        useHITLQueue(sortBy, filters);

    // Update group filter when currentGroup changes (ensures group-scoped queue)
    useEffect(() => {
        setFilters((prev) => ({
            ...prev,
            groupId: currentGroup?.id || undefined,
        }));
    }, [currentGroup?.id]);

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
            />
        </DashboardLayout>
    );
}
