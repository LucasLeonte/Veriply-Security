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
import { useDuplicateBot } from "@/hooks/useBotsQuery";
import { AlertCircle, Loader, Copy } from "lucide-react";

interface DuplicateBotModalProps {
    isOpen: boolean;
    bot: Bot | null;
    onClose: () => void;
    onSuccess: (bot: Bot) => void;
    onError?: (error: string) => void;
}

export function DuplicateBotModal({
    isOpen,
    bot,
    onClose,
    onSuccess,
    onError,
}: DuplicateBotModalProps) {
    const [newName, setNewName] = useState("");
    const [nameError, setNameError] = useState("");
    const [generalError, setGeneralError] = useState("");
    const { mutate, isPending, error } = useDuplicateBot();

    // Reset form when modal opens/closes
    useEffect(() => {
        if (isOpen && bot) {
            setNewName(`${bot.name} (Copy)`);
            setNameError("");
            setGeneralError("");
        } else {
            setNewName("");
            setNameError("");
            setGeneralError("");
        }
    }, [isOpen, bot]);

    const validateName = (value: string) => {
        if (value.length < 2) {
            setNameError("Name must be at least 2 characters");
        } else if (value.length > 50) {
            setNameError("Name must be at most 50 characters");
        } else {
            setNameError("");
        }
    };

    const isFormValid =
        newName.length >= 2 && newName.length <= 50 && !nameError;

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setGeneralError("");

        if (!isFormValid || !bot) {
            setGeneralError("Please fix the errors above");
            return;
        }

        try {
            const duplicatedBot = await mutate({
                botId: bot.id,
                name: newName,
            });

            onSuccess(duplicatedBot);
            setNewName("");
            onClose();

            // Show success toast (would integrate with toast library)
            console.log(`Bot duplicated: ${duplicatedBot.name}`);
        } catch (err) {
            const errorMessage =
                err instanceof Error ? err.message : "Failed to duplicate bot";
            setGeneralError(errorMessage);
            onError?.(errorMessage);
        }
    };

    if (!bot) return null;

    return (
        <Dialog open={isOpen} onOpenChange={onClose}>
            <div className="sm:max-w-md w-full">
                <DialogHeader>
                    <DialogTitle>
                        <div className="flex items-center gap-2">
                            <Copy size={20} />
                            Duplicate Bot
                        </div>
                    </DialogTitle>
                    <DialogDescription>
                        Create a copy of "{bot.name}". The new bot will inherit
                        the description and confidence threshold, but will start
                        empty (no documents).
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

                    {/* Original Bot Name (Read-only) */}
                    <div>
                        <label
                            htmlFor="original-name"
                            className="block text-sm font-medium text-gray-700"
                        >
                            Original Bot
                        </label>
                        <input
                            id="original-name"
                            type="text"
                            value={bot.name}
                            readOnly
                            className="mt-1 w-full px-3 py-2 border border-gray-300 rounded-md bg-gray-50 text-gray-600 text-sm"
                        />
                    </div>

                    {/* New Bot Name */}
                    <div>
                        <label
                            htmlFor="new-name"
                            className="block text-sm font-medium text-gray-700"
                        >
                            New Bot Name *
                        </label>
                        <input
                            id="new-name"
                            type="text"
                            value={newName}
                            onChange={(e) => {
                                setNewName(e.target.value);
                                validateName(e.target.value);
                            }}
                            placeholder="e.g., HR Bot (Copy)"
                            className={`mt-1 w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                                nameError ? "border-red-500" : "border-gray-300"
                            }`}
                            disabled={isPending}
                            autoFocus
                        />
                        {nameError && (
                            <p className="mt-1 text-sm text-red-600">
                                {nameError}
                            </p>
                        )}
                        <p className="mt-1 text-xs text-gray-500">
                            2-50 characters, must be unique in your organization
                        </p>
                    </div>

                    {/* Info Box */}
                    <div className="p-3 bg-blue-50 border border-blue-200 rounded text-sm text-blue-700">
                        <p className="font-medium mb-1">The new bot will:</p>
                        <ul className="list-disc list-inside space-y-1 text-xs">
                            <li>
                                Inherit the description and confidence threshold
                            </li>
                            <li>Start with status "Empty" (no documents)</li>
                            <li>Have its own separate chat history</li>
                        </ul>
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
                            className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:bg-blue-400 flex items-center gap-2"
                            disabled={!isFormValid || isPending}
                        >
                            {isPending && (
                                <Loader size={16} className="animate-spin" />
                            )}
                            {isPending ? "Duplicating..." : "Duplicate Bot"}
                        </button>
                    </div>
                </form>
            </div>
        </Dialog>
    );
}
