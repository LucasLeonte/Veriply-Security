"use client";

import { useEffect, useRef, useState } from "react";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { ChatMessage } from "@/types/chat";
import { Loader2, FileText } from "lucide-react";
import ReactMarkdown from "react-markdown";
import { CitationViewer } from "./CitationViewer";
import FeedbackBar, { FeedbackSnapshot } from "../FeedbackBar";

interface MessageListProps {
    messages: ChatMessage[];
    botName: string;
    botAvatar?: string;
    streaming: boolean;
    feedbackState: Record<string, FeedbackSnapshot>;
    onSubmitFeedback: (args: {
        messageId: string;
        answerId?: string;
        type: "positive" | "negative";
        reason?: "incorrect" | "not_helpful" | "incomplete" | "harmful" | "other";
        notes?: string;
    }) => Promise<{ success: boolean; error?: string } | void>;
}

export default function MessageList({
    messages,
    botName,
    botAvatar,
    streaming,
    feedbackState,
    onSubmitFeedback,
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

    // Highlighting logic has moved into CitationViewer

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

                                    <FeedbackBar
                                        messageId={message.id}
                                        answerId={message.answerId}
                                        state={feedbackState[message.id]}
                                        onSubmit={onSubmitFeedback}
                                    />
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
