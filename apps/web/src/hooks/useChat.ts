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

// Context window size (configurable per bot, default 10 messages)
const DEFAULT_CONTEXT_WINDOW = 10;

export function useChat(
    botId: string,
    contextWindowSize: number = DEFAULT_CONTEXT_WINDOW,
    embedOrigin?: string
) {
    const [messages, setMessages] = useState<ChatMessage[]>([]);
    const [loading, setLoading] = useState(false);
    const [streaming, setStreaming] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [retryCount, setRetryCount] = useState(0);
    const [feedbackState, setFeedbackState] = useState<
        Record<string, FeedbackEntry>
    >({});
    const [feedbackRateLog, setFeedbackRateLog] = useState<number[]>([]);
    const [feedbackError, setFeedbackError] = useState<string | null>(null);

    // Initialize sessionId synchronously to ensure it's available immediately
    const getOrCreateSessionId = useCallback(() => {
        const key = `chat_session_${botId}`;
        let sessionId =
            typeof window !== "undefined" ? sessionStorage.getItem(key) : null;
        if (!sessionId) {
            sessionId = uuidv4();
            if (typeof window !== "undefined") {
                sessionStorage.setItem(key, sessionId);
            }
        }
        return sessionId;
    }, [botId]);

    const sessionIdRef = useRef<string>(
        typeof window !== "undefined" ? getOrCreateSessionId() : ""
    );

    // Ensure sessionId is set on client-side mount (for SSR hydration)
    useEffect(() => {
        if (!sessionIdRef.current) {
            sessionIdRef.current = getOrCreateSessionId();
        }
    }, [getOrCreateSessionId]);

    // Listen for storage events (for cross-tab communication only)
    // The initial localStorage check is done in the history loading useEffect
    useEffect(() => {
        if (typeof window === "undefined") return;

        const currentSession = sessionIdRef.current;

        // Listen for storage events (for cross-tab communication)
        const handleStorage = (event: StorageEvent) => {
            if (event.key?.startsWith("approved_answer_") && event.newValue) {
                try {
                    const data = JSON.parse(event.newValue);
                    const { type, sessionId, answer, timestamp } = data;

                    if (
                        type === "approved_answer" &&
                        sessionId === currentSession
                    ) {
                        const approvedMessage: ChatMessage = {
                            id: uuidv4(),
                            role: "assistant",
                            content: answer,
                            timestamp: new Date(timestamp).getTime(),
                            confidence: 1.0,
                            trustLevel: "verified",
                            sourceType: "hitl",
                        };

                        setMessages((prev) => {
                            const alreadyExists = prev.some(
                                (m) =>
                                    m.sourceType === "hitl" &&
                                    m.content === answer
                            );
                            if (alreadyExists) return prev;
                            return [...prev, approvedMessage];
                        });

                        localStorage.removeItem(`approved_answer_${sessionId}`);
                    }
                } catch (err) {
                    // Silently handle storage errors
                }
            }
        };

        window.addEventListener("storage", handleStorage);

        return () => {
            window.removeEventListener("storage", handleStorage);
        };
    }, [botId]);

    // WebSocket for real-time updates (e.g. approved answers from HITL)
    const wsRef = useRef<WebSocket | null>(null);
    const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);

    const connectWebSocket = useCallback(() => {
        if (typeof window === "undefined" || !sessionIdRef.current) return;

        // Avoid duplicate connections
        if (
            wsRef.current &&
            (wsRef.current.readyState === WebSocket.OPEN ||
                wsRef.current.readyState === WebSocket.CONNECTING)
        ) {
            return;
        }

        const getWsUrl = () => {
            const apiUrl =
                process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
            // Check if we need to use a relative path (for proxy) or absolute
            // If API_URL is absolute, replace protocol
            if (apiUrl.startsWith("http")) {
                const wsProtocol = apiUrl.startsWith("https") ? "wss" : "ws";
                const hostPath = apiUrl.replace(/^https?:\/\//, "");
                return `${wsProtocol}://${hostPath}/api/v1/bots/${botId}/chat/ws/${sessionIdRef.current}`;
            }
            // Fallback for relative paths
            const protocol =
                window.location.protocol === "https:" ? "wss:" : "ws:";
            return `${protocol}//${window.location.host}/api/v1/bots/${botId}/chat/ws/${sessionIdRef.current}`;
        };

        const wsUrl = getWsUrl();

        try {
            console.log(`[Chat Debug] Attempting to connect to WebSocket: ${wsUrl}`);
            const ws = new WebSocket(wsUrl);
            wsRef.current = ws;

            ws.onopen = () => {
                console.log("[Chat Debug] WebSocket connected successfully");
            };

            ws.onmessage = (event) => {
                console.log("[Chat Debug] WebSocket message received:", event.data);
                try {
                    const data = JSON.parse(event.data);

                    if (data.type === "approved_answer") {
                        console.log("[Chat Debug] Processing approved answer:", data);
                        setMessages((prev) => {
                            // 1. Try to find and update existing message by ID
                            if (data.message_id) {
                                const exists = prev.find(
                                    (m) => m.id === data.message_id
                                );
                                if (exists) {
                                    console.log("[Chat Debug] Updating existing message:", data.message_id);
                                    return prev.map((m) =>
                                        m.id === data.message_id
                                            ? {
                                                ...m,
                                                content: data.answer,
                                                citations: data.citations || m.citations,
                                                trustLevel: "verified",
                                                sourceType: "hitl",
                                                confidence: 1.0,
                                            }
                                            : m
                                    );
                                }
                            }

                            // 2. Fallback: check for duplication by content
                            const alreadyExists = prev.some(
                                (m) =>
                                    m.sourceType === "hitl" &&
                                    m.content === data.answer
                            );
                            if (alreadyExists) {
                                console.log("[Chat Debug] Duplicate message ignored");
                                return prev;
                            }

                            // 3. Append as new message
                            console.log("[Chat Debug] Appending new message");
                            const newMsg: ChatMessage = {
                                id: data.message_id || uuidv4(),
                                role: "assistant",
                                content: data.answer,
                                timestamp: Date.now(),
                                confidence: 1.0,
                                trustLevel: "verified",
                                sourceType: "hitl",
                                citations: data.citations,
                            };
                            return [...prev, newMsg];
                        });
                    }
                } catch (e) {
                    console.error("[Chat Debug] Error parsing WebSocket message:", e);
                }
            };

            ws.onclose = (e) => {
                console.log("[Chat Debug] WebSocket closed. Code:", e.code, "Reason:", e.reason);
                wsRef.current = null;
                // Reconnect after delay
                reconnectTimeoutRef.current = setTimeout(() => {
                    console.log("[Chat Debug] Attempting reconnect...");
                    connectWebSocket();
                }, 3000);
            };

            ws.onerror = (e) => {
                console.error("[Chat Debug] WebSocket error:", e);
            };
        } catch (e) {
            console.error("[Chat Debug] Exception in connectWebSocket:", e);
        }
    }, [botId]);

    useEffect(() => {
        connectWebSocket();
        return () => {
            if (wsRef.current) {
                wsRef.current.close();
                wsRef.current = null;
            }
            if (reconnectTimeoutRef.current) {
                clearTimeout(reconnectTimeoutRef.current);
            }
        };
    }, [connectWebSocket]);

    const lastQueryRef = useRef<string>("");
    const streamingMessageRef = useRef<ChatMessage | null>(null);
    const contextWindow = useMemo(() => {
        const configured = Number(process.env.NEXT_PUBLIC_CONTEXT_WINDOW);
        if (
            Number.isFinite(configured) &&
            configured > 0 &&
            configured <= 100
        ) {
            return Math.floor(configured);
        }
        return 10;
    }, []);

    // Track if we've processed the approved answer to handle Strict Mode double-renders
    const processedApprovedAnswerRef = useRef<string | null>(null);
    const initialLoadDoneRef = useRef<boolean>(false);

    // Load chat history on mount AND check for pending approved answers
    useEffect(() => {
        // Prevent Strict Mode from running this twice and overwriting messages
        if (initialLoadDoneRef.current) {
            return;
        }

        const sessionId = sessionIdRef.current;
        let history = loadChatHistory(botId, sessionId);

        // Check for pending approved answer in localStorage
        if (sessionId) {
            const approvedKey = `approved_answer_${sessionId}`;
            const stored = localStorage.getItem(approvedKey);
            if (stored) {
                try {
                    const data = JSON.parse(stored);

                    if (
                        data.type === "approved_answer" &&
                        data.sessionId === sessionId
                    ) {
                        // Check if this answer is already in history
                        const alreadyExists = history.some(
                            (m: ChatMessage) =>
                                m.sourceType === "hitl" &&
                                m.content === data.answer
                        );
                        if (!alreadyExists) {
                            const approvedMessage: ChatMessage = {
                                id: uuidv4(),
                                role: "assistant",
                                content: data.answer,
                                timestamp: new Date(data.timestamp).getTime(),
                                confidence: 1.0,
                                trustLevel: "verified",
                                sourceType: "hitl",
                            };
                            history = [...history, approvedMessage];
                            // Mark as processed and remove from localStorage
                            const answerKey = `${data.sessionId}_${data.timestamp}`;
                            processedApprovedAnswerRef.current = answerKey;
                            localStorage.removeItem(approvedKey);
                        }
                    }
                } catch (err) {
                    // Silently handle processing errors
                }
            }
        }

        setMessages(history);
        initialLoadDoneRef.current = true;
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
                // Silently handle parse errors
            }
        }
    }, [botId]);

    // Save chat history whenever messages change

    // Save chat history whenever messages change
    useEffect(() => {
        if (messages.length > 0) {
            saveChatHistory(botId, sessionIdRef.current, messages);
        }
    }, [botId, messages]);

    // Persist feedback state per session
    useEffect(() => {
        if (typeof window === "undefined") return;
        const key = `feedback_state_${botId}_${sessionIdRef.current}`;
        sessionStorage.setItem(key, JSON.stringify(feedbackState));
    }, [feedbackState, botId]);

    // Clear history on page unload

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
                const conversationHistory = messages
                    .slice(-contextWindowSize)
                    .map((msg) => ({
                        role: msg.role,
                        content: msg.content,
                    }));

                // Stream tokens
                let fullContent = "";
                let metadata: any = null;

                for await (const chunk of streamChatQuery(botId, query, {
                    context: contextPayload,
                    contextWindow,
                    sessionId: sessionIdRef.current,
                    messageId: assistantMessage.id,
                    embedOrigin,
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
                        if (metadata?.confidence !== undefined) {
                            lastMsg.confidence = metadata.confidence as number;
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
                            lastMsg.answerId = metadata.response_id;
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
        if (typeof window !== "undefined") {
            sessionStorage.setItem(key, newSessionId);
        }
        setError(null);
        setRetryCount(0);
        setFeedbackState({});
        setFeedbackRateLog([]);
    }, [botId]);

    const startNewSession = useCallback(() => {
        // Just reset the state and generate a new ID, preserving the old history in storage
        setMessages([]);
        const newSessionId = uuidv4();
        sessionIdRef.current = newSessionId;
        const key = `chat_session_${botId}`;
        if (typeof window !== "undefined") {
            sessionStorage.setItem(key, newSessionId);
        }
        setError(null);
        setRetryCount(0);
        setFeedbackState({});
        setFeedbackRateLog([]);
    }, [botId]);

    const resumeSession = useCallback(
        (sessionId: string) => {
            sessionIdRef.current = sessionId;
            const key = `chat_session_${botId}`;
            if (typeof window !== "undefined") {
                sessionStorage.setItem(key, sessionId);
            }
            const history = loadChatHistory(botId, sessionId);
            setMessages(history);
            setError(null);
            setRetryCount(0);
            // Load feedback state for that session if available
            if (typeof window !== "undefined") {
                try {
                    const key = `feedback_state_${botId}_${sessionId}`;
                    const stored = sessionStorage.getItem(key);
                    setFeedbackState(stored ? JSON.parse(stored) : {});
                } catch {
                    setFeedbackState({});
                }
            }
        },
        [botId]
    );

    const submitFeedbackForMessage = useCallback(
        async (params: {
            messageId: string;
            answerId?: string;
            type: FeedbackType;
            reason?: FeedbackReason;
            notes?: string;
        }) => {
            const { messageId, answerId, type, reason, notes } = params;
            if (!answerId) {
                const err = "Missing answer identifier for feedback";
                setFeedbackError(err);

                // Also update the local state for this message so the UI shows the error
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

            // Fast-fail if user is not authenticated (no stored token)
            const token =
                typeof window !== "undefined" ? getAccessToken() : null;
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

            // Retry logic with exponential backoff (3 attempts: 1s, 2s, 4s delays)
            const maxRetries = 3;
            let lastError: any = null;

            for (let attempt = 0; attempt < maxRetries; attempt++) {
                try {
                    // Show "Retrying..." status on retries
                    if (attempt > 0) {
                        setFeedbackState((prev) => ({
                            ...prev,
                            [messageId]: {
                                type,
                                reason,
                                status: "pending",
                                timestamp: Date.now(),
                                message: `Retrying... (attempt ${attempt + 1
                                    }/${maxRetries})`,
                                retryAttempt: attempt,
                            },
                        }));
                    }

                    await submitFeedbackApi(botId, {
                        answer_id: answerId,
                        message_id: messageId,
                        type,
                        reason,
                        additional_notes: notes,
                        session_id: sessionIdRef.current,
                    });

                    // Success - clear retry state
                    setFeedbackState((prev) => ({
                        ...prev,
                        [messageId]: {
                            type,
                            reason,
                            status: "sent",
                            timestamp: Date.now(),
                        },
                    }));

                    return { success: true, retriesUsed: attempt };
                } catch (err: any) {
                    lastError = err;
                    const status = err?.status as number | undefined;

                    // Don't retry on 401 (auth) or 429 (rate limit) - these are client errors
                    if (status === 401 || status === 429) {
                        const message =
                            status === 401
                                ? "Please log in to provide feedback"
                                : "Please wait before providing more feedback";
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
                                    status === 429
                                        ? Date.now() + 60 * 1000
                                        : undefined,
                            },
                        }));
                        return { success: false, error: message };
                    }

                    // On last attempt, give up
                    if (attempt === maxRetries - 1) {
                        const message =
                            err?.message || "Failed to send feedback";
                        setFeedbackError(message);
                        setFeedbackState((prev) => ({
                            ...prev,
                            [messageId]: {
                                type,
                                reason,
                                status: "error",
                                timestamp: Date.now(),
                                message,
                            },
                        }));
                        return {
                            success: false,
                            error: message,
                            retriesExhausted: true,
                        };
                    }

                    // Wait with exponential backoff: 1s, 2s, 4s
                    const delayMs = Math.pow(2, attempt) * 1000;
                    await new Promise((resolve) =>
                        setTimeout(resolve, delayMs)
                    );
                }
            }

            // Fallback (should never reach here)
            const message = lastError?.message || "Failed to send feedback";
            setFeedbackError(message);
            setFeedbackState((prev) => ({
                ...prev,
                [messageId]: {
                    type,
                    reason,
                    status: "error",
                    timestamp: Date.now(),
                    message,
                },
            }));
            return { success: false, error: message };
        },
        [botId, feedbackRateLog]
    );

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
        resumeSession,
        feedbackState,
        feedbackError,
        submitFeedbackForMessage,
        startNewSession,
    };
}
