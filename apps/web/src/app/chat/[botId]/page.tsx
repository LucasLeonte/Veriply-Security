import { Metadata } from "next";
import { notFound } from "next/navigation";
import ChatInterface from "@/components/chat/ChatInterface";
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

export default async function ChatPage({ params, searchParams }: PageProps) {
    const resolvedParams = await params;
    const resolvedSearchParams = await searchParams;
    let botInfo;

    try {
        botInfo = await getBotPublicInfo(resolvedParams.botId);
    } catch (error) {
        const errorMsg =
            error instanceof Error ? error.message : "Unknown error";
        console.error(
            `[ChatPage] Failed to load public bot ${resolvedParams.botId}: ${errorMsg}`
        );
        // Bot not found or not public
        notFound();
    }

    const embedded =
        (typeof resolvedSearchParams?.embedded === "string" &&
            resolvedSearchParams?.embedded === "true") ||
        (Array.isArray(resolvedSearchParams?.embedded) &&
            resolvedSearchParams?.embedded[0] === "true");

    return (
        <main
            className={
                embedded
                    ? "w-full h-screen bg-transparent"
                    : "h-screen w-full flex items-center justify-center bg-slate-50"
            }
        >
            <ChatInterface
                botId={resolvedParams.botId}
                botName={botInfo.name}
                botAvatar={botInfo.avatar_url}
                description={botInfo.description}
                isPublic={botInfo.is_public}
                confidenceThreshold={botInfo.confidence_threshold}
                embedded={embedded}
            />
        </main>
    );
}
