"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { ChatMessage } from "@/types/chat";
import {
    streamChatQuery,
    loadChatHistory,
    saveChatHistory,
    clearChatHistory as clearStoredHistory,
} from "@/lib/api/chat";
import { v4 as uuidv4 } from "uuid";
import {
    submitFeedback as submitFeedbackApi,
    FeedbackReason,
    FeedbackType,
} from "@/lib/api/feedback";
import { getAccessToken } from "@/lib/auth";

type FeedbackEntry = {
    type: FeedbackType;
    reason?: FeedbackReason;
    status: "idle" | "pending" | "sent" | "error" | "cooldown";
    timestamp: number;
    message?: string;
    cooldownUntil?: number;
};

export function useChat(botId: string) {
    const [messages, setMessages] = useState<ChatMessage[]>([]);
    const [loading, setLoading] = useState(false);
    const [streaming, setStreaming] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [retryCount, setRetryCount] = useState(0);
    const [feedbackState, setFeedbackState] = useState<Record<string, FeedbackEntry>>({});
    const [feedbackRateLog, setFeedbackRateLog] = useState<number[]>([]);
    const [feedbackError, setFeedbackError] = useState<string | null>(null);
    const lastQueryRef = useRef<string>("");
    const streamingMessageRef = useRef<ChatMessage | null>(null);
    const sessionIdRef = useRef<string>("");

    // Initialize session id for tracking feedback (one per session)
    if (typeof window !== "undefined" && !sessionIdRef.current) {
        const key = `chat_session_id_${botId}`;
        const existing = sessionStorage.getItem(key);
        if (existing) {
            sessionIdRef.current = existing;
        } else {
            const generated = uuidv4();
            sessionStorage.setItem(key, generated);
            sessionIdRef.current = generated;
        }
    }

    // Load chat history on mount
    useEffect(() => {
        const history = loadChatHistory(botId);
        setMessages(history);
    }, [botId]);

    // Load feedback state for this session
    useEffect(() => {
        if (typeof window === "undefined") return;
        const key = `feedback_state_${botId}_${sessionIdRef.current}`;
        const stored = sessionStorage.getItem(key);
        if (stored) {
            try {
                setFeedbackState(JSON.parse(stored));
            } catch (err) {
                console.error("Failed to load feedback state", err);
            }
        }
    }, [botId]);

    // Save chat history whenever messages change
    useEffect(() => {
        if (messages.length > 0) {
            saveChatHistory(botId, messages);
        }
    }, [botId, messages]);

    // Persist feedback state per session
    useEffect(() => {
        if (typeof window === "undefined") return;
        const key = `feedback_state_${botId}_${sessionIdRef.current}`;
        sessionStorage.setItem(key, JSON.stringify(feedbackState));
    }, [feedbackState, botId]);

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
                        if (metadata?.answer_id) {
                            lastMsg.answerId = metadata.answer_id as string;
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

    const submitFeedbackForMessage = useCallback(
        async (
            params: {
                messageId: string;
                answerId?: string;
                type: FeedbackType;
                reason?: FeedbackReason;
                notes?: string;
            }
        ) => {
            const { messageId, answerId, type, reason, notes } = params;
            if (!answerId) {
                const err = "Missing answer identifier for feedback";
                setFeedbackError(err);
                return { success: false, error: err };
            }

            // Fast-fail if user is not authenticated (no stored token)
            const token = typeof window !== "undefined" ? getAccessToken() : null;
            if (!token) {
                const err = "Please log in to provide feedback";
                setFeedbackError(err);
                setFeedbackState((prev) => ({
                    ...prev,
                    [messageId]: {
                        type,
                        reason,
                        status: "error",
                        timestamp: Date.now(),
                        message: err,
                    },
                }));
                return { success: false, error: err };
            }

            const now = Date.now();
            const filtered = feedbackRateLog.filter(
                (ts) => now - ts < 5 * 60 * 1000
            );
            if (filtered.length >= 20) {
                const err = "Please wait before providing more feedback";
                setFeedbackError(err);
                setFeedbackRateLog(filtered);
                setFeedbackState((prev) => ({
                    ...prev,
                    [messageId]: {
                        type,
                        reason,
                        status: "cooldown",
                        timestamp: now,
                        message: err,
                        cooldownUntil: now + 60 * 1000,
                    },
                }));
                return { success: false, rateLimited: true };
            }

            setFeedbackRateLog([...filtered, now]);
            setFeedbackError(null);
            setFeedbackState((prev) => ({
                ...prev,
                [messageId]: {
                    type,
                    reason,
                    status: "pending",
                    timestamp: now,
                },
            }));

            try {
                await submitFeedbackApi(botId, {
                    answer_id: answerId,
                    message_id: messageId,
                    type,
                    reason,
                    additional_notes: notes,
                    session_id: sessionIdRef.current,
                });

                setFeedbackState((prev) => ({
                    ...prev,
                    [messageId]: {
                        type,
                        reason,
                        status: "sent",
                        timestamp: Date.now(),
                    },
                }));

                return { success: true };
            } catch (err: any) {
                const status = err?.status as number | undefined;
                const message =
                    status === 401
                        ? "Please log in to provide feedback"
                        : err?.message || "Failed to send feedback";
                setFeedbackError(message);
                setFeedbackState((prev) => ({
                    ...prev,
                    [messageId]: {
                        type,
                        reason,
                        status: status === 429 ? "cooldown" : "error",
                        timestamp: Date.now(),
                        message,
                        cooldownUntil:
                            status === 429 ? Date.now() + 60 * 1000 : undefined,
                    },
                }));
                return { success: false, error: message };
            }
        },
        [botId, feedbackRateLog]
    );

    return {
        messages,
        loading,
        streaming,
        error,
        sendMessage,
        retryLastMessage,
        clearHistory,
        feedbackState,
        feedbackError,
        submitFeedbackForMessage,
        sessionId: sessionIdRef.current,
    };
}
