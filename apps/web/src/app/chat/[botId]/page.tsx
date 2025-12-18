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
            description: bot.welcome_message || `Ask ${bot.name} questions`,
        };
    } catch {
        return {
            title: "Bot Not Found | Veriply",
        };
    }
}

export default async function ChatPage({ params, searchParams }: PageProps) {
    const resolvedParams = await params;
    let botInfo;

    try {
        botInfo = await getBotPublicInfo(resolvedParams.botId);
    } catch {
        // Bot not found or not public
        notFound();
    }

    const embedded =
        (typeof searchParams?.embedded === "string" &&
            searchParams?.embedded === "true") ||
        (Array.isArray(searchParams?.embedded) &&
            searchParams?.embedded[0] === "true");

    return (
        <main
            className={
                embedded
                    ? "w-full h-full bg-transparent"
                    : "h-screen w-full flex items-center justify-center bg-slate-50"
            }
            style={embedded ? { height: "100%", width: "100%" } : undefined}
        >
            <ChatInterface
                botId={resolvedParams.botId}
                botName={botInfo.name}
                botAvatar={botInfo.avatar_url}
                welcomeMessage={botInfo.welcome_message}
                isPublic={botInfo.is_public}
                embedded={embedded}
            />
        </main>
    );
}
