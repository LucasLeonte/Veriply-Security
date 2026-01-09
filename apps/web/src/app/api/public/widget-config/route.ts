import { NextRequest, NextResponse } from "next/server";

const API_BASE =
    process.env.NEXT_PUBLIC_API_URL ||
    process.env.API_URL ||
    "http://127.0.0.1:8000";

function buildTarget(botId: string): string {
    return `${API_BASE}/api/v1/bots/${botId}/widget/config`;
}

export async function GET(request: NextRequest): Promise<NextResponse> {
    const { searchParams } = new URL(request.url);
    const botId = searchParams.get("botId");
    const embedOrigin =
        request.headers.get("x-embed-origin") ||
        request.headers.get("referer") ||
        request.headers.get("origin");

    if (!botId) {
        return NextResponse.json(
            { detail: "botId is required" },
            { status: 400 }
        );
    }

    const target = buildTarget(botId);
    const headers = new Headers();
    headers.set("content-type", "application/json");
    if (embedOrigin) {
        headers.set("x-embed-origin", embedOrigin);
    }

    try {
        const upstream = await fetch(target, {
            method: "GET",
            headers,
            cache: "no-store",
        });

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
            { detail: "Failed to fetch widget config" },
            { status: 500 }
        );
    }
}
