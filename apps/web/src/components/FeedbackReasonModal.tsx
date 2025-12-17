"use client";

import { useEffect, useState } from "react";
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogHeader,
    DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { FeedbackReason } from "@/lib/api/feedback";

interface FeedbackReasonModalProps {
    open: boolean;
    onClose: () => void;
    onSubmit: (reason: FeedbackReason, notes?: string) => Promise<void> | void;
    pending?: boolean;
}

const REASONS: { value: FeedbackReason; label: string }[] = [
    { value: "incorrect", label: "Incorrect information" },
    { value: "not_helpful", label: "Not helpful / Irrelevant" },
    { value: "incomplete", label: "Incomplete answer" },
    { value: "harmful", label: "Harmful or unsafe" },
    { value: "other", label: "Other" },
];

export function FeedbackReasonModal({
    open,
    onClose,
    onSubmit,
    pending,
}: FeedbackReasonModalProps) {
    const [reason, setReason] = useState<FeedbackReason | undefined>();
    const [notes, setNotes] = useState("");
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        if (!open) {
            setReason(undefined);
            setNotes("");
            setError(null);
        }
    }, [open]);

    const handleSubmit = async () => {
        if (!reason) {
            setError("Please select a reason");
            return;
        }
        if (reason === "other" && notes.trim().length < 10) {
            setError("Please provide at least 10 characters for Other");
            return;
        }
        setError(null);
        await onSubmit(reason, notes.trim() || undefined);
        onClose();
    };

    return (
        <Dialog open={open} onOpenChange={(value) => !value && onClose()}>
            <DialogContent>
                <DialogHeader>
                    <DialogTitle>What was wrong?</DialogTitle>
                    <DialogDescription>
                        Help us improve responses by sharing why this answer was
                        not helpful.
                    </DialogDescription>
                </DialogHeader>

                <div className="space-y-3 mt-2">
                    {REASONS.map((item) => (
                        <label
                            key={item.value}
                            className="flex items-center gap-2 text-sm text-slate-800"
                        >
                            <input
                                type="radio"
                                name="feedback-reason"
                                value={item.value}
                                checked={reason === item.value}
                                onChange={() => setReason(item.value)}
                                className="h-4 w-4"
                            />
                            <span>{item.label}</span>
                        </label>
                    ))}

                    {reason === "other" && (
                        <div className="space-y-1">
                            <Label htmlFor="feedback-notes">Tell us more...</Label>
                            <Input
                                id="feedback-notes"
                                placeholder="Tell us more..."
                                maxLength={500}
                                value={notes}
                                onChange={(e) => setNotes(e.target.value)}
                            />
                            <p className="text-xs text-slate-500">
                                {notes.length}/500 characters
                            </p>
                        </div>
                    )}

                    {error && (
                        <p className="text-sm text-red-600" role="alert">
                            {error}
                        </p>
                    )}
                </div>

                <div className="flex justify-end gap-2 mt-4">
                    <Button
                        variant="outline"
                        type="button"
                        onClick={onClose}
                        disabled={pending}
                    >
                        Cancel
                    </Button>
                    <Button
                        type="button"
                        onClick={handleSubmit}
                        disabled={pending}
                    >
                        Send Feedback
                    </Button>
                </div>
            </DialogContent>
        </Dialog>
    );
}

export default FeedbackReasonModal;