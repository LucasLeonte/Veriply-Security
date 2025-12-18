import { NextResponse } from "next/server";

// Mock data - in production this would come from your database
const mockQueueItems = [
    {
        id: "1",
        type: "chat" as const,
        timestamp: new Date(Date.now() - 5 * 60000).toISOString(),
        userQuestion: "What are your pricing options?",
        aiDraft:
            "We offer three pricing tiers: Basic ($29/month), Professional ($79/month), and Enterprise (custom pricing). Each tier includes...",
        confidence: 0.92,
        citations: [
            { source: "Pricing Page - Basic Plan", relevance: 0.95 },
            { source: "Pricing Page - Professional Plan", relevance: 0.93 },
        ],
        status: "pending" as const,
        source: "website_chat",
    },
    {
        id: "2",
        type: "email" as const,
        timestamp: new Date(Date.now() - 15 * 60000).toISOString(),
        userQuestion: "Do you offer API access?",
        aiDraft:
            "Yes, we provide comprehensive API documentation and access for our Professional and Enterprise plans. Our API allows you to integrate...",
        confidence: 0.87,
        citations: [
            { source: "API Documentation", relevance: 0.98 },
            { source: "Pricing - Professional Features", relevance: 0.85 },
        ],
        status: "pending" as const,
        source: "email",
    },
    {
        id: "3",
        type: "chat" as const,
        timestamp: new Date(Date.now() - 30 * 60000).toISOString(),
        userQuestion: "How do I get started with a trial?",
        aiDraft:
            "You can start a free 14-day trial directly from our website. No credit card required. Simply click 'Start Free Trial' on the homepage...",
        confidence: 0.78,
        citations: [
            { source: "Trial Information", relevance: 0.92 },
            { source: "Getting Started Guide", relevance: 0.80 },
        ],
        status: "pending" as const,
        source: "website_chat",
    },
];

export async function GET() {
    try {
        // In production, add authentication check here
        const pendingItems = mockQueueItems.filter(
            (item) => item.status === "pending"
        );

        const stats = {
            total: mockQueueItems.length,
            pending: pendingItems.length,
            chat: mockQueueItems.filter((item) => item.type === "chat").length,
            email: mockQueueItems.filter((item) => item.type === "email")
                .length,
        };

        return NextResponse.json({
            items: pendingItems,
            stats,
        });
    } catch (error) {
        console.error("Error fetching HITL queue:", error);
        return NextResponse.json(
            { error: "Failed to fetch queue" },
            { status: 500 }
        );
    }
}
