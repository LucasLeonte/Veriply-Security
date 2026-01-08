"use client";

import { useState, useEffect, useCallback } from "react";
import { Button } from "@/components/ui/button";
import { ChevronDown, ChevronRight, Plus, Upload, RefreshCw, Trash2, Edit2 } from "lucide-react";
import { getAccessToken } from "@/lib/auth";
import { useToast } from "@/components/ui/toast";
import QAEntryDialog from "./QAEntryDialog";
import QAImportDialog from "./QAImportDialog";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

interface VerifiedQA {
  id: string;
  question_text: string;
  answer_text: string;
  source_citations: Record<string, any> | null;
  bot_id: string;
  approved_by_user_id: string | null;
  approved_at: string;
  created_at: string;
  updated_at: string;
}

interface QASectionProps {
  groupId: string;
}

export default function QASection({ groupId }: QASectionProps) {
  const { toast } = useToast();
  const [entries, setEntries] = useState<VerifiedQA[]>([]);
  const [loading, setLoading] = useState(false);
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [skip, setSkip] = useState(0);
  const [isAddDialogOpen, setIsAddDialogOpen] = useState(false);
  const [isImportDialogOpen, setIsImportDialogOpen] = useState(false);
  const limit = 10;

  const fetchEntries = useCallback(async () => {
    if (!groupId) return;

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

      const url = `${API_BASE_URL}/api/v1/verified-qa?group_id=${groupId}&skip=${skip}&limit=${limit}`;
      const response = await fetch(url, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch Q&A entries: ${response.status}`);
      }

      const data = await response.json();
      setEntries(data);
    } catch (error: any) {
      console.error("Error fetching Q&A entries:", error);
      toast({
        title: "Error",
        description: "Failed to load Q&A entries",
        variant: "error",
      });
    } finally {
      setLoading(false);
    }
  }, [groupId, skip, limit, toast]);

  useEffect(() => {
    fetchEntries();
  }, [fetchEntries]);

  const handleAddSuccess = () => {
    fetchEntries();
    toast({
      title: "Success",
      description: "Q&A entry added successfully",
      variant: "success",
    });
  };

  const handleImportSuccess = (summary: any) => {
    fetchEntries();
    toast({
      title: "Import Complete",
      description: `Imported ${summary.imported_count} entries. ${summary.skipped_count} skipped.`,
      variant: "success",
    });
  };

  const handleDelete = async (entryId: string) => {
    setDeletingId(entryId);
    try {
      const token = getAccessToken();
      if (!token) {
        throw new Error("No authentication token found");
      }

      const response = await fetch(
        `${API_BASE_URL}/api/v1/verified-qa/${entryId}?group_id=${groupId}`,
        {
          method: "DELETE",
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      if (!response.ok) {
        throw new Error(`Failed to delete entry: ${response.status}`);
      }

      toast({
        title: "Success",
        description: "Q&A entry deleted successfully",
        variant: "success",
      });

      fetchEntries();
    } catch (error: any) {
      toast({
        title: "Error",
        description: error.message || "Failed to delete entry",
        variant: "error",
      });
    } finally {
      setDeletingId(null);
    }
  };

  return (
    <div className="bg-white border border-slate-200 rounded-lg">
      {/* Header */}
      <div className="p-4 border-b border-slate-200">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold text-slate-900">
              Q&A Entries
            </h3>
            <p className="text-sm text-slate-600 mt-0.5">
              Verified question & answer pairs
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Button
              onClick={() => fetchEntries()}
              className="text-slate-600 hover:bg-slate-100 p-2"
              title="Refresh"
              disabled={loading}
            >
              <RefreshCw size={18} className={loading ? "animate-spin" : ""} />
            </Button>
            <Button
              onClick={() => setIsImportDialogOpen(true)}
              className="flex items-center gap-2 px-3 py-2 text-sm text-slate-700 border border-slate-300 hover:bg-slate-50"
            >
              <Upload size={16} />
              Import CSV
            </Button>
            <Button
              onClick={() => setIsAddDialogOpen(true)}
              className="flex items-center gap-2 px-3 py-2 text-sm bg-emerald-600 text-white hover:bg-emerald-700"
            >
              <Plus size={16} />
              Add Entry
            </Button>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="p-4">
        {loading ? (
          <div className="text-center py-8">
            <p className="text-slate-600">Loading Q&A entries...</p>
          </div>
        ) : entries.length === 0 ? (
          <div className="bg-slate-50 rounded-lg p-8 text-center border border-slate-200">
            <p className="text-slate-600 text-sm">
              No Q&A entries yet. Add entries manually or import from CSV.
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {entries.map((entry) => (
              <div
                key={entry.id}
                className="bg-slate-50 rounded-lg border border-slate-200 hover:shadow-sm transition"
              >
                <button
                  onClick={() =>
                    setExpandedId(expandedId === entry.id ? null : entry.id)
                  }
                  className="w-full text-left p-4 hover:bg-slate-100 transition rounded-lg"
                >
                  <div className="flex items-start gap-3">
                    {expandedId === entry.id ? (
                      <ChevronDown className="w-5 h-5 text-slate-400 flex-shrink-0 mt-0.5" />
                    ) : (
                      <ChevronRight className="w-5 h-5 text-slate-400 flex-shrink-0 mt-0.5" />
                    )}
                    <div className="flex-1 min-w-0">
                      <h4 className="font-medium text-slate-900 break-words text-sm">
                        {entry.question_text}
                      </h4>
                      <p className="text-xs text-slate-500 mt-1">
                        Added {new Date(entry.created_at).toLocaleDateString()}
                      </p>
                    </div>
                  </div>
                </button>

                {/* Expanded Content */}
                {expandedId === entry.id && (
                  <div className="px-4 pb-4 border-t border-slate-200 space-y-3 bg-white rounded-b-lg">
                    <div>
                      <p className="text-xs font-medium text-slate-700 mb-2 mt-3">
                        Answer:
                      </p>
                      <p className="text-sm text-slate-700 whitespace-pre-wrap break-words">
                        {entry.answer_text}
                      </p>
                    </div>

                    {entry.source_citations && (
                      <div>
                        <p className="text-xs font-medium text-slate-700 mb-2">
                          Citations:
                        </p>
                        <pre className="text-xs bg-slate-50 p-2 rounded border border-slate-200 overflow-x-auto">
                          {JSON.stringify(entry.source_citations, null, 2)}
                        </pre>
                      </div>
                    )}

                    <div className="flex gap-4 text-xs text-slate-500 pt-2">
                      <span>
                        Created: {new Date(entry.created_at).toLocaleString()}
                      </span>
                      <span>
                        Updated: {new Date(entry.updated_at).toLocaleString()}
                      </span>
                    </div>

                    {/* Action Buttons */}
                    <div className="flex gap-2 pt-4 border-t border-slate-200 mt-4">
                      <Button
                        onClick={() => {
                          // TODO: Implement edit dialog
                          toast({
                            title: "Coming soon",
                            description: "Edit functionality will be available soon",
                            variant: "info",
                          });
                        }}
                        className="flex items-center gap-2 px-3 py-1.5 text-xs bg-blue-50 text-blue-700 hover:bg-blue-100 border border-blue-200"
                      >
                        <Edit2 size={14} />
                        Edit
                      </Button>
                      <Button
                        onClick={() => {
                          if (confirm("Are you sure you want to delete this Q&A entry?")) {
                            handleDelete(entry.id);
                          }
                        }}
                        disabled={deletingId === entry.id}
                        className="flex items-center gap-2 px-3 py-1.5 text-xs bg-red-50 text-red-700 hover:bg-red-100 border border-red-200 disabled:opacity-50"
                      >
                        <Trash2 size={14} />
                        {deletingId === entry.id ? "Deleting..." : "Delete"}
                      </Button>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}

        {/* Pagination */}
        {entries.length === limit && (
          <div className="flex gap-3 justify-center pt-6">
            <Button
              onClick={() => setSkip(Math.max(0, skip - limit))}
              disabled={skip === 0}
              className="border border-slate-300 text-slate-700 hover:bg-slate-50 disabled:opacity-50"
              size="sm"
            >
              ← Previous
            </Button>
            <Button
              onClick={() => setSkip(skip + limit)}
              className="border border-slate-300 text-slate-700 hover:bg-slate-50"
              size="sm"
            >
              Next →
            </Button>
          </div>
        )}
      </div>

      {/* Dialogs */}
      <QAEntryDialog
        open={isAddDialogOpen}
        onOpenChange={setIsAddDialogOpen}
        groupId={groupId}
        onSuccess={handleAddSuccess}
      />
      <QAImportDialog
        open={isImportDialogOpen}
        onOpenChange={setIsImportDialogOpen}
        groupId={groupId}
        onSuccess={handleImportSuccess}
      />
    </div>
  );
}
