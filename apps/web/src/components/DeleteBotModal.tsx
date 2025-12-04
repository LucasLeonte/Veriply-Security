"use client";

import React, { useState, useEffect } from "react";
import {
    Dialog,
    DialogContent,
    DialogHeader,
    DialogTitle,
    DialogDescription,
} from "@/components/ui/dialog";
import { Bot } from "@/types/bot";
import { useDeleteBot } from "@/hooks/useBotsQuery";
import { AlertCircle, Loader, Trash2 } from "lucide-react";

interface DeleteBotModalProps {
    isOpen: boolean;
    bot: Bot | null;
    onClose: () => void;
    onSuccess: () => void;
    onError?: (error: string) => void;
}

export function DeleteBotModal({
    isOpen,
    bot,
    onClose,
    onSuccess,
    onError,
}: DeleteBotModalProps) {
    const [confirmName, setConfirmName] = useState("");
    const [generalError, setGeneralError] = useState("");
    const { mutate, isPending } = useDeleteBot();

    // Reset form when modal opens/closes
    useEffect(() => {
        if (isOpen) {
            // eslint-disable-next-line react-hooks/set-state-in-effect
            setConfirmName("");
            setGeneralError("");
        }
    }, [isOpen]);

    const isConfirmationValid = bot && confirmName === bot.name;

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setGeneralError("");

        if (!bot || !isConfirmationValid) {
            setGeneralError("Please type the bot name exactly to confirm");
            return;
        }

        try {
            await mutate(bot.id);
            onSuccess();
            setConfirmName("");
            onClose();

            // Show success toast (would integrate with toast library)
            console.log(`Bot deleted: ${bot.name}`);
        } catch (err) {
            const errorMessage =
                err instanceof Error ? err.message : "Failed to delete bot";
            setGeneralError(errorMessage);
            onError?.(errorMessage);
        }
    };

    if (!bot) return null;

    return (
        <Dialog open={isOpen} onOpenChange={onClose}>
            <DialogContent className="sm:max-w-md w-full">
                <DialogHeader>
                    <DialogTitle>
                        <div className="flex items-center gap-2 text-red-600">
                            <Trash2 size={20} />
                            Delete Bot
                        </div>
                    </DialogTitle>
                    <DialogDescription>
                        This action cannot be undone. This will permanently
                        delete the bot &quot;{bot.name}&quot; and all associated data.
                    </DialogDescription>
                </DialogHeader>

                <form onSubmit={handleSubmit} className="space-y-4">
                    {/* General Error */}
                    {generalError && (
                        <div className="flex items-center gap-2 p-3 bg-red-50 border border-red-200 rounded text-red-700 text-sm">
                            <AlertCircle size={16} />
                            <span>{generalError}</span>
                        </div>
                    )}

                    {/* Warning Box */}
                    <div className="p-4 bg-red-50 border border-red-200 rounded">
                        <p className="font-medium text-red-900 mb-2">
                            ⚠️ Warning: Permanent Deletion
                        </p>
                        <ul className="space-y-1 text-sm text-red-700">
                            <li>✓ Bot record will be deleted</li>
                            <li>
                                ✓ All {bot.doc_count ?? 0} documents will be
                                removed
                            </li>
                            <li>✓ All embeddings will be deleted</li>
                            <li>✓ Chat history will be cleared</li>
                        </ul>
                    </div>

                    {/* Confirmation Input */}
                    <div>
                        <label
                            htmlFor="confirm-name"
                            className="block text-sm font-medium text-gray-700"
                        >
                            To confirm, type the bot name:{" "}
                            <span className="font-bold">{bot.name}</span>
                        </label>
                        <input
                            id="confirm-name"
                            type="text"
                            value={confirmName}
                            onChange={(e) => setConfirmName(e.target.value)}
                            placeholder={bot.name}
                            className={`mt-2 w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-red-500 ${confirmName && !isConfirmationValid
                                ? "border-red-500"
                                : "border-gray-300"
                                }`}
                            disabled={isPending}
                            autoFocus
                        />
                        {confirmName && !isConfirmationValid && (
                            <p className="mt-1 text-sm text-red-600">
                                Name doesn&apos;t match. Please type exactly:{" "}
                                {bot.name}
                            </p>
                        )}
                    </div>

                    {/* Buttons */}
                    <div className="flex justify-end gap-3 pt-4">
                        <button
                            type="button"
                            onClick={onClose}
                            className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
                            disabled={isPending}
                        >
                            Cancel
                        </button>
                        <button
                            type="submit"
                            className="px-4 py-2 text-sm font-medium text-white bg-red-600 rounded-md hover:bg-red-700 disabled:bg-red-400 flex items-center gap-2"
                            disabled={!isConfirmationValid || isPending}
                        >
                            {isPending && (
                                <Loader size={16} className="animate-spin" />
                            )}
                            {isPending ? "Deleting..." : "Delete Bot"}
                        </button>
                    </div>
                </form>
            </DialogContent>
        </Dialog>
    );
}
