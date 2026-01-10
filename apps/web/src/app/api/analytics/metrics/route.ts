import { NextRequest, NextResponse } from "next/server";

const API_BASE =
    process.env.NEXT_PUBLIC_API_URL ||
    process.env.API_URL ||
    "http://127.0.0.1:8000";

function forwardHeaders(request: NextRequest): Headers {
    const headers = new Headers();
    const cookie = request.headers.get("cookie");
    if (cookie) headers.set("cookie", cookie);
    const auth = request.headers.get("authorization");
    if (auth) headers.set("authorization", auth);
    headers.set("content-type", "application/json");
    return headers;
}

export async function GET(request: NextRequest): Promise<NextResponse> {
    try {
        const { searchParams } = new URL(request.url);
        const period = searchParams.get("period") || "7";

        const target = `${API_BASE}/api/v1/analytics/metrics?period=${period}`;
        const upstream = await fetch(target, {
            method: "GET",
            headers: forwardHeaders(request),
            cache: "no-store",
        });

        if (!upstream.ok) {
            const errorBody = await upstream.text();
            return NextResponse.json(
                { error: errorBody || "Failed to fetch analytics" },
                { status: upstream.status }
            );
        }

        const body = await upstream.text();
        return new NextResponse(body, {
            status: upstream.status,
            headers: {
                "content-type":
                    upstream.headers.get("content-type") || "application/json",
            },
        });
    } catch (error) {
        
        return NextResponse.json(
            { error: "Failed to fetch analytics" },
            { status: 502 }
        );
    }
}
