"use client";

import { useEffect, useRef, useState } from "react";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { ChatMessage, Citation } from "@/types/chat";
import { Loader2, FileText } from "lucide-react";
import ReactMarkdown from "react-markdown";
import { CitationViewer } from "./CitationViewer";

interface MessageListProps {
    messages: ChatMessage[];
    botName: string;
    botAvatar?: string;
    streaming: boolean;
}

export default function MessageList({
    messages,
    botName,
    botAvatar,
    streaming,
}: MessageListProps) {
    const messagesEndRef = useRef<HTMLDivElement>(null);
    const [selectedCitation, setSelectedCitation] = useState<Citation | null>(null);
    const [selectedMessageText, setSelectedMessageText] = useState<string>("");

    // Auto-scroll to bottom on new messages
    useEffect(() => {
        const el = messagesEndRef.current as unknown as { scrollIntoView?: (opts?: ScrollIntoViewOptions) => void } | null;
        if (el && typeof el.scrollIntoView === "function") {
            el.scrollIntoView({ behavior: "smooth" });
        }
    }, [messages, streaming]);

    const highlightText = (text: string, messageText: string) => {
        if (!text) return text;

        // Common stopwords to exclude from highlighting
        const stopwords = new Set([
            "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
            "of", "with", "by", "from", "as", "is", "are", "was", "were", "be",
            "have", "has", "do", "does", "did", "can", "could", "will", "would",
            "should", "may", "might", "must", "shall", "that", "this", "these",
            "those", "you", "me", "he", "she", "it", "we", "they", "what", "which",
            "who", "when", "where", "why", "how", "all", "each", "every", "both",
            "i", "your", "our", "their", "my", "his", "her", "its", "not", "no",
            "yes", "more", "less", "very", "so", "too", "just", "only", "also",
        ]);

        // Extract keywords: words 5+ chars, not stopwords, unique
        const keywords = Array.from(
            new Set(
                (messageText.match(/\b\w{5,}\b/g) || [])
                    .map((word) => word.toLowerCase())
                    .filter((word) => !stopwords.has(word))
                    .slice(0, 8) // Top 8 keywords
            )
        );

        if (keywords.length === 0) return text;

        // Split chunk text into sentences
        const sentences = text.split(/(?<=[.!?])\s+/);
        
        // Score each sentence by keyword matches
        const scoredSentences = sentences.map((sentence, idx) => {
            const lowerSentence = sentence.toLowerCase();
            const matchCount = keywords.filter((kw) => lowerSentence.includes(kw)).length;
            return { sentence, idx, matchCount };
        });

        // Get top sentences with highest keyword density (at least 1 match, max 3 sentences)
        const topSentences = new Set(
            scoredSentences
                .filter((s) => s.matchCount > 0)
                .sort((a, b) => b.matchCount - a.matchCount)
                .slice(0, 3)
                .map((s) => s.idx)
        );

        // Rebuild text with highlights only in top-scoring sentences
        const escaped = keywords.map((word) =>
            word.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")
        );
        const regex = new RegExp(`(${escaped.join("|")})`, "gi");

        return sentences.map((sentence, idx) => {
            if (!topSentences.has(idx)) {
                return <span key={idx}>{sentence} </span>;
            }

            // Highlight keywords in this sentence
            const parts = sentence.split(regex);
            return (
                <span key={idx}>
                    {parts.map((part, partIdx) =>
                        keywords.includes(part.toLowerCase()) ? (
                            <mark
                                key={partIdx}
                                className="bg-amber-200/80 text-slate-900 px-0.5 rounded"
                            >
                                {part}
                            </mark>
                        ) : (
                            <span key={partIdx}>{part}</span>
                        )
                    )}{" "}
                </span>
            );
        });
    };

    return (
        <>
            <div className="space-y-4">
                {messages.map((message) => (
                    <div
                        key={message.id}
                        className={`flex gap-3 ${
                            message.role === "user" ? "justify-end" : "justify-start"
                        }`}
                    >
                        {message.role === "assistant" && (
                            <Avatar className="h-8 w-8 mt-1">
                                <AvatarImage src={botAvatar} alt={botName} />
                                <AvatarFallback className="bg-sky-500 text-white text-xs">
                                    {botName.charAt(0).toUpperCase()}
                                </AvatarFallback>
                            </Avatar>
                        )}
                        <div
                            className={`max-w-[70%] rounded-lg px-4 py-2 shadow-sm ${
                                message.role === "user"
                                    ? "bg-sky-600 text-white rounded-br-sm"
                                    : "bg-white border border-slate-100 rounded-bl-sm"
                            }`}
                        >
                            {message.role === "user" ? (
                                <p className="text-sm whitespace-pre-wrap">
                                    {message.content}
                                </p>
                            ) : (
                                <div className="prose prose-sm max-w-none">
                                    <ReactMarkdown
                                        components={{
                                            p: ({ children }) => (
                                                <p className="text-slate-800 leading-relaxed mb-2 last:mb-0">
                                                    {children}
                                                </p>
                                            ),
                                            strong: ({ children }) => (
                                                <strong className="font-semibold text-slate-900">
                                                    {children}
                                                </strong>
                                            ),
                                            em: ({ children }) => (
                                                <em className="italic">
                                                    {children}
                                                </em>
                                            ),
                                            code: ({ children, className }) => {
                                                const isInline = !className;
                                                return isInline ? (
                                                    <code className="bg-slate-100 text-red-600 px-1 py-0.5 rounded text-xs">
                                                        {children}
                                                    </code>
                                                ) : (
                                                    <code className="block bg-slate-100 p-2 rounded text-xs overflow-x-auto">
                                                        {children}
                                                    </code>
                                                );
                                            },
                                            ul: ({ children }) => (
                                                <ul className="list-disc list-inside space-y-1 my-2">
                                                    {children}
                                                </ul>
                                            ),
                                            ol: ({ children }) => (
                                                <ol className="list-decimal list-inside space-y-1 my-2">
                                                    {children}
                                                </ol>
                                            ),
                                            li: ({ children }) => (
                                                <li className="text-slate-800">
                                                    {children}
                                                </li>
                                            ),
                                            a: ({ children, href }) => (
                                                <a
                                                    href={href}
                                                    className="text-sky-600 hover:text-sky-700 underline"
                                                    target="_blank"
                                                    rel="noopener noreferrer"
                                                >
                                                    {children}
                                                </a>
                                            ),
                                        }}
                                    >
                                        {message.content}
                                    </ReactMarkdown>
                                    {message.citations && message.citations.length > 0 && (
                                        <div className="mt-4 pt-3 border-t border-slate-100">
                                            <p className="text-xs font-semibold text-slate-500 mb-2 uppercase tracking-wider">
                                                Sources
                                            </p>
                                            <div className="flex flex-wrap gap-2">
                                                {message.citations
                                                    .filter(c => (c.similarity ?? 0) >= 0.65)
                                                    .map((citation, idx) => (
                                                        <button
                                                            key={idx}
                                                            onClick={() => {
                                                                setSelectedCitation(citation);
                                                                setSelectedMessageText(message.content);
                                                            }}
                                                            className="flex items-center gap-1.5 px-2.5 py-1.5 bg-slate-50 hover:bg-sky-50 border border-slate-200 hover:border-sky-200 rounded text-xs font-medium text-slate-600 hover:text-sky-700 transition-colors"
                                                        >
                                                            <FileText size={12} />
                                                            <span className="truncate max-w-[150px]">
                                                                {citation.document_name || citation.source}
                                                            </span>
                                                        </button>
                                                    ))}
                                            </div>
                                        </div>
                                    )}
                                </div>
                            )}
                        </div>
                        {message.role === "user" && (
                            <Avatar className="h-8 w-8 mt-1">
                                <AvatarFallback className="bg-slate-700 text-white text-xs">
                                    You
                                </AvatarFallback>
                            </Avatar>
                        )}
                    </div>
                ))}

                {/* Typing Indicator */}
                {streaming && (
                    <div className="flex gap-3 justify-start">
                        <Avatar className="h-8 w-8 mt-1">
                            <AvatarImage src={botAvatar} alt={botName} />
                            <AvatarFallback className="bg-sky-500 text-white text-xs">
                                {botName.charAt(0).toUpperCase()}
                            </AvatarFallback>
                        </Avatar>
                        <div className="bg-white border border-slate-200 rounded-lg px-4 py-2">
                            <Loader2 className="h-4 w-4 animate-spin text-slate-400" />
                        </div>
                    </div>
                )}

                <div ref={messagesEndRef} />
            </div>

            {/* Citation Viewer Modal */}
            <CitationViewer
                citation={selectedCitation}
                open={!!selectedCitation}
                onOpenChange={(open) => !open && setSelectedCitation(null)}
                answerText={selectedMessageText}
            />
        </>
    );
}
