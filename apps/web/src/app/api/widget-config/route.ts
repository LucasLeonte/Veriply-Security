import { NextRequest, NextResponse } from "next/server";

const API_BASE =
    process.env.NEXT_PUBLIC_API_URL ||
    process.env.API_URL ||
    "http://127.0.0.1:8000";

function buildTarget(groupId: string, botId: string): string {
    return `${API_BASE}/api/v1/groups/${groupId}/bots/${botId}/widget/config`;
}

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
    const { searchParams } = new URL(request.url);
    const groupId = searchParams.get("groupId");
    const botId = searchParams.get("botId");

    if (!groupId || !botId) {
        return NextResponse.json(
            { detail: "groupId and botId are required" },
            { status: 400 }
        );
    }

    const target = buildTarget(groupId, botId);
    const upstream = await fetch(target, {
        method: "GET",
        headers: forwardHeaders(request),
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
}

export async function PUT(request: NextRequest): Promise<NextResponse> {
    const { searchParams } = new URL(request.url);
    const groupId = searchParams.get("groupId");
    const botId = searchParams.get("botId");

    if (!groupId || !botId) {
        return NextResponse.json(
            { detail: "groupId and botId are required" },
            { status: 400 }
        );
    }

    try {
        const target = buildTarget(groupId, botId);
        const payload = await request.json();

        const upstream = await fetch(target, {
            method: "PUT",
            headers: forwardHeaders(request),
            body: JSON.stringify(payload),
            cache: "no-store",
        });

        const body = await upstream.text();

        if (!upstream.ok) {
            console.error(
                `Widget config save failed: ${upstream.status} ${upstream.statusText}`,
                body
            );
        }

        return new NextResponse(body, {
            status: upstream.status,
            headers: {
                "content-type":
                    upstream.headers.get("content-type") || "application/json",
            },
        });
    } catch (error) {
        console.error("Widget config PUT error:", error);
        return NextResponse.json(
            { detail: "Failed to save widget config" },
            { status: 500 }
        );
    }
}
