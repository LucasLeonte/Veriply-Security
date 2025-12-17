"use client";

import { useMemo, useState } from "react";
import { ThumbsUp, ThumbsDown, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import FeedbackReasonModal from "./FeedbackReasonModal";
import { FeedbackReason, FeedbackType } from "@/lib/api/feedback";

export type FeedbackSnapshot = {
    type: FeedbackType;
    reason?: FeedbackReason;
    status: "idle" | "pending" | "sent" | "error" | "cooldown";
    timestamp: number;
    message?: string;
    cooldownUntil?: number;
};

interface FeedbackBarProps {
    messageId: string;
    answerId?: string;
    state?: FeedbackSnapshot;
    onSubmit: (args: {
        messageId: string;
        answerId?: string;
        type: FeedbackType;
        reason?: FeedbackReason;
        notes?: string;
    }) => Promise<{ success: boolean; error?: string } | void>;
}

export function FeedbackBar({
    messageId,
    answerId,
    state,
    onSubmit,
}: FeedbackBarProps) {
    const [modalOpen, setModalOpen] = useState(false);
    const isPending = state?.status === "pending";
    const isCooldown = state?.status === "cooldown" && !!state?.cooldownUntil && state.cooldownUntil > Date.now();

    const currentMessage = useMemo(() => {
        if (state?.message) return state.message;
        if (state?.status === "sent") return "Thank you for the feedback!";
        if (state?.status === "error") return "Could not send feedback";
        if (isCooldown) return "Please wait before providing more feedback";
        return "";
    }, [state, isCooldown]);

    const handlePositive = async () => {
        await onSubmit({ messageId, answerId, type: "positive" });
    };

    const handleNegative = async () => {
        setModalOpen(true);
    };

    const handleSubmitReason = async (reason: FeedbackReason, notes?: string) => {
        await onSubmit({ messageId, answerId, type: "negative", reason, notes });
    };

    const selectedType = state?.type;

    return (
        <div className="mt-3 flex items-center gap-3 text-xs text-slate-600">
            <div className="flex items-center gap-1">
                <Button
                    size="sm"
                    variant={selectedType === "positive" ? "secondary" : "ghost"}
                    onClick={handlePositive}
                    disabled={isPending || isCooldown}
                    title="Helpful response"
                    aria-label="Helpful response"
                >
                    {isPending && selectedType === "positive" ? (
                        <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                        <ThumbsUp className="h-4 w-4" />
                    )}
                </Button>
                <Button
                    size="sm"
                    variant={selectedType === "negative" ? "secondary" : "ghost"}
                    onClick={handleNegative}
                    disabled={isPending || isCooldown}
                    title="Not helpful"
                    aria-label="Not helpful"
                >
                    {isPending && selectedType === "negative" ? (
                        <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                        <ThumbsDown className="h-4 w-4" />
                    )}
                </Button>
            </div>

            {currentMessage && (
                <span className="text-slate-500">{currentMessage}</span>
            )}

            <FeedbackReasonModal
                open={modalOpen}
                onClose={() => setModalOpen(false)}
                onSubmit={handleSubmitReason}
                pending={isPending}
            />
        </div>
    );
}

export default FeedbackBar;