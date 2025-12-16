import { NextResponse } from "next/server";

export async function GET() {
    try {
        // In production, add authentication check here

        // Mock analytics data - in production this would come from your database
        const mockMetrics = {
            totalQueries: 2847,
            autoResolved: 1935,
            autoResolvedPercent: 68,
            avgResponseTime: 1.2,
            trustScore: 97,
            hitlInterventionRate: 32,
            chartData: [
                { period: "Mon", interventionRate: 80 },
                { period: "Tue", interventionRate: 72 },
                { period: "Wed", interventionRate: 65 },
                { period: "Thu", interventionRate: 50 },
                { period: "Fri", interventionRate: 40 },
                { period: "Sat", interventionRate: 35 },
                { period: "Sun", interventionRate: 22 },
            ],
            rejectionReasons: [
                {
                    reason: "Hallucination detected",
                    count: 15,
                    percent: 45,
                },
                {
                    reason: "Incomplete answer",
                    count: 8,
                    percent: 25,
                },
                {
                    reason: "Tone mismatch",
                    count: 6,
                    percent: 20,
                },
                {
                    reason: "Missing citations",
                    count: 4,
                    percent: 10,
                },
            ],
            knowledgeGaps: [
                {
                    question: "Do you offer student discounts?",
                    askCount: 12,
                },
                {
                    question: "What integrations do you support?",
                    askCount: 8,
                },
                {
                    question: "Is there a mobile app?",
                    askCount: 6,
                },
            ],
        };

        // In production, fetch real data from database filtered by tenant
        return NextResponse.json(mockMetrics);
    } catch (error) {
        console.error("Error fetching analytics:", error);
        return NextResponse.json(
            { error: "Failed to fetch analytics" },
            { status: 500 }
        );
    }
}
