"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { useToast } from "@/components/ui/toast";
import { getAccessToken } from "@/lib/auth";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

interface AddEntryDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  botId: string;
  onSuccess: () => void;
}

export default function AddEntryDialog({
  open,
  onOpenChange,
  botId,
  onSuccess,
}: AddEntryDialogProps) {
  const { toast } = useToast();
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    question_text: "",
    answer_text: "",
  });
  const [errors, setErrors] = useState<Record<string, string>>({});

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

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
        bot_id: botId,
        source_citations: null,
      };
      
      console.log("Creating entry with URL:", url);
      console.log("Payload:", payload);
      
      const response = await fetch(url, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(payload),
      });

      console.log("Response status:", response.status);
      const responseData = await response.json();
      console.log("Response data:", responseData);

      if (!response.ok) {
        throw new Error(responseData.detail || `API Error: ${response.status}`);
      }

      setFormData({
        question_text: "",
        answer_text: "",
      });
      setErrors({});
      onOpenChange(false);
      onSuccess();
    } catch (error: any) {
      const message = error.message || "Failed to create Q&A entry. Please try again.";
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

  if (!open) return null;

  return (
    <div
      className="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
      onClick={() => !loading && onOpenChange(false)}
    >
      <div
        className="bg-white rounded-lg shadow-lg p-6 w-full max-w-xl"
        onClick={(e) => e.stopPropagation()}
      >
        <h2 className="text-xl font-bold text-slate-900 mb-1">Add New Q&A Entry</h2>
        <p className="text-sm text-slate-600 mb-4">Create a new verified Q&A pair for your knowledge base</p>

        <form onSubmit={handleSubmit} className="space-y-4">
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
                <span className="text-sm text-red-600">{errors.question_text}</span>
              )}
              <span className="text-xs text-slate-500 ml-auto">{formData.question_text.length}/2000</span>
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
                <span className="text-sm text-red-600">{errors.answer_text}</span>
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
              onClick={() => onOpenChange(false)}
              disabled={loading}
            >
              Cancel
            </Button>
            <Button type="submit" className="bg-emerald-600 text-white hover:bg-emerald-700" disabled={loading}>
              {loading ? "Adding..." : "Add Entry"}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}
