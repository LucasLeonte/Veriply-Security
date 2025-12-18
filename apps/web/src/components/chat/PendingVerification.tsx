"use client";

import { useState, useEffect } from "react";
import { Loader2, CheckCircle } from "lucide-react";
import TrustBadge from "./TrustBadge";
import { ChatMessage } from "@/types/chat";

interface PendingVerificationProps {
    messageId: string;
    botId: string;
    onVerified?: (response: ChatMessage) => void;
    estimatedWaitTime?: string;
}

export default function PendingVerification({
    messageId,
    botId,
    onVerified,
    estimatedWaitTime = "Usually within 5 minutes",
}: PendingVerificationProps) {
    const [status, setStatus] = useState<"pending" | "resolved" | "error">(
        "pending"
    );
    const [resolvedResponse, setResolvedResponse] = useState<ChatMessage | null>(
        null
    );
    const [error, setError] = useState<string | null>(null);

    // Poll for verification status
    useEffect(() => {
        const pollInterval = setInterval(async () => {
            try {
                const response = await fetch(
                    `/api/v1/bots/${botId}/chat/${messageId}/status`
                );

                if (!response.ok) {
                    throw new Error(`Status check failed: ${response.status}`);
                }

                const data = await response.json();

                if (data.status === "resolved" && data.response) {
                    setStatus("resolved");
                    setResolvedResponse(data.response);
                    onVerified?.(data.response);
                    clearInterval(pollInterval);
                }
            } catch (err) {
                console.error("Error polling verification status:", err);
                setStatus("error");
                setError(
                    err instanceof Error ? err.message : "Unknown error"
                );
                clearInterval(pollInterval);
            }
        }, 2000); // Poll every 2 seconds

        return () => clearInterval(pollInterval);
    }, [messageId, botId, onVerified]);

    if (status === "resolved") {
        return (
            <div className="flex flex-col gap-3">
                <div className="flex items-center gap-2 px-4 py-2.5 bg-green-50 border border-green-200 rounded text-sm text-green-800">
                    <CheckCircle className="w-4 h-4 flex-shrink-0" />
                    <span>✓ We have an answer for you!</span>
                </div>
                {resolvedResponse && (
                    <div className="px-4 py-2 bg-white border border-slate-100 rounded-lg shadow-sm">
                        <div className="prose prose-sm max-w-none text-slate-800">
                            {resolvedResponse.content}
                        </div>
                        {resolvedResponse.trustLevel && (
                            <div className="mt-3 pt-3 border-t border-slate-100">
                                <TrustBadge
                                    trustLevel={resolvedResponse.trustLevel}
                                    confidenceScore={
                                        resolvedResponse.confidenceScore
                                    }
                                />
                            </div>
                        )}
                    </div>
                )}
            </div>
        );
    }

    if (status === "error") {
        return (
            <div className="flex flex-col gap-3 px-4 py-3 bg-red-50 border border-red-200 rounded text-sm text-red-800">
                <div>
                    <strong>Error:</strong> {error}
                </div>
                <p className="text-xs text-red-700">
                    Please try asking again or refresh the page.
                </p>
            </div>
        );
    }

    return (
        <div className="flex flex-col gap-3 px-4 py-3 bg-blue-50 border border-blue-200 rounded-lg">
            <div className="flex items-center gap-2">
                <Loader2 className="w-4 h-4 animate-spin text-blue-600 flex-shrink-0" />
                <div className="flex-1">
                    <p className="text-sm font-medium text-blue-900">
                        I'm checking with the team.
                    </p>
                    <p className="text-xs text-blue-700 mt-1">
                        You'll receive a verified response shortly.
                    </p>
                </div>
            </div>
            {estimatedWaitTime && (
                <p className="text-xs text-blue-700 ml-6">
                    {estimatedWaitTime}
                </p>
            )}
        </div>
    );
}
