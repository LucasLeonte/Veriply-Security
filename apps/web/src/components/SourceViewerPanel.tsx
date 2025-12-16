"use client";

import { Citation } from "@/types/citations";
import { cn } from "@/lib/utils";
import { X } from "lucide-react";

interface SourceViewerPanelProps {
  citation: Citation | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function SourceViewerPanel({
  citation,
  open,
  onOpenChange,
}: SourceViewerPanelProps) {
  if (!open || !citation) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-hidden">
      {/* Overlay */}
      <div
        className="absolute inset-0 bg-black/50 transition-opacity"
        onClick={() => onOpenChange(false)}
      />

      {/* Slide-in panel from right */}
      <div
        className={cn(
          "absolute right-0 top-0 bottom-0 w-full max-w-md transform transition-transform",
          open ? "translate-x-0" : "translate-x-full"
        )}
      >
        <div className="flex flex-col h-full bg-white shadow-lg">
          {/* Header */}
          <div className="flex items-center justify-between border-b border-slate-200 px-6 py-4">
            <div className="flex-1">
              <h2 className="text-lg font-semibold text-slate-900">
                Source Context
              </h2>
              <p className="text-sm text-slate-500 mt-1">
                {citation.document_name}
              </p>
            </div>
            <button
              onClick={() => onOpenChange(false)}
              className="rounded-md p-1 hover:bg-slate-100 transition-colors"
              aria-label="Close panel"
            >
              <X className="w-5 h-5 text-slate-400" />
            </button>
          </div>

          {/* Content */}
          <div className="flex-1 overflow-y-auto px-6 py-4">
            {/* Document metadata */}
            <div className="space-y-4 mb-6">
              <div>
                <label className="text-xs font-semibold text-slate-600 uppercase">
                  Document
                </label>
                <p className="text-sm text-slate-900 mt-1">
                  {citation.document_name}
                </p>
              </div>

              {citation.section && (
                <div>
                  <label className="text-xs font-semibold text-slate-600 uppercase">
                    Section
                  </label>
                  <p className="text-sm text-slate-900 mt-1">
                    {citation.section}
                  </p>
                </div>
              )}

              {citation.page_number && (
                <div>
                  <label className="text-xs font-semibold text-slate-600 uppercase">
                    Page
                  </label>
                  <p className="text-sm text-slate-900 mt-1">
                    {citation.page_number}
                  </p>
                </div>
              )}

              <div>
                <label className="text-xs font-semibold text-slate-600 uppercase">
                  Relevance
                </label>
                <div className="flex items-center gap-2 mt-1">
                  <div className="flex-1 bg-slate-200 rounded-full h-2">
                    <div
                      className="bg-blue-600 h-2 rounded-full transition-all"
                      style={{
                        width: `${Math.round(citation.similarity_score * 100)}%`,
                      }}
                    />
                  </div>
                  <span className="text-sm font-medium text-slate-900">
                    {Math.round(citation.similarity_score * 100)}%
                  </span>
                </div>
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-600 uppercase">
                  Confidence
                </label>
                <span
                  className={cn(
                    "inline-block px-2 py-1 mt-1 text-xs font-medium rounded-md",
                    {
                      "bg-green-100 text-green-800":
                        citation.confidence === "high",
                      "bg-yellow-100 text-yellow-800":
                        citation.confidence === "medium",
                      "bg-orange-100 text-orange-800":
                        citation.confidence === "low",
                    }
                  )}
                >
                  {citation.confidence}
                </span>
              </div>
            </div>

            {/* Chunk content */}
            <div className="border-t border-slate-200 pt-4">
              <label className="text-xs font-semibold text-slate-600 uppercase">
                Full Chunk Text
              </label>
              <div className="mt-3 p-3 bg-slate-50 rounded-md border border-slate-200">
                <p className="text-sm text-slate-700 leading-relaxed">
                  {citation.text_snippet}
                </p>
              </div>
            </div>
          </div>

          {/* Footer */}
          <div className="border-t border-slate-200 bg-slate-50 px-6 py-4">
            <button
              onClick={() => onOpenChange(false)}
              className="w-full px-4 py-2 bg-slate-900 text-white text-sm font-medium rounded-lg hover:bg-slate-800 transition-colors"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
