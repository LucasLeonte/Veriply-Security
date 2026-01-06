import { Metadata } from "next";
import { notFound } from "next/navigation";
import PublicChatClient from "./public-chat-client";
import { getBotPublicInfo } from "@/lib/api/chat";
import { headers } from "next/headers";

interface PageProps {
    params: {
        botId: string;
    };
    searchParams?: Record<string, string | string[] | undefined>;
}

export async function generateMetadata({
    params,
}: PageProps): Promise<Metadata> {
    const resolvedParams = await params;
    try {
        const incomingHeaders = headers();
        const embedOrigin =
            incomingHeaders.get("x-embed-origin") ||
            incomingHeaders.get("referer") ||
            incomingHeaders.get("origin") ||
            undefined;

        const bot = await getBotPublicInfo(resolvedParams.botId, embedOrigin);
        return {
            title: `Chat with ${bot.name} | Veriply`,
            description: bot.description || `Ask ${bot.name} questions`,
        };
    } catch {
        return {
            title: "Bot Not Found | Veriply",
        };
    }
}

// Mark this route as public - no authentication required
export const dynamic = "force-dynamic";

async function getWidgetConfig(
    botId: string,
    embedOrigin?: string
): Promise<{ primary_color: string } | null> {
    try {
        const headers = new Headers();
        headers.set("content-type", "application/json");
        if (embedOrigin) {
            headers.set("x-embed-origin", embedOrigin);
        }

        const response = await fetch(
            `${
                process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000"
            }/api/v1/bots/${botId}/widget/config`,
            { cache: "no-store", headers }
        );
        if (response.ok) {
            return await response.json();
        }
        if (response.status === 403) {
            throw new Error("domain_forbidden");
        }
    } catch (error) {
        if (
            error instanceof Error &&
            error.message &&
            error.message.includes("domain_forbidden")
        ) {
            throw error;
        }
        console.error("Failed to fetch widget config:", error);
    }
    return null;
}

export default async function PublicChatPage({
    params,
    searchParams,
}: PageProps) {
    const resolvedParams = await params;
    const resolvedSearchParams = await searchParams;
    const incomingHeaders = headers();
    const embedOrigin =
        incomingHeaders.get("x-embed-origin") ||
        incomingHeaders.get("referer") ||
        incomingHeaders.get("origin") ||
        (typeof resolvedSearchParams?.embed_origin === "string"
            ? resolvedSearchParams.embed_origin
            : Array.isArray(resolvedSearchParams?.embed_origin)
            ? resolvedSearchParams?.embed_origin[0]
            : undefined) ||
        undefined;

    let botInfo;
    let domainBlocked = false;

    try {
        botInfo = await getBotPublicInfo(resolvedParams.botId, embedOrigin);
    } catch (error) {
        const errorMsg =
            error instanceof Error ? error.message : "Unknown error";
        console.error(
            `[PublicChatPage] Failed to load public bot ${resolvedParams.botId}: ${errorMsg}`
        );
        const lowered = errorMsg.toLowerCase();
        if (lowered.includes("not authorized")) {
            domainBlocked = true;
        } else if (
            lowered.includes("not public") ||
            lowered.includes("not found")
        ) {
            notFound();
        } else {
            domainBlocked = true;
        }
    }

    const embedded =
        (typeof resolvedSearchParams?.embedded === "string" &&
            resolvedSearchParams?.embedded === "true") ||
        (Array.isArray(resolvedSearchParams?.embedded) &&
            resolvedSearchParams?.embedded[0] === "true");

    // Always fetch widget config for primary color in embedded mode
    let primaryColor = "#3B82F6";
    if (embedded && !domainBlocked) {
        try {
            const widgetConfig = await getWidgetConfig(
                resolvedParams.botId,
                embedOrigin
            );
            if (widgetConfig?.primary_color) {
                primaryColor = widgetConfig.primary_color;
            }
        } catch (err) {
            const msg = err instanceof Error ? err.message : "";
            if (msg.includes("domain_forbidden")) {
                domainBlocked = true;
            }
        }
    }

    if (domainBlocked) {
        return (
            <main className="h-screen w-full flex items-center justify-center bg-slate-50">
                <div className="max-w-md w-full text-center p-8 bg-white rounded-xl shadow-lg border border-amber-200">
                    <h1 className="text-xl font-semibold text-slate-900 mb-2">
                        This widget is not authorized for this domain
                    </h1>
                    <p className="text-sm text-slate-600">
                        If you own this bot, add this domain to your allowed
                        list in widget settings and try again.
                    </p>
                </div>
            </main>
        );
    }

    return (
        <main
            className={
                embedded
                    ? "w-full h-screen bg-transparent"
                    : "min-h-screen w-full flex items-center justify-center bg-slate-50"
            }
        >
            <PublicChatClient
                botId={resolvedParams.botId}
                botName={botInfo.name}
                botAvatar={botInfo.avatar_url}
                description={botInfo.description}
                isPublic={botInfo.is_public}
                confidenceThreshold={botInfo.confidence_threshold}
                bot={botInfo}
                embedded={embedded}
                primaryColor={primaryColor}
            />
        </main>
    );
}
