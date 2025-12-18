"use client";

import { useState, useEffect, useCallback, useRef, useMemo } from "react";
import { ChatMessage, Citation } from "@/types/chat";
import {
    streamChatQuery,
    loadChatHistory,
    saveChatHistory,
    clearChatHistory as clearStoredHistory,
} from "@/lib/api/chat";
import { v4 as uuidv4 } from "uuid";

// Context window size (configurable per bot, default 10 messages)
const DEFAULT_CONTEXT_WINDOW = 10;

export function useChat(botId: string, contextWindowSize: number = DEFAULT_CONTEXT_WINDOW) {
    const [messages, setMessages] = useState<ChatMessage[]>([]);
    const [loading, setLoading] = useState(false);
    const [streaming, setStreaming] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [retryCount, setRetryCount] = useState(0);
    
    // Initialize sessionId from sessionStorage to persist across tab switches
    const sessionIdRef = useRef<string>('');
    
    // Set up sessionId on mount
    useEffect(() => {
        if (!sessionIdRef.current) {
            const key = `chat_session_${botId}`;
            let sessionId = typeof window !== 'undefined' ? sessionStorage.getItem(key) : null;
            if (!sessionId) {
                sessionId = uuidv4();
            }
            if (typeof window !== 'undefined' && sessionId) {
                sessionStorage.setItem(key, sessionId);
            }
            sessionIdRef.current = sessionId || uuidv4();
        }
    }, [botId]);
    
    const lastQueryRef = useRef<string>("");
    const streamingMessageRef = useRef<ChatMessage | null>(null);
    const contextWindow = useMemo(() => {
        const configured = Number(process.env.NEXT_PUBLIC_CONTEXT_WINDOW);
        if (Number.isFinite(configured) && configured > 0 && configured <= 100) {
            return Math.floor(configured);
        }
        return 10;
    }, []);

    // Load chat history on mount
    useEffect(() => {
        const history = loadChatHistory(botId, sessionIdRef.current);
        setMessages(history);
    }, [botId]);

    // Save chat history whenever messages change
    useEffect(() => {
        if (messages.length > 0) {
            saveChatHistory(botId, sessionIdRef.current, messages);
        }
    }, [botId, messages]);

    // Clear history on page unload
    useEffect(() => {
        const handleBeforeUnload = () => {
            // Session-based: clear on unload (as per AC #9)
            // Comment this out if we want persistent history
            clearStoredHistory(botId, sessionIdRef.current);
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

            const contextPayload = [...messages, userMessage];
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
                // Build conversation history using context window
                const conversationHistory = messages.slice(-contextWindowSize).map((msg) => ({
                    role: msg.role,
                    content: msg.content,
                }));

                // Stream tokens
                let fullContent = "";
                let metadata: any = null;

                for await (const chunk of streamChatQuery(botId, query, {
                    context: contextPayload,
                    contextWindow,
                })) {
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
                        if (metadata?.trust_level) {
                            lastMsg.trustLevel = metadata.trust_level;
                        }
                        if (metadata?.confidence_score) {
                            lastMsg.confidenceScore = metadata.confidence_score;
                        }
                        if (metadata?.source_type) {
                            lastMsg.sourceType = metadata.source_type;
                        }
                        if (metadata?.response_id) {
                            lastMsg.responseId = metadata.response_id;
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
        [botId, messages, loading, contextWindow]
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
        clearStoredHistory(botId, sessionIdRef.current);
        // Generate new sessionId and store it for the next conversation
        const newSessionId = uuidv4();
        sessionIdRef.current = newSessionId;
        const key = `chat_session_${botId}`;
        if (typeof window !== 'undefined') {
            sessionStorage.setItem(key, newSessionId);
        }
        setError(null);
        setRetryCount(0);
    }, [botId]);

    // Compute context size (number of messages in context window)
    const contextSize = Math.min(messages.length, contextWindowSize);

    return {
        messages,
        loading,
        streaming,
        error,
        contextSize,
        sendMessage,
        retryLastMessage,
        clearHistory,
        contextWindow,
        sessionId: sessionIdRef.current,
    };
}
