"use client";

import { useState, useEffect, useRef } from "react";
import { X, Send, Loader2, RefreshCw } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { useChat } from "@/hooks/useChat";
import MessageList from "./MessageList";
import ContextSummary from "../ContextSummary";

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
    );
}
