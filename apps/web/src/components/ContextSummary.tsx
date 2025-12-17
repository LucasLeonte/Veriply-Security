"use client";

import { useMemo, useState } from "react";
import { ChevronDown, ChevronUp } from "lucide-react";
import { ChatMessage } from "@/types/chat";
import { Button } from "./ui/button";
import { Card } from "./ui/card";

interface ContextSummaryProps {
    messages: ChatMessage[];
    contextWindow: number;
}

function buildSummary(messages: ChatMessage[], contextWindow: number): string {
    const olderMessages = messages.slice(0, Math.max(0, messages.length - contextWindow));
    if (olderMessages.length === 0) return "";

    const trimmed = olderMessages.slice(-6); // keep recent portion of older history
    const snippets = trimmed.map((msg) => {
        const prefix = msg.role === "assistant" ? "Assistant" : "User";
        const normalized = msg.content.replace(/\s+/g, " ").trim();
        const preview = normalized.length > 120 ? `${normalized.slice(0, 117)}...` : normalized;
        const citationHint = msg.citations && msg.citations.length > 0
            ? ` (sources: ${msg.citations.slice(0, 2).map((c) => c.source).join(", ")})`
            : "";
        return `${prefix}: ${preview}${citationHint}`;
    });

    return `Previous messages: ${snippets.join(" | ")}`;
}

export default function ContextSummary({ messages, contextWindow }: ContextSummaryProps) {
    const [open, setOpen] = useState(false);
    const summaryText = useMemo(
        () => buildSummary(messages, contextWindow),
        [messages, contextWindow]
    );

    if (!summaryText) return null;

    const summarizedCount = Math.max(0, messages.length - contextWindow);

    return (
        <Card className="mb-3 border-slate-200 bg-slate-50">
            <div className="flex items-center justify-between p-3">
                <div className="text-xs text-slate-600">
                    Context: keeping {Math.min(messages.length, contextWindow)} messages; {summarizedCount} summarized
                </div>
                <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => setOpen((prev) => !prev)}
                    className="h-7 px-2 text-xs"
                >
                    {open ? (
                        <>
                            Hide context <ChevronUp className="h-3 w-3 ml-1" />
                        </>
                    ) : (
                        <>
                            View context <ChevronDown className="h-3 w-3 ml-1" />
                        </>
                    )}
                </Button>
            </div>
            {open && (
                <div className="px-3 pb-3 text-xs text-slate-700 leading-relaxed">
                    {summaryText}
                </div>
            )}
        </Card>
    );
}
