"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { DashboardLayout } from "@/components";
import { ReviewInterfaceDetail } from "@/components/hitl/ReviewInterfaceDetail";
import { getAccessToken } from "@/lib/auth";

import type { ReviewQueueItemDetail } from "@/types/hitl";

export default function ReviewItemPage() {
    const params = useParams();
    const router = useRouter();
    const itemId = params?.itemId as string;
    
    const [item, setItem] = useState<ReviewQueueItemDetail | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        if (!itemId) return;
        
        const fetchItemDetail = async () => {
            try {
                setIsLoading(true);
                setError(null);
                
                const token = getAccessToken();
                const headers: Record<string, string> = {
                    "Content-Type": "application/json",
                };
                if (token) {
                    headers.Authorization = `Bearer ${token}`;
                }
                
                const response = await fetch(`/api/hitl/queue/${itemId}`, {
                    method: "GET",
                    headers,
                });
                
                if (!response.ok) {
                    throw new Error(`Failed to fetch item: ${response.statusText}`);
                }
                
                const data = await response.json();
                setItem(data);
            } catch (err) {
                console.error("Failed to fetch item detail:", err);
                setError(err instanceof Error ? err.message : "Unknown error");
            } finally {
                setIsLoading(false);
            }
        };
        
        fetchItemDetail();
    }, [itemId]);

    const handleApprove = async (edits?: string) => {
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
            
            // Navigate back to queue
            router.push("/inbox");
        } catch (err) {
            console.error("Failed to approve item:", err);
            throw err;
        }
    };

    const handleReject = async (reason?: string) => {
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
            
            // Navigate back to queue
            router.push("/inbox");
        } catch (err) {
            console.error("Failed to reject item:", err);
            throw err;
        }
    };

    if (isLoading) {
        return (
            <DashboardLayout>
                <div className="flex items-center justify-center h-screen">
                    <div className="text-slate-600">Loading item details...</div>
                </div>
            </DashboardLayout>
        );
    }

    if (error || !item) {
        return (
            <DashboardLayout>
                <div className="space-y-6">
                    <h2 className="text-2xl font-semibold text-slate-900">
                        Review Item
                    </h2>
                    <div className="bg-white rounded-lg border border-red-200 p-6 text-red-600">
                        <p>Error: {error || "Item not found"}</p>
                    </div>
                </div>
            </DashboardLayout>
        );
    }

    return (
        <DashboardLayout>
            <ReviewInterfaceDetail
                item={item}
                onApprove={handleApprove}
                onReject={handleReject}
                onBack={() => router.push("/inbox")}
            />
        </DashboardLayout>
    );
}
