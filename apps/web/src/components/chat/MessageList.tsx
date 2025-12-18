"use client";

import { useEffect, useRef, useState } from "react";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { ChatMessage, Citation } from "@/types/chat";
import { Loader2, FileText, AlertCircle, CheckCircle2 } from "lucide-react";
import ReactMarkdown from "react-markdown";
import { CitationViewer } from "./CitationViewer";
import { sendToReviewQueue } from "@/lib/api/chat";
import ContextSummary from "./ContextSummary";

interface MessageListProps {
    messages: ChatMessage[];
    botName: string;
    botAvatar?: string;
    streaming: boolean;
    botId?: string;
    // Bot confidence threshold as percentage (0-100)
    confidenceThresholdPercent?: number;
    contextWindowSize?: number;
}

export default function MessageList({
    messages,
    botName,
    botAvatar,
    streaming,
    botId,
    confidenceThresholdPercent,
    contextWindowSize = 10,
}: MessageListProps) {
    const messagesEndRef = useRef<HTMLDivElement>(null);
    const [selectedCitation, setSelectedCitation] = useState<Citation | null>(null);
    const [selectedMessageText, setSelectedMessageText] = useState<string>("");
    const [sentToReview, setSentToReview] = useState<Set<string>>(new Set());
    const [sendingToReview, setSendingToReview] = useState<Set<string>>(new Set());

    // Default to 80% if not provided
    const reviewThreshold = Math.min(
        1,
        Math.max(0, (typeof confidenceThresholdPercent === "number" ? confidenceThresholdPercent : 80) / 100)
    );

    // Auto-scroll to bottom on new messages
    useEffect(() => {
        const el = messagesEndRef.current as unknown as { scrollIntoView?: (opts?: ScrollIntoViewOptions) => void } | null;
        if (el && typeof el.scrollIntoView === "function") {
            el.scrollIntoView({ behavior: "smooth" });
        }
    }, [messages, streaming]);

    // Auto-send low confidence messages to review queue
    useEffect(() => {
        if (!botId) return;
        
        messages.forEach((message, idx) => {
            if (
                message.role === "assistant" &&
                message.confidence !== undefined &&
                message.confidence < reviewThreshold &&
                !sentToReview.has(message.id) &&
                !sendingToReview.has(message.id)
            ) {
                // Find the user message before this one
                let userQuestion = "";
                for (let i = idx - 1; i >= 0; i--) {
                    if (messages[i].role === "user") {
                        userQuestion = messages[i].content;
                        break;
                    }
                }
                
                if (userQuestion) {
                    setSendingToReview(prev => new Set(prev).add(message.id));
                    
                    sendToReviewQueue(
                        botId,
                        userQuestion,
                        message.content,
                        message.confidence,
                        message.citations
                    ).then((result) => {
                        // Mark as sent even if backend reports logical failure,
                        // to avoid hammering the endpoint on every render
                        if (!result?.success) {
                            console.warn("Review queue send reported failure:", result?.message);
                        }
                        setSentToReview(prev => new Set(prev).add(message.id));
                    }).catch(err => {
                        console.error("Failed to send to review queue:", err);
                        // Prevent infinite retry loops on hard failures
                        setSentToReview(prev => new Set(prev).add(message.id));
                    }).finally(() => {
                        setSendingToReview(prev => {
                            const next = new Set(prev);
                            next.delete(message.id);
                            return next;
                        });
                    });
                }
            }
        });
    }, [messages, botId, sentToReview, sendingToReview, reviewThreshold]);

    return (
        <>
            <div className="space-y-4">
                {/* Context Summary (shown when messages exceed context window) */}
                <ContextSummary
                    messages={messages}
                    contextWindowSize={contextWindowSize}
                />
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
                                    {/* Confidence Bar */}
                                    {message.confidence !== undefined && (
                                        <div className="mt-3 pt-3 border-t border-slate-100">
                                            <div className="flex items-center gap-2 mb-1">
                                                <span className="text-xs font-medium text-slate-500">Certainty</span>
                                                <span className={`text-xs font-semibold ${
                                                    message.confidence >= 0.8 ? "text-green-600" : 
                                                    message.confidence >= 0.6 ? "text-amber-600" : "text-red-600"
                                                }`}>
                                                    {Math.round(message.confidence * 100)}%
                                                </span>
                                            </div>
                                            <div className="w-full h-2 bg-slate-100 rounded-full overflow-hidden">
                                                <div 
                                                    className={`h-full rounded-full transition-all duration-500 ${
                                                        message.confidence >= 0.8 ? "bg-green-500" : 
                                                        message.confidence >= 0.6 ? "bg-amber-500" : "bg-red-500"
                                                    }`}
                                                    style={{ width: `${Math.round(message.confidence * 100)}%` }}
                                                />
                                            </div>
                                            {message.confidence < reviewThreshold && (
                                                <div className="mt-2 flex items-center gap-1.5 text-xs">
                                                    {sendingToReview.has(message.id) ? (
                                                        <>
                                                            <Loader2 className="h-3 w-3 animate-spin text-amber-500" />
                                                            <span className="text-amber-600">Sending to review queue...</span>
                                                        </>
                                                    ) : sentToReview.has(message.id) ? (
                                                        <>
                                                            <CheckCircle2 className="h-3 w-3 text-green-500" />
                                                            <span className="text-green-600">Sent to team for review</span>
                                                        </>
                                                    ) : (
                                                        <>
                                                            <AlertCircle className="h-3 w-3 text-amber-500" />
                                                            <span className="text-amber-600">Will be sent to team for review</span>
                                                        </>
                                                    )}
                                                </div>
                                            )}
                                        </div>
                                    )}
                                    {message.citations && message.citations.length > 0 && (
                                        <div className="mt-4 pt-3 border-t border-slate-100">
                                            <p className="text-xs font-semibold text-slate-500 mb-2 uppercase tracking-wider">
                                                Sources
                                            </p>
                                            <div className="flex flex-wrap gap-2">
                                                {message.citations
                                                    // Show all citations provided by the backend;
                                                    // the backend already applies its own
                                                    // similarity thresholds when building the
                                                    // citations list.
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
