import { NextRequest, NextResponse } from "next/server";

export async function GET(request: NextRequest) {
    try {
        // Get the API base URL from environment or use default
        const apiBaseUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
        
        // Get auth token from Authorization header (forwarded from client)
        const authHeader = request.headers.get("Authorization");
        
        // Build headers with auth token if available
        const headers: HeadersInit = {
            "Content-Type": "application/json",
        };
        
        if (authHeader) {
            headers.Authorization = authHeader;
        }
        
        // Get query parameters from request URL
        const { searchParams } = new URL(request.url);
        const sortBy = searchParams.get('sort_by') || 'oldest';
        
        // Call the backend HITL endpoint with sort parameter
        const response = await fetch(`${apiBaseUrl}/api/v1/hitl/queue?sort_by=${sortBy}`, {
            method: "GET",
            headers,
        });

        if (!response.ok) {
            console.error(
                `Failed to fetch HITL queue from backend: ${response.status} ${response.statusText}`
            );
            
            // Return empty queue on error instead of 500
            return NextResponse.json({
                items: [],
                stats: {
                    total: 0,
                    pending: 0,
                    chat: 0,
                    email: 0,
                },
            });
        }

        const data = await response.json();

        return NextResponse.json({
            items: data.items || [],
            stats: data.stats || {
                total: 0,
                pending: 0,
                chat: 0,
                email: 0,
            },
        });
    } catch (error) {
        console.error("Error fetching HITL queue:", error);
        
        // Return empty queue on error instead of 500
        return NextResponse.json({
            items: [],
            stats: {
                total: 0,
                pending: 0,
                chat: 0,
                email: 0,
            },
        });
    }
}
