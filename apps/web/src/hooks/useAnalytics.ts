import { useEffect, useState } from "react";

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

export function useAnalytics() {
    const [metrics, setMetrics] = useState<AnalyticsMetrics | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<Error | null>(null);

    useEffect(() => {
        const fetchMetrics = async () => {
            try {
                setIsLoading(true);
                setError(null);

                const response = await fetch(`/api/analytics/metrics`, {
                    method: "GET",
                    headers: {
                        "Content-Type": "application/json",
                    },
                });

                if (!response.ok) {
                    throw new Error(`Failed to fetch analytics: ${response.statusText}`);
                }

                const data: AnalyticsMetrics = await response.json();
                setMetrics(data);
            } catch (err) {
                setError(err instanceof Error ? err : new Error("Unknown error"));
                console.error("Failed to fetch analytics:", err);
            } finally {
                setIsLoading(false);
            }
        };

        fetchMetrics();
    }, []);

    return {
        metrics,
        isLoading,
        error,
    };
}
