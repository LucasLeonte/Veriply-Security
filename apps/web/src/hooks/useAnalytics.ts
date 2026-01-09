import { useEffect, useState } from "react";
import { getAccessToken } from "@/lib/auth";

export interface AnalyticsMetrics {
    totalQueries: number;
    autoResolved: number;
    autoResolvedPercent: number;
    avgResponseTime: number;
    trustScore: number;
    hitlInterventionRate: number;
    chartData: Array<{
        period: string;
        interventionRate: number;
    }>;
    rejectionReasons: Array<{
        reason: string;
        count: number;
        percent: number;
    }>;
    knowledgeGaps: Array<{
        question: string;
        askCount: number;
    }>;
}

export function useAnalytics(groupId?: string | null) {
    const [metrics, setMetrics] = useState<AnalyticsMetrics | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<Error | null>(null);

    useEffect(() => {
        const fetchMetrics = async () => {
            try {
                setIsLoading(true);
                setError(null);
                // Explicitly clear metrics when refetching with new groupId
                setMetrics(null);

                const token = getAccessToken();
                const headers: Record<string, string> = {
                    "Content-Type": "application/json",
                };

                if (token) {
                    headers["authorization"] = `Bearer ${token}`;
                }

                // Build URL with group_id if provided
                const apiBase =
                    process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";
                const params = new URLSearchParams();
                if (groupId) {
                    params.set("group_id", groupId);
                }
                const url = `${apiBase}/api/v1/analytics/metrics${
                    params.toString() ? `?${params.toString()}` : ""
                }`;

                const response = await fetch(url, {
                    method: "GET",
                    headers,
                    credentials: "include",
                });

                if (!response.ok) {
                    throw new Error(
                        `Failed to fetch analytics: ${response.statusText}`
                    );
                }

                const data: AnalyticsMetrics = await response.json();
                setMetrics(data);
            } catch (err) {
                setError(
                    err instanceof Error ? err : new Error("Unknown error")
                );
            } finally {
                setIsLoading(false);
            }
        };

        fetchMetrics();
    }, [groupId]);

    return {
        metrics,
        isLoading,
        error,
    };
}
