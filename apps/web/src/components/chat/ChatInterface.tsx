"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { Send, Loader2, RefreshCw } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { useChat } from "@/hooks/useChat";
import MessageList from "./MessageList";
import { fetchChatHistory } from "@/lib/api/chatHistory";
import { ChatHistoryEntry } from "@/types/chat";

interface ChatInterfaceProps {
    botId: string;
    botName: string;
    botAvatar?: string;
    welcomeMessage: string;
    isPublic: boolean;
}

export default function ChatInterface({
    botId,
    botName,
    botAvatar,
    welcomeMessage,
    isPublic,
}: ChatInterfaceProps) {
    const [input, setInput] = useState("");
    const {
        messages,
        loading,
        streaming,
        error,
        sendMessage,
        clearHistory,
        retryLastMessage,
        feedbackState,
        feedbackError,
        submitFeedbackForMessage,
    } = useChat(botId);
    const textareaRef = useRef<HTMLTextAreaElement>(null);
    const [activeTab, setActiveTab] = useState<"chat" | "history">("chat");
    const [historyEntries, setHistoryEntries] = useState<ChatHistoryEntry[]>([]);
    const [historyLoading, setHistoryLoading] = useState(false);
    const [historyError, setHistoryError] = useState<string | null>(null);
    const [historySessionFilter, setHistorySessionFilter] = useState("");

    // Auto-focus input on mount
    useEffect(() => {
        textareaRef.current?.focus();
    }, []);

    // Auto-resize textarea
    useEffect(() => {
        if (textareaRef.current) {
            textareaRef.current.style.height = "auto";
            textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
        }
    }, [input]);

    const loadHistory = useCallback(
        async (sessionId?: string) => {
            setHistoryLoading(true);
            setHistoryError(null);
            try {
                const entries = await fetchChatHistory(botId, {
                    sessionId: sessionId || undefined,
                    limit: 200,
                });
                setHistoryEntries(entries);
            } catch (err: any) {
                const status = err?.status as number | undefined;
                const message =
                    status === 401
                        ? "Please log in as an owner/admin to view history"
                        : err?.message || "Failed to load history";
                setHistoryError(message);
            } finally {
                setHistoryLoading(false);
            }
        },
        [botId]
    );

    useEffect(() => {
        if (activeTab === "history") {
            loadHistory(historySessionFilter || undefined);
        }
    }, [activeTab, loadHistory]);

    const handleSend = async () => {
        if (!input.trim() || loading) return;

        const query = input.trim();
        setInput("");
        await sendMessage(query);

        // Reset textarea height
        if (textareaRef.current) {
            textareaRef.current.style.height = "auto";
        }
    };

    const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    };

    if (!isPublic) {
        return (
            <Card className="w-full max-w-2xl p-8 text-center">
                <h2 className="text-xl font-semibold text-slate-900 mb-2">
                    This bot is not available
                </h2>
                <p className="text-slate-600">
                    The bot owner has not made this bot public yet.
                </p>
            </Card>
        );
    }

    return (
        <Card className="w-full max-w-4xl h-[90vh] flex flex-col shadow-lg">
            {/* Header */}
            <div className="flex items-center justify-between p-4 border-b border-slate-200">
                <div className="flex items-center gap-3">
                    <Avatar className="h-10 w-10">
                        <AvatarImage src={botAvatar} alt={botName} />
                        <AvatarFallback className="bg-sky-500 text-white">
                            {botName.charAt(0).toUpperCase()}
                        </AvatarFallback>
                    </Avatar>
                    <div>
                        <h1 className="font-semibold text-slate-900">
                            {botName}
                        </h1>
                        <p className="text-xs text-slate-500">
                            {streaming
                                ? "Typing..."
                                : loading
                                ? "Thinking..."
                                : "Online"}
                        </p>
                    </div>
                </div>
                <div className="flex items-center gap-2">
                    <span className={`text-[10px] px-2 py-1 rounded-full border ${isPublic ? "bg-emerald-50 text-emerald-700 border-emerald-200" : "bg-slate-100 text-slate-600 border-slate-200"}`}>
                        {isPublic ? "Public" : "Private"}
                    </span>
                    <div className="flex items-center gap-1">
                        <Button
                            variant={activeTab === "chat" ? "default" : "ghost"}
                            size="sm"
                            onClick={() => setActiveTab("chat")}
                        >
                            Chat
                        </Button>
                        <Button
                            variant={activeTab === "history" ? "secondary" : "ghost"}
                            size="sm"
                            onClick={() => setActiveTab("history")}
                        >
                            History
                        </Button>
                    </div>
                    <Button
                        variant="ghost"
                        size="sm"
                        onClick={clearHistory}
                        disabled={activeTab !== "chat" || messages.length === 0 || loading}
                        title="Start new conversation"
                    >
                        <RefreshCw className="h-4 w-4" />
                    </Button>
                </div>
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-4">
                {activeTab === "chat" ? (
                    <>
                        {messages.length === 0 ? (
                            <div className="flex flex-col items-center justify-center h-full text-center px-6">
                                <Avatar className="h-16 w-16 mb-4">
                                    <AvatarImage src={botAvatar} alt={botName} />
                                    <AvatarFallback className="bg-sky-500 text-white text-2xl">
                                        {botName.charAt(0).toUpperCase()}
                                    </AvatarFallback>
                                </Avatar>
                                <h2 className="text-xl font-semibold text-slate-900 mb-2">
                                    {welcomeMessage || `Hi! I'm ${botName}`}
                                </h2>
                                <p className="text-slate-600 max-w-md">
                                    Ask me a question and I'll do my best to help you
                                    based on my knowledge base.
                                </p>
                            </div>
                        ) : (
                            <MessageList
                                messages={messages}
                                botName={botName}
                                botAvatar={botAvatar}
                                streaming={streaming}
                                feedbackState={feedbackState}
                                onSubmitFeedback={submitFeedbackForMessage}
                            />
                        )}

                        {(error || feedbackError) && (
                            <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg">
                                {error && (
                                    <p className="text-red-800 text-sm mb-2">{error}</p>
                                )}
                                {feedbackError && (
                                    <p className="text-red-700 text-xs">{feedbackError}</p>
                                )}
                                <Button
                                    variant="outline"
                                    size="sm"
                                    onClick={retryLastMessage}
                                    disabled={loading}
                                >
                                    Retry
                                </Button>
                            </div>
                        )}
                    </>
                ) : (
                    <div className="space-y-4">
                        <div className="flex flex-col gap-2 md:flex-row md:items-center md:gap-3">
                            <Input
                                placeholder="Filter by session id (optional)"
                                value={historySessionFilter}
                                onChange={(e) => setHistorySessionFilter(e.target.value)}
                                className="md:max-w-sm"
                            />
                            <div className="flex gap-2">
                                <Button
                                    variant="outline"
                                    size="sm"
                                    onClick={() => loadHistory(historySessionFilter || undefined)}
                                    disabled={historyLoading}
                                >
                                    Apply
                                </Button>
                                <Button
                                    variant="ghost"
                                    size="sm"
                                    onClick={() => {
                                        setHistorySessionFilter("");
                                        loadHistory();
                                    }}
                                    disabled={historyLoading}
                                >
                                    Clear
                                </Button>
                            </div>
                        </div>

                        {historyLoading && (
                            <div className="flex items-center gap-2 text-slate-600 text-sm">
                                <Loader2 className="h-4 w-4 animate-spin" />
                                Loading history...
                            </div>
                        )}

                        {historyError && (
                            <div className="p-3 bg-red-50 border border-red-200 rounded text-sm text-red-800">
                                {historyError}
                            </div>
                        )}

                        {!historyLoading && !historyError && historyEntries.length === 0 && (
                            <p className="text-sm text-slate-600">No history available yet.</p>
                        )}

                        <div className="space-y-3">
                            {historyEntries.map((entry) => (
                                <div
                                    key={entry.id}
                                    className="border border-slate-200 rounded-lg p-3 bg-white shadow-sm"
                                >
                                    <div className="flex items-center justify-between text-xs text-slate-500">
                                        <span className="font-semibold text-slate-700">
                                            {entry.role.toUpperCase()}
                                        </span>
                                        <span>
                                            {new Date(entry.created_at).toLocaleString()}
                                        </span>
                                    </div>
                                    <p className="mt-2 text-sm text-slate-800 whitespace-pre-wrap">
                                        {entry.content}
                                    </p>
                                    <div className="mt-2 flex flex-wrap gap-3 text-[11px] text-slate-500">
                                        {entry.session_id && <span>Session: {entry.session_id}</span>}
                                        {entry.answer_id && <span>Answer: {entry.answer_id}</span>}
                                        {entry.client_message_id && (
                                            <span>Message: {entry.client_message_id}</span>
                                        )}
                                        {entry.citations?.length ? (
                                            <span>Citations: {entry.citations.length}</span>
                                        ) : null}
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                )}
            </div>

            {/* Input */}
            <div className="p-4 border-t border-slate-200">
                <div className="flex gap-2">
                    <Textarea
                        ref={textareaRef}
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        onKeyDown={handleKeyDown}
                        placeholder="Ask a question..."
                        disabled={loading}
                        className="min-h-[44px] max-h-32 resize-none"
                        rows={1}
                    />
                    <Button
                        onClick={handleSend}
                        disabled={!input.trim() || loading}
                        className="self-end min-w-[44px] h-[44px]"
                        size="icon"
                        aria-label="Send"
                        title="Send"
                    >
                        {loading ? (
                            <Loader2 className="h-5 w-5 animate-spin" />
                        ) : (
                            <Send className="h-5 w-5" />
                        )}
                    </Button>
                </div>
                <p className="text-xs text-slate-500 mt-2">
                    Press Enter to send, Shift+Enter for new line
                </p>
            </div>
        </Card>
    );
}
