"use client";

import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Citation } from "@/types/chat";

interface CitationViewerProps {
    citation: Citation | null;
    open: boolean;
    onOpenChange: (open: boolean) => void;
    answerText?: string; // Assistant message text used for relevance highlighting
}

function renderHighlighted(text: string, answerText?: string) {
    if (!answerText) return <div className="text-sm leading-relaxed text-slate-800 whitespace-pre-wrap">{text}</div>;

    const stopwords = new Set([
        "the","a","an","and","or","but","in","on","at","to","for",
        "of","with","by","from","as","is","are","was","were","be",
        "have","has","do","does","did","can","could","will","would",
        "should","may","might","must","shall","that","this","these",
        "those","you","me","he","she","it","we","they","what","which",
        "who","when","where","why","how","all","each","every","both",
        "i","your","our","their","my","his","her","its","not","no",
        "yes","more","less","very","so","too","just","only","also",
    ]);

    const keywords = Array.from(
        new Set(
            (answerText.match(/\b\w{5,}\b/g) || [])
                .map((w) => w.toLowerCase())
                .filter((w) => !stopwords.has(w))
                .slice(0, 8)
        )
    );

    if (keywords.length === 0) {
        return <div className="text-sm leading-relaxed text-slate-800 whitespace-pre-wrap">{text}</div>;
    }

    const sentences = text.split(/(?<=[.!?])\s+/);
    const scored = sentences.map((s, i) => ({
        s,
        i,
        score: keywords.filter((kw) => s.toLowerCase().includes(kw)).length,
    }));
    const topIdx = new Set(
        scored.filter((x) => x.score > 0).sort((a, b) => b.score - a.score).slice(0, 3).map((x) => x.i)
    );
    const escaped = keywords.map((w) => w.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"));
    const regex = new RegExp(`(${escaped.join("|")})`, "gi");

    return (
        <div className="text-sm leading-relaxed text-slate-800 whitespace-pre-wrap">
            {sentences.map((s, i) => {
                if (!topIdx.has(i)) return <span key={i}>{s} </span>;
                const parts = s.split(regex);
                return (
                    <span key={i}>
                        {parts.map((p, j) =>
                            keywords.includes(p.toLowerCase()) ? (
                                <mark key={j} className="bg-amber-100 text-slate-900 px-0.5 rounded">
                                    {p}
                                </mark>
                            ) : (
                                <span key={j}>{p}</span>
                            )
                        )}{" "}
                    </span>
                );
            })}
        </div>
    );
}

export function CitationViewer({ citation, open, onOpenChange, answerText }: CitationViewerProps) {
    if (!citation) return null;

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="max-w-2xl max-h-[80vh] flex flex-col">
                <DialogHeader>
                    <DialogTitle className="text-lg font-semibold text-slate-900">
                        {citation.document_name || citation.source}
                    </DialogTitle>
                    <DialogDescription className="flex gap-3 text-xs text-slate-600 mt-2">
                        {citation.page_number !== undefined && (
                            <span>📄 Page {citation.page_number}</span>
                        )}
                        {citation.section && (
                            <span>📍 {citation.section}</span>
                        )}
                        {citation.similarity !== undefined && (
                            <span className="text-sky-700 font-semibold">
                                ✓ {Math.round(citation.similarity * 100)}% relevance
                            </span>
                        )}
                    </DialogDescription>
                </DialogHeader>

                <div className="flex-1 min-h-0 mt-4">
                    <p className="text-xs font-medium text-slate-500 mb-2 uppercase tracking-wider">
                        Relevant Context
                    </p>
                    <ScrollArea className="h-[300px] w-full rounded-md border border-slate-200 bg-slate-50 p-4">
                        {renderHighlighted(citation.text || "No text content available.", answerText)}
                    </ScrollArea>
                </div>

                {citation.url && (
                    <div className="mt-4 text-center">
                        <a
                            href={citation.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-xs text-sky-700 hover:text-sky-800 font-medium underline"
                        >
                            View full document →
                        </a>
                    </div>
                )}
            </DialogContent>
        </Dialog>
    );
}
