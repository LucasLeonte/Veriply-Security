"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Loader2 } from "lucide-react";
import { fetchChatHistory } from "@/lib/api/chatHistory";
import { saveChatHistory } from "@/lib/api/chat";
import { ChatHistoryEntry } from "@/types/chat";

interface ChatHistoryPanelProps {
    botId: string;
    onResumeChat?: () => void;
}

export function ChatHistoryPanel({ botId, onResumeChat }: ChatHistoryPanelProps) {
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
            const titleSource = firstUser?.content || last.content || "Conversation";
            return {
                sessionId,
                entries: sorted,
                lastTimestamp: new Date(last.created_at).getTime(),
                lastRole: last.role,
                title: titleSource.slice(0, 80),
            };
        });

        return convoList
            .sort((a, b) => b.lastTimestamp - a.lastTimestamp)
            .filter((c) =>
                historySessionFilter
                    ? c.sessionId.toLowerCase().includes(historySessionFilter.toLowerCase()) ||
                      c.title.toLowerCase().includes(historySessionFilter.toLowerCase())
                    : true
            );
    }, [historyEntries, historySessionFilter]);

    const selectedConversation = useMemo(
        () => conversations.find((c) => c.sessionId === selectedSessionId) || null,
        [conversations, selectedSessionId]
    );

    return (
        <div className="space-y-4">
            <div className="flex flex-col gap-2 md:flex-row md:items-center md:gap-3">
                <Input
                    placeholder="Search session or text"
                    value={historySessionFilter}
                    onChange={(e) => setHistorySessionFilter(e.target.value)}
                    className="md:max-w-sm"
                />
                <div className="flex gap-2">
                    <Button
                        variant="outline"
                        size="sm"
                        onClick={() => loadHistory(selectedSessionId || undefined)}
                        disabled={historyLoading}
                    >
                        Refresh
                    </Button>
                    <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => {
                            setHistorySessionFilter("");
                            setSelectedSessionId(null);
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

            {!historyLoading && !historyError && conversations.length === 0 && (
                <p className="text-sm text-slate-600">No history available yet.</p>
            )}

            {conversations.length > 0 && (
                <div className="grid gap-4 md:grid-cols-[260px,1fr]">
                    <div className="border border-slate-200 rounded-lg bg-white shadow-sm divide-y divide-slate-100">
                        {conversations.map((conversation) => (
                            <button
                                key={conversation.sessionId}
                                onClick={() => setSelectedSessionId(conversation.sessionId)}
                                className={`w-full text-left p-3 transition-colors ${
                                    selectedSessionId === conversation.sessionId
                                        ? "bg-sky-50"
                                        : "hover:bg-slate-50"
                                }`}
                            >
                                <div className="flex items-center justify-between text-xs text-slate-500">
                                    <span className="font-semibold text-slate-700">
                                        Session: {conversation.sessionId === "unspecified" ? "(none)" : conversation.sessionId}
                                    </span>
                                    <span>{new Date(conversation.lastTimestamp).toLocaleString()}</span>
                                </div>
                                <p className="mt-1 text-sm text-slate-800 line-clamp-2">
                                    {conversation.title}
                                </p>
                                <p className="text-[11px] text-slate-500 mt-1">
                                    {conversation.entries.length} message{conversation.entries.length !== 1 ? "s" : ""}
                                </p>
                            </button>
                        ))}
                    </div>

                    <div className="border border-slate-200 rounded-lg bg-white shadow-sm p-3 min-h-[320px]">
                        {selectedConversation ? (
                            <div className="space-y-3">
                                <div className="flex items-center justify-between">
                                    <div className="text-xs text-slate-500">
                                        Session: <span className="font-mono">{selectedConversation.sessionId}</span>
                                    </div>
                                    <Button
                                        size="sm"
                                        onClick={async () => {
                                            if (!selectedConversation.sessionId || selectedConversation.sessionId === "unspecified") {
                                                return;
                                            }
                                            try {
                                                // Persist chosen session id so Chat uses it on mount
                                                if (typeof window !== "undefined") {
                                                    sessionStorage.setItem(
                                                        `chat_session_id_${botId}`,
                                                        selectedConversation.sessionId
                                                    );
                                                }

                                                // Load messages from API for this session and map to ChatMessage[]
                                                const entries = await fetchChatHistory(botId, {
                                                    sessionId: selectedConversation.sessionId,
                                                    limit: 500,
                                                });

                                                const mapped = entries
                                                    .sort(
                                                        (a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime()
                                                    )
                                                    .map((e) => ({
                                                        id: (e.role === "user" ? (e.client_message_id || e.id) : e.id) as string,
                                                        role: (e.role === "user" ? "user" : "assistant") as "user" | "assistant",
                                                        content: e.content,
                                                        timestamp: new Date(e.created_at).getTime(),
                                                        citations: e.citations || [],
                                                        answerId: e.answer_id || undefined,
                                                    }));

                                                // Store as the current chat history for ChatInterface
                                                saveChatHistory(botId, mapped);

                                                // Switch to Chat tab
                                                onResumeChat?.();
                                            } catch (err) {
                                                console.error("Failed to resume conversation", err);
                                            }
                                        }}
                                    >
                                        Resume in Chat
                                    </Button>
                                </div>
                                {selectedConversation.entries.map((entry) => (
                                    <div
                                        key={entry.id}
                                        className="border border-slate-100 rounded-md p-3"
                                    >
                                        <div className="flex items-center justify-between text-xs text-slate-500">
                                            <span className="font-semibold text-slate-700">
                                                {entry.role.toUpperCase()}
                                            </span>
                                            <span>{new Date(entry.created_at).toLocaleString()}</span>
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
                        ) : (
                            <div className="flex items-center justify-center h-full text-sm text-slate-600">
                                Select a conversation to view its messages
                            </div>
                        )}
                    </div>
                </div>
            )}
        </div>
    );
}

export default ChatHistoryPanel;
