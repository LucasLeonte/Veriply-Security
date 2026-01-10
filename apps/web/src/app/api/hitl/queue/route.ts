import { NextRequest, NextResponse } from "next/server";

// Ensure this route is always dynamic and never cached
export const dynamic = "force-dynamic";
export const revalidate = 0;

export async function GET(request: NextRequest) {
    try {
        // Get the API base URL from environment or use default
        const apiBaseUrl =
            process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

        // Get auth token from Authorization header (forwarded from client)
        const authHeader = request.headers.get("Authorization");

        // Build headers with auth token if available
        const headers: HeadersInit = {
            "Content-Type": "application/json",
        };

        if (authHeader) {
            headers.Authorization = authHeader;
        }

        // Get query parameters from request URL and forward them to backend
        const { searchParams } = new URL(request.url);
        const groupId = searchParams.get("group_id");
        const sortBy = searchParams.get("sort_by") || "oldest";
        const botId = searchParams.get("bot_id");
        const dateFrom = searchParams.get("date_from");
        const dateTo = searchParams.get("date_to");
        const statusFilter = searchParams.get("status_filter");

        const backendParams = new URLSearchParams({ sort_by: sortBy });
        if (groupId) backendParams.set("group_id", groupId);
        if (botId) backendParams.set("bot_id", botId);
        if (dateFrom) backendParams.set("date_from", dateFrom);
        if (dateTo) backendParams.set("date_to", dateTo);
        if (statusFilter) backendParams.set("status_filter", statusFilter);

        // Call the backend HITL endpoint with all params and disable caching
        const response = await fetch(
            `${apiBaseUrl}/api/v1/hitl/queue?${backendParams.toString()}`,
            {
                method: "GET",
                headers,
                cache: "no-store",
            }
        );

        if (!response.ok) {

            // Return empty queue on error instead of 500
            return NextResponse.json(
                {
                    items: [],
                    stats: {
                        total: 0,
                        pending: 0,
                        chat: 0,
                        email: 0,
                    },
                },
                {
                    headers: {
                        "Cache-Control":
                            "no-store, no-cache, must-revalidate, proxy-revalidate",
                        Pragma: "no-cache",
                        Expires: "0",
                    },
                }
            );
        }

        const data = await response.json();

        return NextResponse.json(
            {
                items: data.items || [],
                stats: data.stats || {
                    total: 0,
                    pending: 0,
                    chat: 0,
                    email: 0,
                },
            },
            {
                headers: {
                    "Cache-Control":
                        "no-store, no-cache, must-revalidate, proxy-revalidate",
                    Pragma: "no-cache",
                    Expires: "0",
                },
            }
        );
    } catch (error) {

        // Return empty queue on error instead of 500
        return NextResponse.json(
            {
                items: [],
                stats: {
                    total: 0,
                    pending: 0,
                    chat: 0,
                    email: 0,
                },
            },
            {
                headers: {
                    "Cache-Control":
                        "no-store, no-cache, must-revalidate, proxy-revalidate",
                    Pragma: "no-cache",
                    Expires: "0",
                },
            }
        );
    }
}
