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
        <div className="mt-2 flex items-center gap-2">
            <div className="flex items-center bg-slate-50 border border-slate-200 rounded-full p-0.5 shadow-sm">
                <Button
                    size="sm"
                    variant={selectedType === "positive" ? "default" : "ghost"}
                    onClick={handlePositive}
                    disabled={isPending || isCooldown}
                    className={`h-6 w-8 rounded-l-full rounded-r-none transition-all ${selectedType === "positive"
                            ? "bg-green-600 hover:bg-green-700 text-white"
                            : "text-slate-500 hover:text-slate-700 hover:bg-slate-100"
                        }`}
                    title="Helpful response"
                    aria-label="Helpful response"
                >
                    {isPending && selectedType === "positive" ? (
                        <Loader2 className="h-3 w-3 animate-spin" />
                    ) : (
                        <ThumbsUp className="h-3 w-3" />
                    )}
                </Button>
                <div className="w-px h-3 bg-slate-200" />
                <Button
                    size="sm"
                    variant={selectedType === "negative" ? "default" : "ghost"}
                    onClick={handleNegative}
                    disabled={isPending || isCooldown}
                    className={`h-6 w-8 rounded-l-none rounded-r-full transition-all ${selectedType === "negative"
                            ? "bg-red-600 hover:bg-red-700 text-white"
                            : "text-slate-500 hover:text-slate-700 hover:bg-slate-100"
                        }`}
                    title="Not helpful"
                    aria-label="Not helpful"
                >
                    {isPending && selectedType === "negative" ? (
                        <Loader2 className="h-3 w-3 animate-spin" />
                    ) : (
                        <ThumbsDown className="h-3 w-3" />
                    )}
                </Button>
            </div>

            {currentMessage && (
                <span className={`text-[10px] font-medium animate-in fade-in slide-in-from-left-2 duration-300 ${state?.status === "error" ? "text-red-500" :
                        state?.status === "sent" ? "text-green-600" : "text-slate-400"
                    }`}>
                    {currentMessage}
                </span>
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