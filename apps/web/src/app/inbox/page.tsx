"use client";

import { useState } from "react";
import { DashboardLayout } from "@/components";
import { ReviewQueue } from "@/components/hitl/ReviewQueue";
import { useHITLQueue } from "@/hooks/useHITLQueue";

export default function InboxPage() {
    const [sortBy, setSortBy] = useState<string>("oldest");
    const { items, stats, isLoading, error, approveItem, rejectItem } =
        useHITLQueue(sortBy);

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
