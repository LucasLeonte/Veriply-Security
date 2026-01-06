"use client";

import { useState, useEffect, useRef } from "react";
import { X, Send, Loader2, RefreshCw, Clock3, Trash2 } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { useChat } from "@/hooks/useChat";
import MessageList from "./MessageList";
import ContextSummary from "../ContextSummary";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { getUserSessions, clearChatHistory } from "@/lib/api/chat";

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
        startNewSession,
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

    const handleDeleteSession = (e: React.MouseEvent, sId: string) => {
        e.stopPropagation();
        if (loading) return;

        if (window.confirm("Are you sure you want to delete this conversation?")) {
            clearChatHistory(botId, sId);
            refreshSessions();
            if (sId === sessionId) {
                startNewSession();
            }
        }
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
                    <div className="p-4 border-b border-slate-100 flex items-center justify-between bg-slate-50/50">
                        <p className="text-sm font-semibold text-slate-700">Conversations</p>
                        <Button
                            variant="ghost"
                            size="icon"
                            className="h-8 w-8 text-slate-500 hover:text-sky-600 hover:bg-sky-50"
                            onClick={() => {
                                startNewSession();
                            }}
                            title="Start new conversation"
                        >
                            <RefreshCw className="h-4 w-4" />
                        </Button>
                    </div>
                    <div className="flex-1 overflow-y-auto divide-y divide-slate-100">
                        {userSessions.length === 0 ? (
                            <div className="p-4 text-sm text-slate-600">No conversations yet.</div>
                        ) : (
                            userSessions.map((s) => (
                                <div
                                    key={s.id}
                                    className={`w-full text-left p-3 transition-colors group cursor-pointer ${selectedSessionId === s.id ? "bg-sky-50" : "hover:bg-slate-50"
                                        }`}
                                    onClick={() => {
                                        resumeSession(s.id);
                                    }}
                                >
                                    <div className="flex items-center justify-between w-full">
                                        <div className="flex-1 min-w-0 pr-2">
                                            <p className="text-sm text-slate-900 line-clamp-1">{s.title}</p>
                                            <p className="text-[11px] text-slate-500">
                                                {new Date(s.lastTimestamp).toLocaleString()} • {s.count} message{s.count !== 1 ? "s" : ""}
                                            </p>
                                        </div>
                                        <Button
                                            variant="ghost"
                                            size="icon"
                                            className="h-6 w-6 text-slate-400 hover:text-red-600 hover:bg-red-50 flex-shrink-0 opacity-0 group-hover:opacity-100 transition-opacity"
                                            onClick={(e) => handleDeleteSession(e, s.id)}
                                            title="Delete conversation"
                                        >
                                            <Trash2 className="h-3.5 w-3.5" />
                                        </Button>
                                    </div>
                                </div>
                            ))
                        )}
                    </div>
                </aside>

                <div className="flex-1 h-full flex flex-col bg-white rounded-2xl shadow-xl shadow-slate-200/50 border border-slate-100 overflow-hidden relative">
                    {/* Header */}
                    <div className="flex items-center justify-between px-6 py-4 border-b border-slate-50 bg-white/80 backdrop-blur-sm z-10 sticky top-0">
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
                                disabled={loading}
                                title="Start new conversation"
                            >
                                <RefreshCw className="h-4 w-4" />
                            </Button>
                        </div>
                    </div>

                    {/* Messages */}
                    <div className="flex-1 overflow-y-auto p-4 md:p-6 scroll-smooth">
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

                    {/* Input Area - Floating Capsule */}
                    <div className="p-4 md:p-6 bg-gradient-to-t from-white via-white to-transparent pt-10">
                        {/* Context Indicator */}
                        {messages.length > 0 && (
                            <div className="mb-3 text-center">
                                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-[10px] font-medium bg-slate-100 text-slate-500 border border-slate-200">
                                    Context: {contextSize} message{contextSize !== 1 ? 's' : ''}
                                </span>
                            </div>
                        )}
                        <div className="relative max-w-4xl mx-auto w-full">
                            <div className="relative flex items-end gap-2 bg-white rounded-3xl border border-slate-200 shadow-lg shadow-slate-100/50 hover:shadow-xl hover:shadow-slate-200/50 transition-shadow p-2 focus-within:ring-2 focus-within:ring-sky-100 focus-within:border-sky-300">
                                <Textarea
                                    ref={textareaRef}
                                    value={input}
                                    onChange={(e) => setInput(e.target.value)}
                                    onKeyDown={handleKeyDown}
                                    placeholder="Message..."
                                    disabled={loading}
                                    className="min-h-[44px] max-h-32 resize-none border-0 shadow-none focus-visible:ring-0 px-4 py-3 text-base bg-transparent flex-1"
                                    rows={1}
                                />
                                <Button
                                    onClick={handleSend}
                                    disabled={!input.trim() || loading}
                                    className={`mb-1 mr-1 rounded-full w-10 h-10 transition-all duration-300 ${input.trim() ? "bg-sky-600 hover:bg-sky-700 text-white shadow-md shadow-sky-200" : "bg-slate-100 text-slate-400 hover:bg-slate-200"}`}
                                    size="icon"
                                    aria-label="Send"
                                    title="Send"
                                >
                                    {loading ? (
                                        <Loader2 className="h-5 w-5 animate-spin" />
                                    ) : (
                                        <Send className="h-5 w-5 ml-0.5" />
                                    )}
                                </Button>
                            </div>
                            <p className="text-[10px] text-slate-400 text-center mt-3 font-medium">
                                Press Enter to send, Shift+Enter for new line
                            </p>
                        </div>
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
                </div>
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
                                    <Button
                                        variant="ghost"
                                        size="sm"
                                        className="h-8 w-8 text-slate-400 hover:text-red-600 hover:bg-red-50 p-0"
                                        onClick={(e) => handleDeleteSession(e, s.id)}
                                        title="Delete conversation"
                                    >
                                        <Trash2 className="h-4 w-4" />
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
