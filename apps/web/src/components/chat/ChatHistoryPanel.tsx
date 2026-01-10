"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Loader2, RefreshCw, Search, MessageSquare, Trash2 } from "lucide-react";
import { fetchChatHistory } from "@/lib/api/chatHistory";
import { saveChatHistory } from "@/lib/api/chat";
import { ChatHistoryEntry, ChatMessage } from "@/types/chat";
import MessageList from "./MessageList";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { User } from "lucide-react";

interface ChatHistoryPanelProps {
    botId: string;
    botName: string;
    botAvatar?: string;
    onResumeChat?: () => void;
}

export function ChatHistoryPanel({ botId, botName, botAvatar, onResumeChat }: ChatHistoryPanelProps) {
    const [historyEntries, setHistoryEntries] = useState<ChatHistoryEntry[]>([]);
    const [historyLoading, setHistoryLoading] = useState(false);
    const [historyError, setHistoryError] = useState<string | null>(null);
    const [historySessionFilter, setHistorySessionFilter] = useState("");
    const [selectedSessionId, setSelectedSessionId] = useState<string | null>(null);

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
                if (sessionId) {
                    setSelectedSessionId(sessionId);
                } else if (entries.length > 0) {
                    const latestSession = entries
                        .filter((e) => !!(e.session_id || ""))
                        .sort(
                            (a, b) =>
                                new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
                        )[0]?.session_id;
                    setSelectedSessionId(latestSession || null);
                } else {
                    setSelectedSessionId(null);
                }
            } catch (err) {
                const status = (err as { status?: number })?.status;
                const message =
                    status === 401
                        ? "Please log in as an owner/admin to view history"
                        : (err as Error)?.message || "Failed to load history";
                setHistoryError(message);
            } finally {
                setHistoryLoading(false);
            }
        },
        [botId]
    );

    useEffect(() => {
        loadHistory();
    }, [loadHistory]);

    const conversations = useMemo(() => {
        const grouped = new Map<string, ChatHistoryEntry[]>();
        historyEntries.forEach((entry) => {
            const key = entry.session_id || "unspecified";
            const arr = grouped.get(key) || [];
            arr.push(entry);
            grouped.set(key, arr);
        });

        const convoList = Array.from(grouped.entries()).map(([sessionId, entries]) => {
            const sorted = [...entries].sort(
                (a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime()
            );
            const last = sorted[sorted.length - 1];
            const firstUser = sorted.find((e) => e.role === "user");

            // Extract user info and origin from the first message in the session
            // (or any message that has it, but usually the first)
            const userInfoMsg = sorted.find(e => e.user_email || e.user_name);
            const userEmail = userInfoMsg?.user_email;
            const userName = userInfoMsg?.user_name;
            const origin = userInfoMsg?.origin;

            const titleSource = firstUser?.content || last.content || "Conversation";
            return {
                sessionId,
                entries: sorted,
                lastTimestamp: new Date(last.created_at).getTime(),
                lastRole: last.role,
                title: titleSource.slice(0, 60), // clamp title length
                userEmail,
                userName,
                origin
            };
        });

        return convoList
            .sort((a, b) => b.lastTimestamp - a.lastTimestamp)
            .filter((c) =>
                historySessionFilter
                    ? c.sessionId.toLowerCase().includes(historySessionFilter.toLowerCase()) ||
                    c.title.toLowerCase().includes(historySessionFilter.toLowerCase()) ||
                    (c.userEmail && c.userEmail.toLowerCase().includes(historySessionFilter.toLowerCase())) ||
                    (c.userName && c.userName.toLowerCase().includes(historySessionFilter.toLowerCase()))
                    : true
            );
    }, [historyEntries, historySessionFilter]);

    const selectedConversation = useMemo(
        () => conversations.find((c) => c.sessionId === selectedSessionId) || null,
        [conversations, selectedSessionId]
    );

    // Map history entries to ChatMessage format for MessageList
    const mappedMessages: ChatMessage[] = useMemo(() => {
        if (!selectedConversation) return [];
        return selectedConversation.entries.map((e) => ({
            id: (e.role === "user" ? (e.client_message_id || e.id) : e.id) as string,
            role: e.role,
            content: e.content,
            timestamp: new Date(e.created_at).getTime(),
            citations: e.citations || [],
            answerId: e.answer_id || undefined,
            // History doesn't strictly have confidence stored in this model yet, or it's not exposed
            // If the backend exposes it later, map it here.
        }));
    }, [selectedConversation]);

    return (
        <div className="flex flex-col md:flex-row h-[calc(100vh-200px)] min-h-[500px] border border-slate-200 rounded-xl bg-white shadow-sm overflow-hidden">
            {/* Sidebar */}
            <div className="w-full md:w-[300px] flex flex-col border-b md:border-b-0 md:border-r border-slate-100 bg-slate-50/50">
                <div className="p-4 border-b border-slate-100 bg-white">
                    <div className="flex items-center gap-2 mb-3">
                        <div className="relative flex-1">
                            <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-slate-400" />
                            <Input
                                placeholder="Search history..."
                                value={historySessionFilter}
                                onChange={(e) => setHistorySessionFilter(e.target.value)}
                                className="pl-9 bg-slate-50 border-slate-200 focus-visible:ring-sky-500"
                            />
                        </div>
                        <Button
                            variant="outline"
                            size="icon"
                            onClick={() => loadHistory(selectedSessionId || undefined)}
                            disabled={historyLoading}
                            title="Refresh"
                            className="bg-white"
                        >
                            <RefreshCw className={`h-4 w-4 ${historyLoading ? "animate-spin" : ""}`} />
                        </Button>
                    </div>
                </div>

                <div className="flex-1 overflow-y-auto">
                    {conversations.length === 0 ? (
                        <div className="p-8 text-center text-slate-500 text-sm">
                            {historyLoading ? (
                                <div className="flex flex-col items-center gap-2">
                                    <Loader2 className="h-5 w-5 animate-spin text-slate-400" />
                                    <span>Loading...</span>
                                </div>
                            ) : (
                                "No history found."
                            )}
                        </div>
                    ) : (
                        <div className="divide-y divide-slate-100">
                            {conversations.map((conversation) => (
                                <button
                                    key={conversation.sessionId}
                                    onClick={() => setSelectedSessionId(conversation.sessionId)}
                                    className={`w-full text-left p-4 transition-all hover:bg-white group relative ${selectedSessionId === conversation.sessionId
                                        ? "bg-white border-l-4 border-l-sky-500 shadow-sm z-10"
                                        : "border-l-4 border-l-transparent hover:border-l-slate-200"
                                        }`}
                                >
                                    <div className="flex items-start gap-3">
                                        <div className={`mt-1 p-2 rounded-full flex-shrink-0 ${selectedSessionId === conversation.sessionId
                                            ? "bg-sky-100 text-sky-600"
                                            : "bg-slate-100 text-slate-400 group-hover:bg-slate-200 group-hover:text-slate-500"
                                            }`}>
                                            <MessageSquare size={16} />
                                        </div>
                                        <div className="flex-1 min-w-0">
                                            <p className={`text-sm font-medium mb-1 line-clamp-1 ${selectedSessionId === conversation.sessionId
                                                ? "text-slate-900"
                                                : "text-slate-700"
                                                }`}>
                                                {conversation.title}
                                            </p>
                                            <div className="flex flex-wrap items-center gap-1.5 mb-1">
                                                {conversation.userName || conversation.userEmail ? (
                                                    <div className="flex items-center gap-1 text-xs text-slate-500 bg-slate-100 px-1.5 py-0.5 rounded-full max-w-full">
                                                        <User size={10} />
                                                        <span className="truncate max-w-[120px]" title={conversation.userEmail}>
                                                            {conversation.userName || conversation.userEmail?.split('@')[0]}
                                                        </span>
                                                    </div>
                                                ) : (
                                                    <div className="text-xs text-slate-400 italic px-1">Anonymous</div>
                                                )}
                                                {conversation.origin && (
                                                    <span className={`text-[10px] px-1.5 py-0.5 rounded border uppercase tracking-wider font-semibold ${conversation.origin.toLowerCase().includes('widget')
                                                        ? 'bg-purple-50 text-purple-600 border-purple-100'
                                                        : (conversation.origin === 'localhost' || conversation.origin.includes('veriply'))
                                                            ? 'bg-emerald-50 text-emerald-600 border-emerald-100'
                                                            : 'bg-slate-50 text-slate-600 border-slate-200'
                                                        }`}>
                                                        {conversation.origin === 'localhost' ? 'Internal Chat' : conversation.origin}
                                                    </span>
                                                )}
                                            </div>
                                            <div className="flex items-center justify-between text-xs text-slate-500">
                                                <span>{new Date(conversation.lastTimestamp).toLocaleDateString()}</span>
                                                <span>{conversation.entries.length} msgs</span>
                                            </div>
                                        </div>
                                    </div>
                                </button>
                            ))}
                        </div>
                    )}
                </div>
            </div>

            {/* Main Content */}
            <div className="flex-1 flex flex-col bg-slate-50/30">
                {selectedConversation ? (
                    <>
                        <div className="px-6 py-4 bg-white border-b border-slate-100 flex items-center justify-between shadow-sm z-10">
                            <div>
                                <h3 className="text-sm font-semibold text-slate-800">
                                    {selectedConversation.userName || selectedConversation.userEmail
                                        ? (selectedConversation.userName || selectedConversation.userEmail?.split('@')[0])
                                        : "Conversation Detail"}
                                </h3>
                                <div className="flex items-center gap-2 text-xs text-slate-500 mt-0.5">
                                    {selectedConversation.userEmail && (
                                        <>
                                            <span className="truncate max-w-[200px]">{selectedConversation.userEmail}</span>
                                            <span>•</span>
                                        </>
                                    )}
                                    <span className="font-mono bg-slate-100 px-1.5 py-0.5 rounded">
                                        {selectedConversation.sessionId.slice(0, 8)}...
                                    </span>
                                    <span>•</span>
                                    <span>
                                        {new Date(selectedConversation.lastTimestamp).toLocaleString()}
                                    </span>
                                </div>
                            </div>
                            <Button
                                size="sm"
                                onClick={async () => {
                                    if (!selectedConversation.sessionId || selectedConversation.sessionId === "unspecified") {
                                        return;
                                    }
                                    try {
                                        if (typeof window !== "undefined") {
                                            sessionStorage.setItem(
                                                `chat_session_id_${botId}`,
                                                selectedConversation.sessionId
                                            );
                                        }
                                        const entries = await fetchChatHistory(botId, {
                                            sessionId: selectedConversation.sessionId,
                                            limit: 500,
                                        });

                                        const mapped: ChatMessage[] = entries
                                            .sort(
                                                (a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime()
                                            )
                                            .map((e) => ({
                                                id: (e.role === "user" ? (e.client_message_id || e.id) : e.id) as string,
                                                role: e.role,
                                                content: e.content,
                                                timestamp: new Date(e.created_at).getTime(),
                                                citations: e.citations || [],
                                                answerId: e.answer_id || undefined,
                                            }));
                                        // Store as the current chat history for ChatInterface
                                        saveChatHistory(botId, selectedConversation.sessionId, mapped);
                                        onResumeChat?.();
                                    } catch (err) {
                                        
                                    }
                                }}
                                className="bg-sky-600 hover:bg-sky-700 text-white shadow-sm"
                            >
                                Resume in Chat
                            </Button>
                        </div>

                        <div className="flex-1 overflow-hidden relative">
                            <div className="absolute inset-0 overflow-y-auto px-4 py-6 md:px-8 bg-white">
                                <MessageList
                                    messages={mappedMessages}
                                    botName={botName}
                                    botAvatar={botAvatar}
                                    streaming={false}
                                    botId={botId}
                                    sessionId={selectedConversation.sessionId || undefined}
                                />
                            </div>
                        </div>
                    </>
                ) : (
                    <div className="flex-1 flex flex-col items-center justify-center text-slate-400 p-8">
                        <div className="w-16 h-16 bg-slate-100 rounded-full flex items-center justify-center mb-4">
                            <MessageSquare className="h-8 w-8 text-slate-300" />
                        </div>
                        <p className="text-slate-600 font-medium">No conversation selected</p>
                        <p className="text-sm mt-1">Select a session from the sidebar to view history</p>
                    </div>
                )}
            </div>
        </div>
    );
}

export default ChatHistoryPanel;
