"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { Citation } from "@/types/citations";
import { SourceViewerPanel } from "./SourceViewerPanel";
import { cn } from "@/lib/utils";

interface AnnotatedAnswerProps {
  answerHtml: string;
  citations: Citation[];
}

export function AnnotatedAnswer({ answerHtml, citations }: AnnotatedAnswerProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [activeCitation, setActiveCitation] = useState<Citation | null>(null);

  const citationMap = useMemo(() => {
    const map: Record<string, Citation> = {};
    citations.forEach((c) => {
      map[c.id] = c;
    });
    return map;
  }, [citations]);

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;

    // Decorate inline citation nodes with styles and tooltip
    citations.forEach((citation) => {
      const nodes = el.querySelectorAll<HTMLElement>(
        `[data-citation-id="${citation.id}"]`
      );
      nodes.forEach((node) => {
        // Build tooltip with document name, section, page
        const tooltipParts = [citation.document_name];
        if (citation.section) {
          tooltipParts.push(`— ${citation.section}`);
        }
        if (citation.page_number) {
          tooltipParts.push(`(p. ${citation.page_number})`);
        }

        node.setAttribute(
          "title",
          `${tooltipParts.join(" ")} • ${Math.round(citation.similarity_score * 100)}%`
        );

        // Add visual styles
        node.classList.add(
          "text-blue-600",
          "underline",
          "decoration-2",
          "cursor-pointer",
          "font-medium"
        );
      });
    });
  }, [answerHtml, citations]);

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;

    // Click handler for citations
    const handler = (event: Event) => {
      const target = event.target as HTMLElement;
      const citationNode = target.closest<HTMLElement>("[data-citation-id]");
      if (!citationNode) return;

      const id = citationNode.dataset.citationId;
      if (id && citationMap[id]) {
        setActiveCitation(citationMap[id]);
      }
    };

    el.addEventListener("click", handler);
    return () => el.removeEventListener("click", handler);
  }, [citationMap]);

  const sortedCitations = useMemo(() => {
    return [...citations].sort((a, b) => {
      const aNum = parseInt(a.id.replace(/\D/g, "")) || 0;
      const bNum = parseInt(b.id.replace(/\D/g, "")) || 0;
      return aNum - bNum;
    });
  }, [citations]);

  return (
    <div className="space-y-6">
      {/* Answer with embedded citations */}
      <div
        ref={containerRef}
        className={cn(
          "prose prose-slate max-w-none rounded-lg border border-slate-200 bg-white p-4 shadow-sm",
          "leading-relaxed"
        )}
        dangerouslySetInnerHTML={{ __html: answerHtml }}
      />

      {/* Citations list */}
      {sortedCitations.length > 0 && (
        <div className="space-y-3 rounded-lg border border-slate-200 bg-slate-50 p-4">
          <div className="text-sm font-semibold text-slate-800">
            Citations
          </div>
          <div className="space-y-2 text-sm text-slate-700">
            {sortedCitations.map((citation, idx) => (
              <div
                key={citation.id}
                className="flex flex-col gap-1 rounded-md bg-white/70 p-3 shadow-sm"
              >
                <div className="flex items-center gap-2 text-blue-700 font-semibold">
                  <span>[{idx + 1}]</span>
                  <button
                    className="underline decoration-2 hover:text-blue-800 transition-colors"
                    onClick={() => setActiveCitation(citation)}
                  >
                    {citation.document_name}
                  </button>
                </div>
                <div className="text-slate-800 font-medium">
                  {citation.section || ""}
                  {citation.section && citation.page_number ? " — " : ""}
                  {citation.page_number ? `Page ${citation.page_number}` : ""}
                </div>
                <div className="text-slate-600">{citation.text_snippet}</div>
                <div className="text-xs text-slate-500">
                  Similarity {Math.round(citation.similarity_score * 100)}% · Confidence {citation.confidence}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Source viewer modal/panel */}
      <SourceViewerPanel
        citation={activeCitation}
        open={Boolean(activeCitation)}
        onOpenChange={(open) => {
          if (!open) setActiveCitation(null);
        }}
      />
    </div>
  );
}
