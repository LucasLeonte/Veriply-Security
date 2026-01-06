"use client";

import ChatInterface from "@/components/chat/ChatInterface";

interface PublicChatClientProps {
    botId: string;
    botName: string;
    botAvatar?: string;
    description?: string;
    isPublic: boolean;
    confidenceThreshold: number;
    bot: {
        name: string;
    } | null;
    embedded: boolean;
    primaryColor?: string;
}

export default function PublicChatClient({
    botId,
    botName,
    botAvatar,
    description,
    isPublic,
    confidenceThreshold,
    bot,
    embedded,
    primaryColor = "#3B82F6",
}: PublicChatClientProps) {
    const handleClose = () => {
        // Send message to parent window to close the iframe
        if (typeof window !== "undefined" && window.parent !== window) {
            window.parent.postMessage({ type: "veriply-widget-close" }, "*");
        }
    };

    // For embedded mode, show header with close button
    if (embedded && bot) {
        return (
            <div
                className="fixed flex flex-col"
                style={{
                    width: "100%",
                    height: "100%",
                    borderRadius: "12px",
                    overflow: "hidden",
                    background: "#fff",
                }}
            >
                {/* Custom Header */}
                <div
                    className="px-4 py-3 text-white text-sm font-semibold flex items-center justify-between flex-shrink-0"
                    style={{ background: primaryColor }}
                >
                    <span>Chat with {bot.name}</span>
                    <button
                        onClick={handleClose}
                        className="text-white hover:opacity-80 transition-opacity"
                        aria-label="Close chat"
                    >
                        ✕
                    </button>
                </div>
                {/* Chat Interface */}
                <div className="flex-1 overflow-hidden h-full">
                    <ChatInterface
                        botId={botId}
                        botName={botName}
                        botAvatar={botAvatar}
                        description={description}
                        isPublic={isPublic}
                        confidenceThreshold={confidenceThreshold}
                        embedded={true}
                    />
                </div>
            </div>
        );
    }

    // For non-embedded mode, show full page
    return (
        <ChatInterface
            botId={botId}
            botName={botName}
            botAvatar={botAvatar}
            description={description}
            isPublic={isPublic}
            confidenceThreshold={confidenceThreshold}
            embedded={embedded}
        />
    );
}
