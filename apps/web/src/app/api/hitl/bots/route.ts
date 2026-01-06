import { NextRequest, NextResponse } from "next/server";

export async function GET(request: NextRequest) {
    try {
        const apiBaseUrl =
            process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
        const authHeader = request.headers.get("authorization");

        const headers: HeadersInit = {
            "Content-Type": "application/json",
        };

        if (authHeader) {
            headers.Authorization = authHeader;
        }

        const response = await fetch(`${apiBaseUrl}/api/v1/hitl/bots`, {
            method: "GET",
            headers,
        });

        if (!response.ok) {
            console.error(
                `Failed to fetch HITL bots from backend: ${response.status} ${response.statusText}`
            );
            return NextResponse.json({ bots: [] });
        }

        const data = await response.json();
        const bots = Array.isArray(data?.bots)
            ? data.bots
            : Array.isArray(data)
            ? data
            : [];

        return NextResponse.json({ bots });
    } catch (error) {
        console.error("Error fetching HITL bots:", error);
        return NextResponse.json({ bots: [] });
    }
}
