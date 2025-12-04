"use client";

import React, { useState, useEffect } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Bot } from "@/types/bot";
import { useBotQuery, useUpdateBot } from "@/hooks/useBotsQuery";
import { AlertCircle, Loader, Copy, Check } from "lucide-react";
import { format } from "date-fns";

interface BotSettingsModalProps {
  botId: string;
  isOpen: boolean;
  onClose: () => void;
  onSave?: (bot: Bot) => void;
  onError?: (error: string) => void;
}

export function BotSettingsModal({
  botId,
  isOpen,
  onClose,
  onSave,
  onError,
}: BotSettingsModalProps) {
  const { data: bot, isLoading: isLoadingBot } = useBotQuery(botId);
  const { mutate: updateBot, isPending: isUpdating, error: updateError } = useUpdateBot(botId);

  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [threshold, setThreshold] = useState(80);
  const [nameError, setNameError] = useState("");
  const [descriptionError, setDescriptionError] = useState("");
  const [generalError, setGeneralError] = useState("");
  const [copied, setCopied] = useState(false);
  const [isDirty, setIsDirty] = useState(false);

  // Initialize form with bot data
  useEffect(() => {
    if (bot) {
      setName(bot.name);
      setDescription(bot.description || "");
      setThreshold(bot.confidence_threshold);
      setIsDirty(false);
    }
  }, [bot]);

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

  const isFormValid = name.length >= 2 && name.length <= 50 && !nameError && !descriptionError;

  const handleNameChange = (value: string) => {
    setName(value);
    validateName(value);
    setIsDirty(true);
  };

  const handleDescriptionChange = (value: string) => {
    setDescription(value);
    validateDescription(value);
    setIsDirty(true);
  };

  const handleThresholdChange = (value: number) => {
    setThreshold(value);
    setIsDirty(true);
  };

  const copyBotId = () => {
    if (bot) {
      navigator.clipboard.writeText(bot.id);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setGeneralError("");

    if (!isFormValid) {
      setGeneralError("Please fix the errors above");
      return;
    }

    if (!bot) return;

    // Build update payload with only changed fields
    const updates: Record<string, any> = {};
    if (name !== bot.name) updates.name = name;
    if (description !== bot.description) updates.description = description || undefined;
    if (threshold !== bot.confidence_threshold) updates.confidence_threshold = threshold;

    if (Object.keys(updates).length === 0) {
      onClose();
      return;
    }

    try {
      const updatedBot = await updateBot(updates);
      onSave?.(updatedBot);
      setIsDirty(false);
      onClose();
      console.log(`Bot updated: ${updatedBot.name}`);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Failed to update bot";
      setGeneralError(errorMessage);
      onError?.(errorMessage);
    }
  };

  if (!isOpen) return null;

  if (isLoadingBot) {
    return (
      <Dialog open={isOpen} onOpenChange={onClose}>
        <DialogContent className="sm:max-w-md flex items-center justify-center">
          <Loader className="animate-spin" />
        </DialogContent>
      </Dialog>
    );
  }

  if (!bot) {
    return (
      <Dialog open={isOpen} onOpenChange={onClose}>
        <DialogContent className="sm:max-w-md">
          <div className="p-4 text-red-600">Bot not found</div>
        </DialogContent>
      </Dialog>
    );
  }

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-md max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Bot Settings</DialogTitle>
        </DialogHeader>

        <form onSubmit={handleSave} className="space-y-4">
          {/* General Error */}
          {generalError && (
            <div className="flex items-center gap-2 p-3 bg-red-50 border border-red-200 rounded text-red-700 text-sm">
              <AlertCircle size={16} />
              <span>{generalError}</span>
            </div>
          )}

          {/* Bot Name */}
          <div>
            <label htmlFor="edit-name" className="block text-sm font-medium text-gray-700">
              Bot Name *
            </label>
            <input
              id="edit-name"
              type="text"
              value={name}
              onChange={(e) => handleNameChange(e.target.value)}
              className={`mt-1 w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                nameError ? "border-red-500" : "border-gray-300"
              }`}
              disabled={isUpdating}
            />
            {nameError && (
              <p className="mt-1 text-sm text-red-600">{nameError}</p>
            )}
          </div>

          {/* Description */}
          <div>
            <label htmlFor="edit-description" className="block text-sm font-medium text-gray-700">
              Description
            </label>
            <textarea
              id="edit-description"
              value={description}
              onChange={(e) => handleDescriptionChange(e.target.value)}
              className={`mt-1 w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                descriptionError ? "border-red-500" : "border-gray-300"
              }`}
              rows={3}
              disabled={isUpdating}
            />
            <div className="mt-1 flex justify-between">
              {descriptionError && (
                <p className="text-sm text-red-600">{descriptionError}</p>
              )}
              <p className="text-xs text-gray-500 ml-auto">
                {description.length}/500
              </p>
            </div>
          </div>

          {/* Confidence Threshold */}
          <div>
            <label htmlFor="edit-threshold" className="block text-sm font-medium text-gray-700">
              Confidence Threshold: {threshold}%
            </label>
            <input
              id="edit-threshold"
              type="range"
              min="0"
              max="100"
              value={threshold}
              onChange={(e) => handleThresholdChange(parseInt(e.target.value))}
              className="mt-2 w-full"
              disabled={isUpdating}
            />
          </div>

          {/* Read-only Fields */}
          <div className="pt-4 border-t space-y-3">
            <div>
              <label className="text-sm font-medium text-gray-700">Bot ID</label>
              <div className="mt-1 flex items-center gap-2 p-2 bg-gray-50 border rounded">
                <code className="text-xs text-gray-600 flex-1 break-all">{bot.id}</code>
                <button
                  type="button"
                  onClick={copyBotId}
                  className="p-1 hover:bg-gray-200 rounded"
                  title="Copy bot ID"
                >
                  {copied ? (
                    <Check size={16} className="text-green-600" />
                  ) : (
                    <Copy size={16} className="text-gray-600" />
                  )}
                </button>
              </div>
            </div>

            <div>
              <label className="text-sm font-medium text-gray-700">Created</label>
              <p className="mt-1 text-sm text-gray-600">
                {format(new Date(bot.created_at), "PPpp")}
              </p>
            </div>

            <div>
              <label className="text-sm font-medium text-gray-700">Last Updated</label>
              <p className="mt-1 text-sm text-gray-600">
                {format(new Date(bot.updated_at), "PPpp")}
              </p>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex justify-end gap-2 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50 disabled:opacity-50"
              disabled={isUpdating}
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={!isFormValid || !isDirty || isUpdating}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            >
              {isUpdating && <Loader size={16} className="animate-spin" />}
              Save Changes
            </button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}
