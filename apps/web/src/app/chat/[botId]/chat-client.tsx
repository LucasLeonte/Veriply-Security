"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import ChatInterface from "@/components/chat/ChatInterface";
import { getBotPublicInfo } from "@/lib/api/chat";
import { BotPublicInfo } from "@/types/chat";
import { Loader2 } from "lucide-react";

interface ChatClientProps {
    botId: string;
    embedded?: boolean;
}

export default function ChatClient({
    botId,
    embedded = false,
}: ChatClientProps) {
    const [botInfo, setBotInfo] = useState<BotPublicInfo | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const router = useRouter();

    useEffect(() => {
        async function loadBot() {
            try {
                console.log(`[ChatClient] Loading bot ${botId}...`);
                const info = await getBotPublicInfo(botId);
                console.log(`[ChatClient] Bot loaded successfully:`, info);
                setBotInfo(info);
            } catch (err) {
                const errorMsg =
                    err instanceof Error ? err.message : "Failed to load bot";
                setError(errorMsg);
                console.error(
                    `[ChatClient] Failed to load bot ${botId}:`,
                    errorMsg,
                    err
                );
            } finally {
                setLoading(false);
            }
        }

        loadBot();
    }, [botId]);

    if (loading) {
        return (
            <div className="flex items-center justify-center h-screen">
                <div className="flex flex-col items-center gap-3">
                    <Loader2 className="h-8 w-8 animate-spin text-sky-500" />
                    <p className="text-slate-600">Loading bot...</p>
                </div>
            </div>
        );
    }

    if (error || !botInfo) {
        return (
            <div className="flex items-center justify-center h-screen">
                <div className="max-w-md w-full text-center p-8 bg-white rounded-xl shadow-lg border border-red-200">
                    <h1 className="text-xl font-semibold text-slate-900 mb-2">
                        Bot not available
                    </h1>
                    <p className="text-sm text-slate-600 mb-4">
                        {error || "Unable to load bot information"}
                    </p>
                    <button
                        onClick={() => router.push("/dashboard")}
                        className="px-4 py-2 bg-sky-500 text-white rounded-lg hover:bg-sky-600 transition"
                    >
                        Go to Dashboard
                    </button>
                </div>
            </div>
        );
    }

    return (
        <ChatInterface
            botId={botId}
            botName={botInfo.name}
            botAvatar={botInfo.avatar_url}
            description={botInfo.description}
            isPublic={botInfo.is_public}
            confidenceThreshold={botInfo.confidence_threshold}
            embedded={embedded}
            requirePublic={false}
        />
    );
}
