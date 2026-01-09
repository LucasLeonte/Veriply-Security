"use client";

import { DashboardLayout } from "@/components";
import { AnalyticsDashboard } from "@/components/analytics/AnalyticsDashboard";
import { useAnalytics } from "@/hooks/useAnalytics";
import { useGroup } from "@/contexts/GroupContext";

export default function AnalyticsPage() {
    const { currentGroup } = useGroup();
    const { metrics, isLoading, error } = useAnalytics(currentGroup?.id);

    if (error) {
        return (
            <DashboardLayout>
                <div className="space-y-6">
                    <h2 className="text-2xl font-semibold text-slate-900">
                        Analytics
                    </h2>
                    <div className="bg-white rounded-lg border border-red-200 p-6 text-red-600">
                        <p>Error loading analytics: {error.message}</p>
                    </div>
                </div>
            </DashboardLayout>
        );
    }

    return (
        <DashboardLayout>
            <AnalyticsDashboard metrics={metrics} isLoading={isLoading} />
        </DashboardLayout>
    );
}
