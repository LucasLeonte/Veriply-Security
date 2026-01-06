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

            const response = await fetch(
                `/api/hitl/queue?${params.toString()}`,
                {
                    method: "GET",
                    headers,
                }
            );

            if (!response.ok) {
                throw new Error(
                    `Failed to fetch HITL queue: ${response.statusText}`
                );
            }

            const data: { items: ReviewQueueItem[]; stats: HITLQueueStats } =
                await response.json();

            setItems(data.items || []);
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
            console.error("Failed to fetch HITL queue:", err);
        } finally {
            setIsLoading(false);
        }
    }, [sortBy, filters]);

    // Fallback polling when WebSocket fails
    const startPolling = useCallback(() => {
        if (pollingIntervalRef.current) {
            return; // Already polling
        }

        console.log(
            "Starting fallback polling for queue updates (every 5 seconds)"
        );

        // Poll every 5 seconds
        pollingIntervalRef.current = setInterval(() => {
            fetchQueue();
        }, 5000);
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
                console.debug("Error closing existing WebSocket:", e);
            }
            wsRef.current = null;
        }

        try {
            const token = getAccessToken();
            if (!token) {
                console.warn(
                    "No auth token available for WebSocket, falling back to polling"
                );
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

            console.log(
                `Attempting WebSocket connection (attempt ${
                    reconnectAttemptsRef.current + 1
                }/${maxReconnectAttemptsRef.current})`
            );

            const ws = new WebSocket(wsUrl);

            // Set a connection timeout
            const connectionTimeout = setTimeout(() => {
                if (ws.readyState === WebSocket.CONNECTING) {
                    console.warn(
                        "WebSocket connection timeout, closing and falling back to polling"
                    );
                    ws.close();
                    startPolling();
                }
            }, 5000); // 5 second timeout

            ws.onopen = () => {
                clearTimeout(connectionTimeout);
                console.log("WebSocket connected successfully");
                reconnectAttemptsRef.current = 0;

                // Clear polling once WebSocket is connected
                if (pollingIntervalRef.current) {
                    clearInterval(pollingIntervalRef.current);
                    pollingIntervalRef.current = null;
                    console.log("Polling stopped, using WebSocket for updates");
                }
            };

            ws.onmessage = (event) => {
                try {
                    const message = JSON.parse(event.data);

                    if (message.type === "heartbeat") {
                        // Keep-alive message, no action needed
                        console.debug("Heartbeat received");
                    } else if (message.type === "queue_update") {
                        // Real-time queue update received
                        console.log("Queue update received:", message.data);

                        if (message.data.action === "item_resolved") {
                            // Item was approved/rejected, refresh queue
                            fetchQueue();
                        } else if (message.data.action === "new_item") {
                            // New item added to queue, refresh queue
                            fetchQueue();
                        }
                    } else if (message.type === "pong") {
                        // Response to our ping, connection is alive
                        console.debug("Pong received");
                    }
                } catch (err) {
                    console.error("Failed to parse WebSocket message:", err);
                }
            };

            ws.onerror = (event) => {
                clearTimeout(connectionTimeout);
                // Browser provides limited error information for security reasons
                const readyStateText =
                    ["CONNECTING", "OPEN", "CLOSING", "CLOSED"][
                        ws.readyState
                    ] || "UNKNOWN";
                console.error("WebSocket connection error:", {
                    readyState: ws.readyState,
                    readyStateText,
                    url: wsUrl.replace(/token=[^&]+/, "token=***"), // Hide token in logs
                    timestamp: new Date().toISOString(),
                });

                // If error occurs during connection (readyState 0), start polling immediately
                if (
                    ws.readyState === WebSocket.CONNECTING ||
                    ws.readyState === WebSocket.CLOSED
                ) {
                    console.warn(
                        "WebSocket failed to connect, falling back to polling"
                    );
                    startPolling();
                }
            };

            ws.onclose = (event) => {
                clearTimeout(connectionTimeout);
                console.log("WebSocket closed:", {
                    code: event.code,
                    reason: event.reason || "No reason provided",
                    wasClean: event.wasClean,
                });
                wsRef.current = null;

                // Don't reconnect if connection was closed intentionally (clean close)
                if (event.wasClean) {
                    console.log("WebSocket closed cleanly, not reconnecting");
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

                    console.log(
                        `WebSocket will reconnect in ${delay}ms (attempt ${reconnectAttemptsRef.current}/${maxReconnectAttemptsRef.current})`
                    );

                    setTimeout(() => {
                        connectWebSocket();
                    }, delay);
                } else {
                    // Max reconnect attempts reached, fall back to polling
                    console.warn(
                        "Max WebSocket reconnect attempts reached, falling back to polling"
                    );
                    startPolling();
                }
            };

            wsRef.current = ws;
        } catch (err) {
            console.error("Failed to create WebSocket:", err);
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
                console.log(
                    "WebSocket not connected after 3 seconds, starting polling fallback"
                );
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

            const response = await fetch(`/api/hitl/queue/${itemId}/approve`, {
                method: "POST",
                headers,
                body: JSON.stringify({ edits }),
            });

            if (!response.ok) {
                throw new Error("Failed to approve item");
            }

            // Remove item from local state immediately for optimistic update
            setItems((prev) => prev.filter((item) => item.id !== itemId));

            // Refresh queue from server
            fetchQueue();
        } catch (err) {
            console.error("Failed to approve item:", err);
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

            const response = await fetch(`/api/hitl/queue/${itemId}/reject`, {
                method: "POST",
                headers,
                body: JSON.stringify({ reason }),
            });

            if (!response.ok) {
                throw new Error("Failed to reject item");
            }

            // Remove item from local state immediately for optimistic update
            setItems((prev) => prev.filter((item) => item.id !== itemId));

            // Refresh queue from server
            fetchQueue();
        } catch (err) {
            console.error("Failed to reject item:", err);
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
