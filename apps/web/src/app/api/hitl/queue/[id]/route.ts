import { NextRequest, NextResponse } from "next/server";

export const dynamic = "force-dynamic";
export const revalidate = 0;

export async function GET(
    request: NextRequest,
    { params }: { params: Promise<{ id: string }> }
) {
    try {
        const apiBaseUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
        const authHeader = request.headers.get("Authorization");
        const { id: itemId } = await params;

        const headers: HeadersInit = {
            "Content-Type": "application/json",
        };
        if (authHeader) {
            headers.Authorization = authHeader;
        }

        const response = await fetch(`${apiBaseUrl}/api/v1/hitl/queue/${itemId}`, {
            method: "GET",
            headers,
            cache: "no-store",
        });

        if (!response.ok) {
            return NextResponse.json(
                { error: "Failed to fetch item detail" },
                {
                    status: response.status,
                    headers: {
                        "Cache-Control": "no-store, no-cache, must-revalidate, proxy-revalidate",
                        "Pragma": "no-cache",
                        "Expires": "0",
                    },
                }
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
        console.error("Error fetching HITL item:", error);
        return NextResponse.json(
            { error: "Failed to fetch item detail" },
            {
                status: 500,
                headers: {
                    "Cache-Control": "no-store, no-cache, must-revalidate, proxy-revalidate",
                    "Pragma": "no-cache",
                    "Expires": "0",
                },
            }
        );
    }
}
