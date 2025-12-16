import { useEffect, useState } from "react";

export interface ReviewQueueItem {
    id: string;
    type: "chat" | "email";
    timestamp: string;
    userQuestion: string;
    aiDraft: string;
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

export function useHITLQueue() {
    const [items, setItems] = useState<ReviewQueueItem[]>([]);
    const [stats, setStats] = useState<HITLQueueStats>({
        total: 0,
        pending: 0,
        chat: 0,
        email: 0,
    });
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<Error | null>(null);

    useEffect(() => {
        const fetchQueue = async () => {
            try {
                setIsLoading(true);
                setError(null);

                const response = await fetch(`/api/hitl/queue`, {
                    method: "GET",
                    headers: {
                        "Content-Type": "application/json",
                    },
                });

                if (!response.ok) {
                    throw new Error(`Failed to fetch HITL queue: ${response.statusText}`);
                }

                const data: { items: ReviewQueueItem[]; stats: HITLQueueStats } =
                    await response.json();

                setItems(data.items || []);
                setStats(data.stats || {
                    total: 0,
                    pending: 0,
                    chat: 0,
                    email: 0,
                });
            } catch (err) {
                setError(err instanceof Error ? err : new Error("Unknown error"));
                console.error("Failed to fetch HITL queue:", err);
            } finally {
                setIsLoading(false);
            }
        };

        fetchQueue();
    }, []);

    const approveItem = async (itemId: string, edits?: string) => {
        try {
            const response = await fetch(`/api/hitl/queue/${itemId}/approve`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({ edits }),
            });

            if (!response.ok) {
                throw new Error("Failed to approve item");
            }

            setItems((prev) =>
                prev.map((item) =>
                    item.id === itemId ? { ...item, status: "approved" } : item
                )
            );
        } catch (err) {
            console.error("Failed to approve item:", err);
            throw err;
        }
    };

    const rejectItem = async (itemId: string, reason?: string) => {
        try {
            const response = await fetch(`/api/hitl/queue/${itemId}/reject`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({ reason }),
            });

            if (!response.ok) {
                throw new Error("Failed to reject item");
            }

            setItems((prev) =>
                prev.map((item) =>
                    item.id === itemId ? { ...item, status: "rejected" } : item
                )
            );
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
    };
}
