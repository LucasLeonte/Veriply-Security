"use client";

import { useState } from "react";
import { ChevronDown, ChevronUp } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { ChatMessage } from "@/types/chat";

interface ContextSummaryProps {
    messages: ChatMessage[];
    contextWindowSize: number;
    isCollapsed?: boolean;
}

/**
 * Displays a summary of conversation context when the number of messages
 * exceeds the context window size.
 * 
 * Shows older messages in a summarized format (beyond context window).
 * Collapsible to save space.
 */
export default function ContextSummary({
    messages,
    contextWindowSize,
    isCollapsed: initialCollapsed = true,
}: ContextSummaryProps) {
    const [isCollapsed, setIsCollapsed] = useState(initialCollapsed);

    // Only show summary if we have more messages than context window
    if (messages.length <= contextWindowSize) {
        return null;
    }

    const olderMessages = messages.slice(0, -contextWindowSize);
    const summary = generateSummary(olderMessages);

    return (
        <Card className="mb-4 p-3 bg-slate-50 border-slate-200">
            <div className="flex items-center justify-between">
                <div className="flex-1">
                    <p className="text-xs font-medium text-slate-700 mb-1">
                        Previous Context ({olderMessages.length} older messages)
                    </p>
                    {!isCollapsed && (
                        <p className="text-xs text-slate-600 mt-2">
                            {summary}
                        </p>
                    )}
                </div>
                <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setIsCollapsed(!isCollapsed)}
                    className="ml-2"
                >
                    {isCollapsed ? (
                        <ChevronDown className="h-4 w-4" />
                    ) : (
                        <ChevronUp className="h-4 w-4" />
                    )}
                </Button>
            </div>
        </Card>
    );
}

/**
 * Generate a simple summary of older messages
 * Option A: Simple topic extraction
 */
function generateSummary(messages: ChatMessage[]): string {
    if (messages.length === 0) return "";

    // Count user questions and assistant responses
    const userMessages = messages.filter((m) => m.role === "user");
    const assistantMessages = messages.filter((m) => m.role === "assistant");

    // Extract first few words from user messages to show topics
    const topics = userMessages
        .slice(0, 3)
        .map((m) => {
            const words = m.content.trim().split(/\s+/).slice(0, 5);
            return words.join(" ");
        })
        .filter((t) => t.length > 0);

    if (topics.length === 0) {
        return `You had ${messages.length} previous messages in this conversation.`;
    }

    const topicsSummary = topics.map((t, i) => `"${t}..."`).join(", ");

    return `You asked about ${topicsSummary} and received ${assistantMessages.length} response${assistantMessages.length !== 1 ? "s" : ""}.`;
}
