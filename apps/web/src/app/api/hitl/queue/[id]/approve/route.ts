import { NextRequest, NextResponse } from "next/server";

export async function POST(
    request: NextRequest,
    { params }: { params: Promise<{ id: string }> }
) {
    try {
        const apiBaseUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
        const authHeader = request.headers.get("Authorization");

        const body = await request.json();
        const edits = body?.edits;
        const send_to_chat = body?.send_to_chat ?? true;
        const { id: itemId } = await params;

        const headers: HeadersInit = {
            "Content-Type": "application/json",
        };
        if (authHeader) {
            headers.Authorization = authHeader;
        }

        const response = await fetch(`${apiBaseUrl}/api/v1/hitl/queue/${itemId}/approve`, {
            method: "POST",
            headers,
            // Forward both edits and send_to_chat to the backend
            body: JSON.stringify({ edits, send_to_chat }),
            cache: "no-store",
        });

        if (!response.ok) {
            
            return NextResponse.json(
                { error: "Failed to approve item" },
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
        
        return NextResponse.json(
            { error: "Failed to approve item" },
            { status: 500 }
        );
    }
}
