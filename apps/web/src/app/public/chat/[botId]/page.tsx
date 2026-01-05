import { Metadata } from "next";
import { notFound } from "next/navigation";
import PublicChatClient from "./public-chat-client";
import { getBotPublicInfo } from "@/lib/api/chat";

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
        const bot = await getBotPublicInfo(resolvedParams.botId);
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
    botId: string
): Promise<{ primary_color: string } | null> {
    try {
        const response = await fetch(
            `${
                process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000"
            }/api/v1/bots/${botId}/widget/config`,
            { cache: "no-store" }
        );
        if (response.ok) {
            return await response.json();
        }
    } catch (error) {
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
    let botInfo;

    try {
        botInfo = await getBotPublicInfo(resolvedParams.botId);
    } catch (error) {
        const errorMsg =
            error instanceof Error ? error.message : "Unknown error";
        console.error(
            `[PublicChatPage] Failed to load public bot ${resolvedParams.botId}: ${errorMsg}`
        );
        // Bot not found or not public
        notFound();
    }

    const embedded =
        (typeof resolvedSearchParams?.embedded === "string" &&
            resolvedSearchParams?.embedded === "true") ||
        (Array.isArray(resolvedSearchParams?.embedded) &&
            resolvedSearchParams?.embedded[0] === "true");

    // Always fetch widget config for primary color in embedded mode
    let primaryColor = "#3B82F6";
    if (embedded) {
        const widgetConfig = await getWidgetConfig(resolvedParams.botId);
        if (widgetConfig?.primary_color) {
            primaryColor = widgetConfig.primary_color;
        }
    }

    return (
        <main
            className={
                embedded
                    ? "w-full h-screen bg-transparent"
                    : "h-screen w-full flex items-center justify-center bg-slate-50"
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
