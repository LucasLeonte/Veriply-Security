"use client";

import { useState, useRef, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { useToast } from "@/components/ui/toast";
import { Upload, FileText } from "lucide-react";
import { getAccessToken } from "@/lib/auth";
import { botsApi } from "@/lib/api/bots";
import type { Bot } from "@/types/bot";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

interface QAImportDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  groupId: string;
  onSuccess: (summary: any) => void;
}

export default function QAImportDialog({
  open,
  onOpenChange,
  groupId,
  onSuccess,
}: QAImportDialogProps) {
  const { toast } = useToast();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [loading, setLoading] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [bots, setBots] = useState<Bot[]>([]);
  const [botsLoading, setBotsLoading] = useState(false);
  const [selectedBotId, setSelectedBotId] = useState("");

  // Fetch bots for the group
  useEffect(() => {
    if (open && groupId) {
      setBotsLoading(true);
      botsApi
        .listBots(groupId)
        .then((response) => {
          setBots(response.bots || []);
          // Auto-select first bot if available
          if (response.bots && response.bots.length > 0 && !selectedBotId) {
            setSelectedBotId(response.bots[0].id);
          }
        })
        .catch((err) => {
          
          toast({
            title: "Error",
            description: "Failed to load bots. Please try again.",
            variant: "error",
          });
        })
        .finally(() => setBotsLoading(false));
    }
  }, [open, groupId]);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // Validate file
    if (!file.name.endsWith(".csv")) {
      toast({
        title: "Invalid file",
        description: "Please select a CSV file",
        variant: "error",
      });
      return;
    }

    if (file.size > 5 * 1024 * 1024) {
      toast({
        title: "File too large",
        description: "File size must be less than 5MB",
        variant: "error",
      });
      return;
    }

    setSelectedFile(file);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!selectedBotId) {
      toast({
        title: "No bot selected",
        description: "Please select a bot for the Q&A entries",
        variant: "error",
      });
      return;
    }

    if (!selectedFile) {
      toast({
        title: "No file selected",
        description: "Please select a CSV file",
        variant: "error",
      });
      return;
    }

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

      const formData = new FormData();
      formData.append("file", selectedFile);

      const url = `${API_BASE_URL}/api/v1/verified-qa/bulk-import?bot_id=${selectedBotId}`;

      const response = await fetch(url, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
        },
        body: formData,
      });

      const result = await response.json();

      if (!response.ok) {
        throw new Error(result.detail || `API Error: ${response.status}`);
      }

      toast({
        title: "Import complete",
        description: `Imported ${result.imported_count} entries. ${result.skipped_count} skipped.`,
        variant: "success",
      });

      setSelectedFile(null);
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }

      onOpenChange(false);
      onSuccess(result);
    } catch (error: any) {
      const message =
        error.message ||
        "Failed to import CSV. Please check the file format and try again.";
      
      toast({
        title: "Import failed",
        description: message,
        variant: "error",
      });
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    if (!loading) {
      setSelectedFile(null);
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
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
        className="bg-white rounded-lg shadow-lg p-6 w-full max-w-xl"
        onClick={(e) => e.stopPropagation()}
      >
        <h2 className="text-xl font-bold text-slate-900 mb-1">
          Import Q&A from CSV
        </h2>
        <p className="text-sm text-slate-600 mb-4">
          CSV must have "question" and "answer" columns
        </p>

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Bot Selector */}
          <div>
            <label className="block text-sm font-medium text-slate-900 mb-2">
              Target Bot <span className="text-red-500">*</span>
            </label>
            {botsLoading ? (
              <div className="text-sm text-slate-500">Loading bots...</div>
            ) : bots.length === 0 ? (
              <div className="text-sm text-amber-600 bg-amber-50 p-3 rounded-md">
                No bots found. Please create a bot first to import Q&A entries.
              </div>
            ) : (
              <select
                value={selectedBotId}
                onChange={(e) => setSelectedBotId(e.target.value)}
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
          </div>

          {/* File Input */}
          <div
            className="border-2 border-dashed border-slate-300 rounded-lg p-8 text-center cursor-pointer hover:border-emerald-500 hover:bg-emerald-50 transition"
            onClick={() => fileInputRef.current?.click()}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept=".csv"
              onChange={handleFileSelect}
              className="hidden"
              disabled={loading}
            />

            {selectedFile ? (
              <div>
                <FileText className="w-8 h-8 mx-auto text-emerald-600 mb-2" />
                <p className="text-sm font-medium text-emerald-600">
                  {selectedFile.name}
                </p>
                <p className="text-xs text-slate-500 mt-1">
                  {(selectedFile.size / 1024).toFixed(1)} KB
                </p>
              </div>
            ) : (
              <div>
                <Upload className="w-8 h-8 mx-auto text-slate-400 mb-2" />
                <p className="text-sm font-medium text-slate-900">
                  Click to select CSV file
                </p>
                <p className="text-xs text-slate-600 mt-1">
                  or drag and drop (max 5MB)
                </p>
              </div>
            )}
          </div>

          {/* Format Guide */}
          <div className="bg-emerald-50 border border-emerald-200 p-4 rounded-lg">
            <p className="text-sm font-medium text-emerald-900 mb-2">
              CSV Format Example:
            </p>
            <pre className="text-xs text-emerald-800 overflow-x-auto bg-white p-2 rounded border border-emerald-100">
              {`question,answer
"What is your return policy?","We offer 30-day returns on all items."
"How do I track my order?","Use the tracking link in your confirmation email."`}
            </pre>
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
              disabled={loading || !selectedFile || !selectedBotId || bots.length === 0}
            >
              {loading ? "Importing..." : "Import"}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}
