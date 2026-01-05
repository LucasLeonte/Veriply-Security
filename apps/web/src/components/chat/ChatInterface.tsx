"use client";

import { useState, useEffect, useRef } from "react";
import { X, Send, Loader2, RefreshCw, Clock3 } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { useChat } from "@/hooks/useChat";
import MessageList from "./MessageList";
import ContextSummary from "../ContextSummary";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { getUserSessions } from "@/lib/api/chat";

interface ChatInterfaceProps {
    botId: string;
    botName: string;
    botAvatar?: string;
    welcomeMessage: string;
    isPublic: boolean;
    confidenceThreshold: number; // 0-100 percentage from bot config
}

export default function ChatInterface({
    botId,
    botName,
    botAvatar,
    welcomeMessage,
    isPublic,
    confidenceThreshold,
}: ChatInterfaceProps) {
    const [input, setInput] = useState("");
    const [showClearDialog, setShowClearDialog] = useState(false);
    const {
        messages,
        loading,
        streaming,
        error,
        contextSize,
        sendMessage,
        clearHistory,
        retryLastMessage,
        contextWindow,
        sessionId,
        resumeSession,
        feedbackState,
        submitFeedbackForMessage,
    } = useChat(botId);

    // Validate message structure at runtime for defensive programming
    const validateMessages = (msgs: any[]) => {
        return msgs.every(msg =>
            typeof msg === 'object' &&
            ['user', 'assistant'].includes(msg.role) &&
            typeof msg.content === 'string'
        );
    };

    if (messages.length > 0 && !validateMessages(messages)) {
        console.warn('[ChatInterface] Invalid message structure detected:', messages);
    }

    const textareaRef = useRef<HTMLTextAreaElement>(null);
    const [historyOpen, setHistoryOpen] = useState(false);
    const [userSessions, setUserSessions] = useState<Array<{ id: string; title: string; lastTimestamp: number; count: number }>>([]);
    const [selectedSessionId, setSelectedSessionId] = useState<string | null>(null);

    // Sync selectedSessionId with the one in useChat
    useEffect(() => {
        if (sessionId) {
            setSelectedSessionId(sessionId);
        }
    }, [sessionId]);

    const refreshSessions = () => {
        const list = getUserSessions(botId);
        setUserSessions(list);
    };

    const contextCount = Math.min(messages.length, contextWindow);
    const summarizedCount = Math.max(0, messages.length - contextWindow);

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

    // Refresh sessions when messages change (keeps sidebar index fresh)
    useEffect(() => {
        refreshSessions();
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [messages.length, botId]);

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

    const handleResetConversation = () => {
        if (loading) return;
        const confirmed = window.confirm(
            "Start a new conversation? This will clear the current context."
        );
        if (confirmed) {
            clearHistory();
            setInput("");
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
        <>
            <div className="w-full max-w-6xl h-[90vh] flex gap-4">
                {/* Sidebar (Your chats) */}
                <aside className="hidden md:flex md:flex-col w-[260px] border border-slate-200 rounded-lg bg-white shadow-sm overflow-hidden">
                    <div className="p-3 border-b border-slate-200 flex items-center justify-between">
                        <p className="text-sm font-medium text-slate-800">Your chats</p>
                        <Button
                            variant="outline"
                            size="sm"
                            onClick={() => {
                                clearHistory();
                            }}
                            title="Start new conversation"
                        >
                            New
                        </Button>
                    </div>
                    <div className="flex-1 overflow-y-auto divide-y divide-slate-100">
                        {userSessions.length === 0 ? (
                            <div className="p-4 text-sm text-slate-600">No conversations yet.</div>
                        ) : (
                            userSessions.map((s) => (
                                <button
                                    key={s.id}
                                    onClick={() => {
                                        resumeSession(s.id);
                                    }}
                                    className={`w-full text-left p-3 transition-colors ${selectedSessionId === s.id ? "bg-sky-50" : "hover:bg-slate-50"
                                        }`}
                                >
                                    <p className="text-sm text-slate-900 line-clamp-1">{s.title}</p>
                                    <p className="text-[11px] text-slate-500">
                                        {new Date(s.lastTimestamp).toLocaleString()} • {s.count} message{s.count !== 1 ? "s" : ""}
                                    </p>
                                </button>
                            ))
                        )}
                    </div>
                </aside>

                <Card className="flex-1 h-full flex flex-col shadow-lg">
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
                            {/* Mobile-only: open your chats */}
                            <Button
                                className="md:hidden"
                                variant="ghost"
                                size="sm"
                                onClick={() => {
                                    refreshSessions();
                                    setHistoryOpen(true);
                                }}
                                title="Your conversations"
                            >
                                <Clock3 className="h-4 w-4" />
                            </Button>
                            <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => setShowClearDialog(true)}
                                disabled={messages.length === 0 || loading}
                                title="Start new conversation"
                            >
                                <RefreshCw className="h-4 w-4" />
                            </Button>
                        </div>
                    </div>

                    {/* Messages */}
                    <div className="flex-1 overflow-y-auto p-4">
                        {messages.length > 0 && (
                            <ContextSummary
                                messages={messages}
                                contextWindow={contextWindow}
                            />
                        )}
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
                                botId={botId}
                                confidenceThresholdPercent={confidenceThreshold}
                                feedbackState={feedbackState}
                                onSubmitFeedback={submitFeedbackForMessage}
                            />
                        )}

                        {/* Error Display */}
                        {error && (
                            <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg">
                                <p className="text-red-800 text-sm mb-2">{error}</p>
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
                    </div>

                    {/* Input */}
                    <div className="p-4 border-t border-slate-200">
                        {/* Context Indicator */}
                        {messages.length > 0 && (
                            <div className="mb-2 text-xs text-slate-500">
                                Context: {contextSize} message{contextSize !== 1 ? 's' : ''}
                            </div>
                        )}
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

                    {/* Clear Conversation Dialog */}
                    {showClearDialog && (
                        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
                            <Card className="w-full max-w-md p-6 m-4 bg-white shadow-lg">
                                <h3 className="text-lg font-semibold text-slate-900 mb-2">
                                    Start New Conversation?
                                </h3>
                                <p className="text-slate-700 mb-4">
                                    This will clear your conversation history. This action cannot be undone.
                                </p>
                                <div className="flex gap-3 justify-end">
                                    <Button
                                        variant="outline"
                                        onClick={() => setShowClearDialog(false)}
                                    >
                                        Cancel
                                    </Button>
                                    <Button
                                        variant="destructive"
                                        onClick={() => {
                                            clearHistory();
                                            setShowClearDialog(false);
                                        }}
                                    >
                                        Clear History
                                    </Button>
                                </div>
                            </Card>
                        </div>
                    )}
                </Card>
            </div>

            <Dialog open={historyOpen} onOpenChange={setHistoryOpen}>
                <DialogContent className="max-w-lg">
                    <DialogHeader>
                        <DialogTitle>Your conversations</DialogTitle>
                    </DialogHeader>
                    {userSessions.length === 0 ? (
                        <p className="text-sm text-slate-600">No conversations yet.</p>
                    ) : (
                        <div className="divide-y divide-slate-100 border border-slate-200 rounded-md">
                            {userSessions.map((s) => (
                                <div key={s.id} className="p-3 flex items-center justify-between gap-3">
                                    <div>
                                        <p className="text-sm text-slate-900 line-clamp-1">{s.title}</p>
                                        <p className="text-[11px] text-slate-500">
                                            {new Date(s.lastTimestamp).toLocaleString()} • {s.count} message{s.count !== 1 ? "s" : ""}
                                        </p>
                                        <p className="text-[11px] text-slate-500 font-mono mt-1">{s.id}</p>
                                    </div>
                                    <Button
                                        size="sm"
                                        onClick={() => {
                                            resumeSession(s.id);
                                            setHistoryOpen(false);
                                        }}
                                    >
                                        Open
                                    </Button>
                                </div>
                            ))}
                        </div>
                    )}
                </DialogContent>
            </Dialog>
        </>
    );
}
