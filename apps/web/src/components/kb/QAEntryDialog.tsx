"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { useToast } from "@/components/ui/toast";
import { getAccessToken } from "@/lib/auth";
import { botsApi } from "@/lib/api/bots";
import type { Bot } from "@/types/bot";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

interface QAEntryDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  groupId: string;
  onSuccess: () => void;
}

export default function QAEntryDialog({
  open,
  onOpenChange,
  groupId,
  onSuccess,
}: QAEntryDialogProps) {
  const { toast } = useToast();
  const [loading, setLoading] = useState(false);
  const [bots, setBots] = useState<Bot[]>([]);
  const [botsLoading, setBotsLoading] = useState(false);
  const [formData, setFormData] = useState({
    question_text: "",
    answer_text: "",
    bot_id: "",
  });
  const [errors, setErrors] = useState<Record<string, string>>({});

  // Fetch bots for the group
  useEffect(() => {
    if (open && groupId) {
      setBotsLoading(true);
      botsApi
        .listBots(groupId)
        .then((response) => {
          setBots(response.bots || []);
          // Auto-select first bot if available
          if (response.bots && response.bots.length > 0 && !formData.bot_id) {
            setFormData((prev) => ({ ...prev, bot_id: response.bots[0].id }));
          }
        })
        .catch((err) => {
          console.error("Failed to fetch bots:", err);
          toast({
            title: "Error",
            description: "Failed to load bots. Please try again.",
            variant: "error",
          });
        })
        .finally(() => setBotsLoading(false));
    }
  }, [open, groupId]);

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!formData.bot_id) {
      newErrors.bot_id = "Please select a bot";
    }

    if (!formData.question_text.trim()) {
      newErrors.question_text = "Question is required";
    } else if (formData.question_text.length > 2000) {
      newErrors.question_text = "Question cannot exceed 2000 characters";
    }

    if (!formData.answer_text.trim()) {
      newErrors.answer_text = "Answer is required";
    } else if (formData.answer_text.length > 8000) {
      newErrors.answer_text = "Answer cannot exceed 8000 characters";
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validateForm()) return;

    try {
      setLoading(true);
      const token = getAccessToken();

      if (!token) {
        toast({
          title: "Error",
          description: "No authentication token found. Please log in again.",
          variant: "error",
        });
        return;
      }

      const url = `${API_BASE_URL}/api/v1/verified-qa`;
      const payload = {
        question_text: formData.question_text.trim(),
        answer_text: formData.answer_text.trim(),
        bot_id: formData.bot_id,
        source_citations: null,
      };

      const response = await fetch(url, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(payload),
      });

      const responseData = await response.json();

      if (!response.ok) {
        throw new Error(responseData.detail || `API Error: ${response.status}`);
      }

      toast({
        title: "Success",
        description: "Q&A entry added successfully",
        variant: "success",
      });

      setFormData({
        question_text: "",
        answer_text: "",
        bot_id: bots.length > 0 ? bots[0].id : "",
      });
      setErrors({});
      onOpenChange(false);
      onSuccess();
    } catch (error: any) {
      const message =
        error.message || "Failed to create Q&A entry. Please try again.";
      console.error("Error creating entry:", message);
      toast({
        title: "Error",
        description: message,
        variant: "error",
      });
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    if (!loading) {
      setFormData({
        question_text: "",
        answer_text: "",
        bot_id: bots.length > 0 ? bots[0].id : "",
      });
      setErrors({});
      onOpenChange(false);
    }
  };

  if (!open) return null;

  return (
    <div
      className="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
      onClick={handleClose}
    >
      <div
        className="bg-white rounded-lg shadow-lg p-6 w-full max-w-xl max-h-[90vh] overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
        <h2 className="text-xl font-bold text-slate-900 mb-1">
          Add Q&A Entry
        </h2>
        <p className="text-sm text-slate-600 mb-4">
          Create a new verified Q&A pair for your knowledge base
        </p>

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Bot Selector */}
          <div>
            <label className="block text-sm font-medium text-slate-900 mb-2">
              Bot <span className="text-red-500">*</span>
            </label>
            {botsLoading ? (
              <div className="text-sm text-slate-500">Loading bots...</div>
            ) : bots.length === 0 ? (
              <div className="text-sm text-amber-600 bg-amber-50 p-3 rounded-md">
                No bots found. Please create a bot first to add Q&A entries.
              </div>
            ) : (
              <select
                value={formData.bot_id}
                onChange={(e) => {
                  setFormData({ ...formData, bot_id: e.target.value });
                  if (errors.bot_id) {
                    setErrors({ ...errors, bot_id: "" });
                  }
                }}
                className="w-full px-3 py-2 border border-slate-300 rounded-md focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent text-sm"
                disabled={loading}
              >
                <option value="">Select a bot...</option>
                {bots.map((bot) => (
                  <option key={bot.id} value={bot.id}>
                    {bot.name}
                  </option>
                ))}
              </select>
            )}
            {errors.bot_id && (
              <span className="text-sm text-red-600 mt-1 block">
                {errors.bot_id}
              </span>
            )}
          </div>

          {/* Question Field */}
          <div>
            <label className="block text-sm font-medium text-slate-900 mb-2">
              Question <span className="text-red-500">*</span>
            </label>
            <textarea
              value={formData.question_text}
              onChange={(e) => {
                setFormData({ ...formData, question_text: e.target.value });
                if (errors.question_text) {
                  setErrors({ ...errors, question_text: "" });
                }
              }}
              placeholder="Enter the question..."
              className="w-full px-3 py-2 border border-slate-300 rounded-md focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent text-sm"
              rows={3}
              disabled={loading}
            />
            <div className="flex justify-between mt-1">
              {errors.question_text && (
                <span className="text-sm text-red-600">
                  {errors.question_text}
                </span>
              )}
              <span className="text-xs text-slate-500 ml-auto">
                {formData.question_text.length}/2000
              </span>
            </div>
          </div>

          {/* Answer Field */}
          <div>
            <label className="block text-sm font-medium text-slate-900 mb-2">
              Answer <span className="text-red-500">*</span>
            </label>
            <textarea
              value={formData.answer_text}
              onChange={(e) => {
                setFormData({ ...formData, answer_text: e.target.value });
                if (errors.answer_text) {
                  setErrors({ ...errors, answer_text: "" });
                }
              }}
              placeholder="Enter the answer..."
              className="w-full px-3 py-2 border border-slate-300 rounded-md focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent text-sm"
              rows={6}
              disabled={loading}
            />
            <div className="flex justify-between mt-1">
              {errors.answer_text && (
                <span className="text-sm text-red-600">
                  {errors.answer_text}
                </span>
              )}
              <span className="text-xs text-slate-500 ml-auto">
                {formData.answer_text.length}/8000
              </span>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex gap-3 justify-end pt-4 border-t border-slate-200 mt-4">
            <Button
              type="button"
              className="text-slate-700 border border-slate-300 hover:bg-slate-50"
              onClick={handleClose}
              disabled={loading}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              className="bg-emerald-600 text-white hover:bg-emerald-700"
              disabled={loading || bots.length === 0}
            >
              {loading ? "Adding..." : "Add Entry"}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}
