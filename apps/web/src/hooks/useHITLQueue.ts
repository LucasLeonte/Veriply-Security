import { useEffect, useState, useRef, useCallback } from "react";
import { getAccessToken } from "@/lib/auth";

export interface ReviewQueueItem {
    id: string;
    type: "chat" | "email";
    timestamp: string;
    userQuestion: string;
    aiDraft: string;
    botName: string;
    confidence: number;
    citations: Array<{
        source: string;
        relevance: number;
    }>;
    status: "pending" | "reviewing" | "approved" | "rejected";
    source?: string;
    metadata?: Record<string, unknown>;
}

export interface HITLQueueStats {
    total: number;
    pending: number;
    chat: number;
    email: number;
}

export interface HITLQueueFilters {
    groupId?: string;
    botId?: string;
    dateFrom?: string; // ISO date string
    dateTo?: string; // ISO date string
    status?: "pending" | "in-progress";
}

export function useHITLQueue(
    sortBy: string = "oldest",
    filters?: HITLQueueFilters
) {
    const [items, setItems] = useState<ReviewQueueItem[]>([]);
    const [stats, setStats] = useState<HITLQueueStats>({
        total: 0,
        pending: 0,
        chat: 0,
        email: 0,
    });
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<Error | null>(null);

    // WebSocket and polling state
    const wsRef = useRef<WebSocket | null>(null);
    const pollingIntervalRef = useRef<NodeJS.Timeout | null>(null);
    const reconnectAttemptsRef = useRef(0);
    const maxReconnectAttemptsRef = useRef(5);

    // Fetch queue data from REST API
    const fetchQueue = useCallback(async () => {
        try {
            setError(null);

            const token = getAccessToken();
            const headers: Record<string, string> = {
                "Content-Type": "application/json",
            };
            if (token) {
                headers.Authorization = `Bearer ${token}`;
            }

            // Build query parameters with filters (AC 5.5)
            const params = new URLSearchParams({ sort_by: sortBy });
            if (filters?.groupId) {
                params.append("group_id", filters.groupId);
            }
            if (filters?.botId) {
                params.append("bot_id", filters.botId);
            }
            if (filters?.dateFrom) {
                params.append("date_from", filters.dateFrom);
            }
            if (filters?.dateTo) {
                params.append("date_to", filters.dateTo);
            }
            if (filters?.status) {
                params.append("status_filter", filters.status);
            }

            // Add cache busting timestamp
            params.set("_t", Date.now().toString());

            const response = await fetch(
                `/api/hitl/queue?${params.toString()}`,
                {
                    method: "GET",
                    headers,
                    cache: "no-store",
                }
            );

            if (!response.ok) {
                throw new Error(
                    `Failed to fetch HITL queue: ${response.statusText}`
                );
            }

            const data: { items: ReviewQueueItem[]; stats: HITLQueueStats } =
                await response.json();

            // Defensive filtering: remove any items that should be resolved
            // (safety check in case backend returns stale data)
            const validItems = (data.items || []).filter((item) => {
                // Filter out items with resolution_action in metadata
                const hasResolution = item.metadata?.resolution_action;
                return item.status === "pending" && !hasResolution;
            });

            setItems(validItems);
            setStats(
                data.stats || {
                    total: 0,
                    pending: 0,
                    chat: 0,
                    email: 0,
                }
            );

            // Reset reconnect attempts on successful fetch
            reconnectAttemptsRef.current = 0;
        } catch (err) {
            setError(err instanceof Error ? err : new Error("Unknown error"));
        } finally {
            setIsLoading(false);
        }
    }, [
        sortBy,
        filters?.groupId,
        filters?.botId,
        filters?.dateFrom,
        filters?.dateTo,
        filters?.status,
    ]);

    // Fallback polling when WebSocket fails
    const startPolling = useCallback(() => {
        if (pollingIntervalRef.current) {
            return; // Already polling
        }

        // Use longer polling interval (30 seconds) to reduce server load
        // WebSocket is preferred for real-time updates
        const pollingInterval = 30000; // 30 seconds instead of 5 seconds

        // Poll at longer interval
        pollingIntervalRef.current = setInterval(() => {
            fetchQueue();
        }, pollingInterval);
    }, [fetchQueue]);

    // Connect to WebSocket for real-time updates
    const connectWebSocket = useCallback(() => {
        if (wsRef.current?.readyState === WebSocket.OPEN) {
            return; // Already connected
        }

        // Close any existing connection before creating a new one
        if (wsRef.current) {
            try {
                wsRef.current.close();
            } catch (e) {
                // Silently handle close errors
            }
            wsRef.current = null;
        }

        try {
            const token = getAccessToken();
            if (!token) {
                startPolling();
                return;
            }

            // Determine WebSocket protocol based on current page
            const protocol =
                window.location.protocol === "https:" ? "wss:" : "ws:";

            // For development: connect to backend directly on localhost:8000
            // For production: use the same host as the current page
            const isLocalhost =
                window.location.hostname === "localhost" ||
                window.location.hostname === "127.0.0.1" ||
                window.location.hostname === "0.0.0.0";

            let wsHost: string;
            if (isLocalhost) {
                // In development, backend is on port 8000
                wsHost = "localhost:8000";
            } else {
                // In production, backend is on the same host as frontend
                wsHost = window.location.host;
            }

            const wsUrl = `${protocol}//${wsHost}/api/v1/hitl/ws/queue?token=${encodeURIComponent(
                token
            )}`;

            const ws = new WebSocket(wsUrl);

            // Set a connection timeout
            const connectionTimeout = setTimeout(() => {
                if (ws.readyState === WebSocket.CONNECTING) {
                    ws.close();
                    startPolling();
                }
            }, 5000); // 5 second timeout

            ws.onopen = () => {
                clearTimeout(connectionTimeout);
                reconnectAttemptsRef.current = 0;

                // Clear polling once WebSocket is connected
                if (pollingIntervalRef.current) {
                    clearInterval(pollingIntervalRef.current);
                    pollingIntervalRef.current = null;
                }
            };

            ws.onmessage = (event) => {
                try {
                    const message = JSON.parse(event.data);

                    if (message.type === "heartbeat") {
                        // Keep-alive message, no action needed
                    } else if (message.type === "queue_update") {
                        // Real-time queue update received
                        if (message.data.action === "item_resolved") {
                            // Item was approved/rejected - remove immediately from local state
                            if (message.data.item_id) {
                                setItems((prev) =>
                                    prev.filter(
                                        (i) => i.id !== message.data.item_id
                                    )
                                );
                            }
                            // Then refresh queue for stats update
                            fetchQueue();
                        } else if (message.data.action === "new_item") {
                            // New item added to queue, refresh queue
                            fetchQueue();
                        }
                    } else if (message.type === "pong") {
                        // Response to our ping, connection is alive
                    }
                } catch (err) {
                    // Silently handle parse errors
                }
            };

            ws.onerror = (event: Event) => {
                clearTimeout(connectionTimeout);
                // If error occurs during connection (readyState 0), start polling immediately
                if (
                    ws.readyState === WebSocket.CONNECTING ||
                    ws.readyState === WebSocket.CLOSED
                ) {
                    startPolling();
                }
            };

            ws.onclose = (event) => {
                clearTimeout(connectionTimeout);
                wsRef.current = null;

                // Don't reconnect if connection was closed intentionally (clean close)
                if (event.wasClean) {
                    return;
                }

                // Attempt to reconnect with exponential backoff
                if (
                    reconnectAttemptsRef.current <
                    maxReconnectAttemptsRef.current
                ) {
                    const delay = Math.min(
                        1000 * Math.pow(2, reconnectAttemptsRef.current),
                        30000
                    );
                    reconnectAttemptsRef.current += 1;

                    setTimeout(() => {
                        connectWebSocket();
                    }, delay);
                } else {
                    // Max reconnect attempts reached, fall back to polling
                    startPolling();
                }
            };

            wsRef.current = ws;
        } catch (err) {
            startPolling();
        }
    }, [fetchQueue, startPolling]);

    // Initial setup: fetch queue and connect WebSocket
    useEffect(() => {
        setIsLoading(true);
        fetchQueue();

        // Attempt WebSocket connection after initial data fetch
        // Use a small delay to allow component to settle
        const wsTimeout = setTimeout(() => {
            connectWebSocket();
        }, 100);

        // If WebSocket fails to connect within reasonable time, start polling as fallback
        const pollFallbackTimeout = setTimeout(() => {
            if (
                wsRef.current?.readyState !== WebSocket.OPEN &&
                !pollingIntervalRef.current
            ) {
                startPolling();
            }
        }, 3000);

        return () => {
            clearTimeout(wsTimeout);
            clearTimeout(pollFallbackTimeout);
        };
    }, [fetchQueue, connectWebSocket, startPolling]);

    // Refetch when sortBy changes
    useEffect(() => {
        fetchQueue();
    }, [sortBy]);

    // Cleanup on unmount
    useEffect(() => {
        return () => {
            // Close WebSocket
            if (wsRef.current) {
                wsRef.current.close();
                wsRef.current = null;
            }

            // Clear polling
            if (pollingIntervalRef.current) {
                clearInterval(pollingIntervalRef.current);
                pollingIntervalRef.current = null;
            }
        };
    }, []);

    const approveItem = async (itemId: string, edits?: string) => {
        try {
            const token = getAccessToken();
            const headers: Record<string, string> = {
                "Content-Type": "application/json",
            };
            if (token) {
                headers.Authorization = `Bearer ${token}`;
            }

            // Find the item to get its metadata (contains session_id)
            const item = items.find((i) => i.id === itemId);

            // IMMEDIATELY remove from local state (optimistic update)
            setItems((prev) => prev.filter((i) => i.id !== itemId));

            const response = await fetch(
                `${
                    process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"
                }/api/v1/hitl/queue/${itemId}/approve?_t=${Date.now()}`,
                {
                    method: "POST",
                    headers,
                    body: JSON.stringify({ edits, send_to_chat: true }),
                    cache: "no-store",
                }
            );

            if (!response.ok) {
                // Revert optimistic update on error
                await fetchQueue();
                throw new Error("Failed to approve item");
            }

            const result = await response.json();

            // Store approved answer in localStorage for the chat to pick up
            // This works for both same-tab navigation and cross-tab communication
            if (typeof window !== "undefined" && item?.metadata) {
                const sessionId = (item.metadata as Record<string, unknown>)
                    .session_id;
                if (sessionId && typeof sessionId === "string") {
                    const approvedAnswer = {
                        type: "approved_answer",
                        sessionId,
                        answer: result.resolved_answer || edits || item.aiDraft,
                        question: item.userQuestion,
                        timestamp: new Date().toISOString(),
                    };
                    // Store in localStorage - this triggers storage event in other tabs
                    // and can be read when navigating back to chat in same tab
                    localStorage.setItem(
                        `approved_answer_${sessionId}`,
                        JSON.stringify(approvedAnswer)
                    );
                }
            }

            // Wait 200ms for database commit to complete before refetching
            await new Promise((resolve) => setTimeout(resolve, 200));

            // Refresh from server to ensure stats are updated
            await fetchQueue();
        } catch (err) {
            throw err;
        }
    };

    const rejectItem = async (itemId: string, reason?: string) => {
        try {
            const token = getAccessToken();
            const headers: Record<string, string> = {
                "Content-Type": "application/json",
            };
            if (token) {
                headers.Authorization = `Bearer ${token}`;
            }

            // IMMEDIATELY remove from local state (optimistic update)
            setItems((prev) => prev.filter((i) => i.id !== itemId));

            const response = await fetch(
                `${
                    process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"
                }/api/v1/hitl/queue/${itemId}/reject?_t=${Date.now()}`,
                {
                    method: "POST",
                    headers,
                    body: JSON.stringify({ reason }),
                    cache: "no-store",
                }
            );

            if (!response.ok) {
                // Revert optimistic update on error
                await fetchQueue();
                throw new Error("Failed to reject item");
            }

            // Wait 200ms for database commit to complete before refetching
            await new Promise((resolve) => setTimeout(resolve, 200));

            // Refresh from server to ensure stats are updated
            await fetchQueue();
        } catch (err) {
            throw err;
        }
    };

    return {
        items,
        stats,
        isLoading,
        error,
        approveItem,
        rejectItem,
        refetch: fetchQueue,
    };
}
