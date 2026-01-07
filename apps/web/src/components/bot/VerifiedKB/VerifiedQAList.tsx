"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { ChevronDown, ChevronRight } from "lucide-react";

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
}

export default function VerifiedQAList({
  entries,
  loading,
  skip,
  limit,
  onSkipChange,
}: VerifiedQAListProps) {
  const [expandedId, setExpandedId] = useState<string | null>(null);

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
