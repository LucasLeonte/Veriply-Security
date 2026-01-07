import { NextRequest, NextResponse } from "next/server";

export async function POST(
    request: NextRequest,
    { params }: { params: Promise<{ id: string }> }
) {
    try {
        const apiBaseUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
        const authHeader = request.headers.get("Authorization");

        const { reason } = await request.json();
        const { id: itemId } = await params;

        const headers: HeadersInit = {
            "Content-Type": "application/json",
        };
        if (authHeader) {
            headers.Authorization = authHeader;
        }

        const response = await fetch(`${apiBaseUrl}/api/v1/hitl/queue/${itemId}/reject`, {
            method: "POST",
            headers,
            body: JSON.stringify({ reason }),
            cache: "no-store",
        });

        if (!response.ok) {
            console.error(`Failed to reject item: ${response.status} ${response.statusText}`);
            return NextResponse.json(
                { error: "Failed to reject item" },
                { status: response.status }
            );
        }

        const data = await response.json();
        return NextResponse.json(data, {
            headers: {
                "Cache-Control": "no-store, no-cache, must-revalidate, proxy-revalidate",
                "Pragma": "no-cache",
                "Expires": "0",
            },
        });
    } catch (error) {
        console.error("Error rejecting item:", error);
        return NextResponse.json(
            { error: "Failed to reject item" },
            { status: 500 }
        );
    }
}
