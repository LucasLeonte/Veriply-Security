"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { ChatMessage, Citation } from "@/types/chat";
import {
    streamChatQuery,
    loadChatHistory,
    saveChatHistory,
    clearChatHistory as clearStoredHistory,
} from "@/lib/api/chat";
import { v4 as uuidv4 } from "uuid";

export function useChat(botId: string) {
    const [messages, setMessages] = useState<ChatMessage[]>([]);
    const [loading, setLoading] = useState(false);
    const [streaming, setStreaming] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [retryCount, setRetryCount] = useState(0);
    const lastQueryRef = useRef<string>("");
    const streamingMessageRef = useRef<ChatMessage | null>(null);

    // Load chat history on mount
    useEffect(() => {
        const history = loadChatHistory(botId);
        setMessages(history);
    }, [botId]);

    // Save chat history whenever messages change
    useEffect(() => {
        if (messages.length > 0) {
            saveChatHistory(botId, messages);
        }
    }, [botId, messages]);

    // Clear history on page unload
    useEffect(() => {
        const handleBeforeUnload = () => {
            // Session-based: clear on unload (as per AC #9)
            // Comment this out if we want persistent history
            clearStoredHistory(botId);
        };

        window.addEventListener("beforeunload", handleBeforeUnload);
        return () => {
            window.removeEventListener("beforeunload", handleBeforeUnload);
        };
    }, [botId]);

    const sendMessage = useCallback(
        async (query: string) => {
            if (!query.trim() || loading) return;

            // Reset error and retry count
            setError(null);
            setRetryCount(0);
            lastQueryRef.current = query;

            // Add user message immediately (optimistic update)
            const userMessage: ChatMessage = {
                id: uuidv4(),
                role: "user",
                content: query,
                timestamp: Date.now(),
            };

            setMessages((prev) => [...prev, userMessage]);
            setLoading(true);
            setStreaming(true);

            // Create assistant message placeholder
            const assistantMessage: ChatMessage = {
                id: uuidv4(),
                role: "assistant",
                content: "",
                timestamp: Date.now(),
                citations: [],
            };

            streamingMessageRef.current = assistantMessage;
            setMessages((prev) => [...prev, assistantMessage]);

            try {
                // Build conversation history
                const conversationHistory = messages.slice(-4).map((msg) => ({
                    role: msg.role,
                    content: msg.content,
                }));

                // Stream tokens
                let fullContent = "";
                let metadata: any = null;

                for await (const chunk of streamChatQuery(
                    botId,
                    query,
                    conversationHistory
                )) {
                    if (chunk.type === "token") {
                        fullContent += chunk.content;

                        // Batch updates every 100ms or on newline
                        setMessages((prev) => {
                            const updated = [...prev];
                            const lastMsg = updated[updated.length - 1];
                            if (lastMsg && lastMsg.role === "assistant") {
                                lastMsg.content = fullContent;
                            }
                            return updated;
                        });
                    } else if (chunk.type === "metadata") {
                        metadata = chunk.data;
                    }
                }

                // Update final message with metadata
                setMessages((prev) => {
                    const updated = [...prev];
                    const lastMsg = updated[updated.length - 1];
                    if (lastMsg && lastMsg.role === "assistant") {
                        lastMsg.content = fullContent;
                        if (metadata?.citations) {
                            lastMsg.citations = metadata.citations;
                        }
                    }
                    return updated;
                });

                setStreaming(false);
                setLoading(false);
            } catch (err: any) {
                setStreaming(false);
                setLoading(false);
                setError(
                    err.message ||
                        "Sorry, I encountered an issue. Please try again."
                );

                // Remove incomplete assistant message
                setMessages((prev) => prev.slice(0, -1));

                console.error("Chat error:", err);
            }
        },
        [botId, messages, loading]
    );

    const retryLastMessage = useCallback(() => {
        if (retryCount >= 3) {
            setError("Maximum retry attempts reached. Please try again later.");
            return;
        }

        setRetryCount((prev) => prev + 1);
        sendMessage(lastQueryRef.current);
    }, [retryCount, sendMessage]);

    const clearHistory = useCallback(() => {
        setMessages([]);
        clearStoredHistory(botId);
        setError(null);
        setRetryCount(0);
    }, [botId]);

    return {
        messages,
        loading,
        streaming,
        error,
        sendMessage,
        retryLastMessage,
        clearHistory,
    };
}
