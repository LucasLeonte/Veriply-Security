"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { ChevronDown, ChevronRight, Trash2, Edit2 } from "lucide-react";
import { useToast } from "@/components/ui/toast";
import { getAccessToken } from "@/lib/auth";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

interface VerifiedQA {
  id: string;
  question_text: string;
  answer_text: string;
  source_citations: Record<string, any> | null;
  approved_by_user_id: string | null;
  approved_at: string;
  created_at: string;
  updated_at: string;
}

interface VerifiedQAListProps {
  entries: VerifiedQA[];
  loading: boolean;
  skip: number;
  limit: number;
  onSkipChange: (skip: number) => void;
  groupId: string;
  onEntryDeleted?: () => void;
  onEntryUpdated?: () => void;
}

export default function VerifiedQAList({
  entries,
  loading,
  skip,
  limit,
  onSkipChange,
  groupId,
  onEntryDeleted,
  onEntryUpdated,
}: VerifiedQAListProps) {
  const { toast } = useToast();
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);

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

      onEntryDeleted?.();
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

  if (loading) {
    return (
      <div className="text-center py-12">
        <p className="text-slate-600">Loading verified Q&A entries...</p>
      </div>
    );
  }

  if (entries.length === 0) {
    return (
      <div className="bg-slate-50 rounded-lg p-12 text-center border border-slate-200">
        <p className="text-slate-600 text-sm">
          No verified Q&A entries yet. Start by adding an entry or importing from CSV.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Entries */}
      <div className="grid gap-3">
        {entries.map((entry) => (
          <div
            key={entry.id}
            className="bg-white rounded-lg border border-slate-200 hover:shadow-sm transition"
          >
            <button
              onClick={() =>
                setExpandedId(expandedId === entry.id ? null : entry.id)
              }
              className="w-full text-left p-4 hover:bg-slate-50 transition"
            >
              <div className="flex items-start gap-3">
                {expandedId === entry.id ? (
                  <ChevronDown className="w-5 h-5 text-slate-400 flex-shrink-0 mt-0.5" />
                ) : (
                  <ChevronRight className="w-5 h-5 text-slate-400 flex-shrink-0 mt-0.5" />
                )}
                <div className="flex-1 min-w-0">
                  <h3 className="font-medium text-slate-900 break-words text-sm">
                    {entry.question_text}
                  </h3>
                  <p className="text-xs text-slate-500 mt-1">
                    Added {new Date(entry.created_at).toLocaleDateString()}
                  </p>
                </div>
              </div>
            </button>

            {/* Expanded Content */}
            {expandedId === entry.id && (
              <div className="px-4 pb-4 border-t border-slate-200 space-y-3 bg-slate-50">
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
                    <pre className="text-xs bg-white p-2 rounded border border-slate-200 overflow-x-auto">
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

      {/* Pagination */}
      {entries.length === limit && (
        <div className="flex gap-3 justify-center pt-6">
          <Button
            onClick={() => onSkipChange(Math.max(0, skip - limit))}
            disabled={skip === 0}
            className="border border-slate-300 text-slate-700 hover:bg-slate-50 disabled:opacity-50"
            size="sm"
          >
            ← Previous
          </Button>
          <Button
            onClick={() => onSkipChange(skip + limit)}
            className="border border-slate-300 text-slate-700 hover:bg-slate-50"
            size="sm"
          >
            Next →
          </Button>
        </div>
      )}
    </div>
  );
}
