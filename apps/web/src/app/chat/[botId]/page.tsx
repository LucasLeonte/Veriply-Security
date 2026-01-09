import { Metadata } from "next";
import ChatClient from "./chat-client";

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
    return {
        title: `Chat | Veriply`,
        description: `Chat with your bot`,
    };
}

export default async function ChatPage({ params, searchParams }: PageProps) {
    const resolvedParams = await params;
    const resolvedSearchParams = await searchParams;

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
            <ChatClient botId={resolvedParams.botId} embedded={embedded} />
        </main>
    );
}
