"use client";

import React, { useState } from "react";
import {
    Dialog,
    DialogContent,
    DialogHeader,
    DialogTitle,
    DialogDescription,
} from "@/components/ui/dialog";
import { Bot } from "@/types/bot";
import { useCreateBot } from "@/hooks/useBotsQuery";
import { useGroup } from "@/contexts/GroupContext";
import { AlertCircle, Loader } from "lucide-react";

interface CreateBotModalProps {
    isOpen: boolean;
    onClose: () => void;
    onSuccess: (bot: Bot) => void;
    onError?: (error: string) => void;
}

export function CreateBotModal({
    isOpen,
    onClose,
    onSuccess,
    onError,
}: CreateBotModalProps) {
    const { currentGroup } = useGroup();
    const [name, setName] = useState("");
    const [description, setDescription] = useState("");
    const [threshold, setThreshold] = useState(80);
    const [nameError, setNameError] = useState("");
    const [descriptionError, setDescriptionError] = useState("");
    const [generalError, setGeneralError] = useState("");
    const { mutate, isPending } = useCreateBot();

    // Real-time name validation
    const validateName = (value: string) => {
        if (value.length < 2) {
            setNameError("Name must be at least 2 characters");
        } else if (value.length > 50) {
            setNameError("Name must be at most 50 characters");
        } else {
            setNameError("");
        }
    };

    // Real-time description validation
    const validateDescription = (value: string) => {
        if (value.length > 500) {
            setDescriptionError("Description must be at most 500 characters");
        } else {
            setDescriptionError("");
        }
    };

    const isFormValid =
        name.length >= 2 &&
        name.length <= 50 &&
        !nameError &&
        !descriptionError;

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setGeneralError("");

        if (!isFormValid) {
            setGeneralError("Please fix the errors above");
            return;
        }

        try {
            const bot = await mutate({
                group_id: currentGroup.id,
                name,
                description: description || undefined,
                confidence_threshold: threshold,
            });

            onSuccess(bot);
            setName("");
            setDescription("");
            setThreshold(80);
            onClose();

            // Show success toast (would integrate with toast library)
            console.log(`Bot created: ${bot.name}`);
        } catch (err) {
            const errorMessage =
                err instanceof Error ? err.message : "Failed to create bot";
            setGeneralError(errorMessage);
            onError?.(errorMessage);
        }
    };

    return (
        <Dialog open={isOpen} onOpenChange={onClose}>
            <DialogContent className="sm:max-w-md">
                <DialogHeader>
                    <DialogTitle>Create New Bot</DialogTitle>
                    <DialogDescription>
                        Set up a new bot with custom settings for your
                        organization.
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

                    {/* Bot Name */}
                    <div>
                        <label
                            htmlFor="name"
                            className="block text-sm font-medium text-gray-700"
                        >
                            Bot Name *
                        </label>
                        <input
                            id="name"
                            type="text"
                            value={name}
                            onChange={(e) => {
                                setName(e.target.value);
                                validateName(e.target.value);
                            }}
                            placeholder="e.g., HR Bot, Sales Bot"
                            className={`mt-1 w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${nameError ? "border-red-500" : "border-gray-300"
                                }`}
                            disabled={isPending}
                        />
                        {nameError && (
                            <p className="mt-1 text-sm text-red-600">
                                {nameError}
                            </p>
                        )}
                        <p className="mt-1 text-xs text-gray-500">
                            2-50 characters, unique in your organization
                        </p>
                    </div>

                    {/* Description */}
                    <div>
                        <label
                            htmlFor="description"
                            className="block text-sm font-medium text-gray-700"
                        >
                            Description (Optional)
                        </label>
                        <textarea
                            id="description"
                            value={description}
                            onChange={(e) => {
                                setDescription(e.target.value);
                                validateDescription(e.target.value);
                            }}
                            placeholder="Describe what this bot does..."
                            className={`mt-1 w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${descriptionError
                                    ? "border-red-500"
                                    : "border-gray-300"
                                }`}
                            rows={3}
                            disabled={isPending}
                        />
                        <div className="mt-1 flex justify-between">
                            {descriptionError && (
                                <p className="text-sm text-red-600">
                                    {descriptionError}
                                </p>
                            )}
                            <p className="text-xs text-gray-500 ml-auto">
                                {description.length}/500
                            </p>
                        </div>
                    </div>

                    {/* Confidence Threshold */}
                    <div>
                        <label
                            htmlFor="threshold"
                            className="block text-sm font-medium text-gray-700"
                        >
                            Confidence Threshold: {threshold}%
                        </label>
                        <input
                            id="threshold"
                            type="range"
                            min="0"
                            max="100"
                            value={threshold}
                            onChange={(e) =>
                                setThreshold(parseInt(e.target.value))
                            }
                            className="mt-2 w-full"
                            disabled={isPending}
                        />
                        <p className="mt-1 text-xs text-gray-500">
                            Responses below this threshold will be reviewed by
                            your team
                        </p>
                    </div>

                    {/* Action Buttons */}
                    <div className="flex justify-end gap-2 pt-4">
                        <button
                            type="button"
                            onClick={onClose}
                            className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50 disabled:opacity-50"
                            disabled={isPending}
                        >
                            Cancel
                        </button>
                        <button
                            type="submit"
                            disabled={!isFormValid || isPending}
                            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                        >
                            {isPending && (
                                <Loader size={16} className="animate-spin" />
                            )}
                            Create Bot
                        </button>
                    </div>
                </form>
            </DialogContent>
        </Dialog>
    );
}
