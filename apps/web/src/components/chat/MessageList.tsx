"use client";

import { useEffect, useRef, useState } from "react";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { User } from "lucide-react";
import { ChatMessage, Citation } from "@/types/chat";
import { Loader2, FileText, AlertCircle } from "lucide-react";
import ReactMarkdown from "react-markdown";
import { CitationViewer } from "./CitationViewer";
import ContextSummary from "./ContextSummary";
import TrustBadge from "./TrustBadge";
import PendingVerification from "./PendingVerification";
import FeedbackBar, { FeedbackSnapshot } from "../FeedbackBar";
import { sendToReviewQueue } from "@/lib/api/chat";
import { getAccessToken } from "@/lib/auth";

interface MessageListProps {
    messages: ChatMessage[];
    botName: string;
    botAvatar?: string;
    streaming: boolean;
    botId?: string;
    sessionId?: string;
    // Bot confidence threshold as percentage (0-100)
    confidenceThresholdPercent?: number;
    contextWindowSize?: number;
    feedbackState?: Record<string, FeedbackSnapshot>;
    onSubmitFeedback?: (args: {
        messageId: string;
        answerId?: string;
        type: "positive" | "negative";
        reason?:
            | "incorrect"
            | "not_helpful"
            | "incomplete"
            | "harmful"
            | "other";
        notes?: string;
    }) => Promise<{ success: boolean; error?: string } | void>;
}

export default function MessageList({
    messages,
    botName,
    botAvatar,
    streaming,
    botId,
    sessionId,
    confidenceThresholdPercent,
    contextWindowSize = 10,
    feedbackState = {},
    onSubmitFeedback,
}: MessageListProps) {
    const messagesEndRef = useRef<HTMLDivElement>(null);
    const [selectedCitation, setSelectedCitation] = useState<Citation | null>(
        null
    );
    const [selectedMessageText, setSelectedMessageText] = useState<string>("");
    const [sentToReview, setSentToReview] = useState<Set<string>>(new Set());
    const [sendingToReview, setSendingToReview] = useState<Set<string>>(
        new Set()
    );
    const [userProfile, setUserProfile] = useState<{
        name?: string;
        avatar_url?: string;
    } | null>(null);

    // Use ref to track submission attempts across renders (persists between useEffect calls)
    const submissionAttemptsRef = useRef<Set<string>>(new Set());

    // Default to 80% if not provided
    const reviewThreshold = Math.min(
        1,
        Math.max(
            0,
            (typeof confidenceThresholdPercent === "number"
                ? confidenceThresholdPercent
                : 80) / 100
        )
    );

    // Fetch user profile on component mount
    useEffect(() => {
        const loadUserProfile = async () => {
            try {
                const token = getAccessToken();
                if (!token) return;

                const apiUrl =
                    process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";
                const response = await fetch(`${apiUrl}/api/v1/profile/me`, {
                    method: "GET",
                    headers: {
                        Authorization: `Bearer ${token}`,
                    },
                });

                if (!response.ok) return;

                const data = await response.json();
                setUserProfile({
                    name: data?.name,
                    avatar_url: data?.avatar_url,
                });
            } catch (err) {}
        };

        loadUserProfile();
    }, []);

    // Auto-scroll to bottom on new messages
    useEffect(() => {
        const el = messagesEndRef.current as unknown as {
            scrollIntoView?: (opts?: ScrollIntoViewOptions) => void;
        } | null;
        if (el && typeof el.scrollIntoView === "function") {
            el.scrollIntoView({ behavior: "smooth" });
        }
    }, [messages, streaming]);

    // Auto-send low confidence messages to review queue
    useEffect(() => {
        if (!botId || !sessionId) return;

        messages.forEach((message, idx) => {
            // Skip if already processed using ref (guards against concurrent useEffect runs)
            if (submissionAttemptsRef.current.has(message.id)) return;

            // Treat missing confidence as 0 to ensure unanswered/empty replies still go to HITL
            const effectiveConfidence =
                message.confidence !== undefined ? message.confidence : 0;

            if (
                message.role === "assistant" &&
                effectiveConfidence < reviewThreshold &&
                !sentToReview.has(message.id) &&
                !sendingToReview.has(message.id)
            ) {
                // Mark as attempted immediately to prevent duplicate calls
                submissionAttemptsRef.current.add(message.id);

                // Find the user message before this one
                let userQuestion = "";
                for (let i = idx - 1; i >= 0; i--) {
                    if (messages[i].role === "user") {
                        userQuestion = messages[i].content;
                        break;
                    }
                }

                if (userQuestion) {
                    setSendingToReview((prev) => new Set(prev).add(message.id));

                    sendToReviewQueue(
                        botId,
                        userQuestion,
                        message.content,
                        effectiveConfidence,
                        message.citations,
                        sessionId
                    )
                        .then(
                            (result: {
                                success: boolean;
                                message?: string;
                            }) => {
                                // Mark as sent even if backend reports logical failure,
                                // to avoid hammering the endpoint on every render
                                if (!result?.success) {
                                }
                                setSentToReview((prev) =>
                                    new Set(prev).add(message.id)
                                );
                            }
                        )
                        .catch((err: Error) => {
                            // Prevent infinite retry loops on hard failures
                            setSentToReview((prev) =>
                                new Set(prev).add(message.id)
                            );
                        })
                        .finally(() => {
                            setSendingToReview((prev) => {
                                const next = new Set(prev);
                                next.delete(message.id);
                                return next;
                            });
                        });
                } else {
                    // No user question found, remove from attempts so it can retry
                    submissionAttemptsRef.current.delete(message.id);
                }
            }
        });
    }, [
        messages,
        botId,
        sessionId,
        sentToReview,
        sendingToReview,
        reviewThreshold,
    ]);

    return (
        <>
            <div className="space-y-4">
                {/* Context Summary (shown when messages exceed context window) */}
                <ContextSummary
                    messages={messages}
                    contextWindowSize={contextWindowSize}
                />
                {messages
                    .filter((msg) => msg.role === "user" || msg.content)
                    .map((message) => (
                        <div
                            key={message.id}
                            className={`flex gap-3 ${
                                message.role === "user"
                                    ? "justify-end"
                                    : "justify-start"
                            }`}
                        >
                            {message.role === "assistant" && (
                                <Avatar className="h-8 w-8 mt-1">
                                    <AvatarImage
                                        src={botAvatar}
                                        alt={botName}
                                    />
                                    <AvatarFallback className="bg-sky-500 text-white text-xs">
                                        <User className="w-full h-full" />
                                    </AvatarFallback>
                                </Avatar>
                            )}

                            <div
                                className={`flex flex-col gap-1 max-w-[85%] md:max-w-[75%] ${
                                    message.role === "user"
                                        ? "items-end"
                                        : "items-start"
                                }`}
                            >
                                {/* Pending verification state */}
                                {message.role === "assistant" &&
                                message.trustLevel === "pending" &&
                                botId ? (
                                    <div className="w-full">
                                        <PendingVerification
                                            messageId={message.id}
                                            botId={botId}
                                        />
                                    </div>
                                ) : (
                                    <div
                                        className={`w-full px-5 py-3 shadow-sm ${
                                            message.role === "user"
                                                ? "bg-gradient-to-br from-sky-600 to-blue-600 text-white rounded-2xl rounded-tr-sm"
                                                : "bg-white border border-slate-100 rounded-2xl rounded-tl-sm shadow-sm"
                                        }`}
                                    >
                                        {message.role === "user" ? (
                                            <p className="text-sm whitespace-pre-wrap text-left">
                                                {message.content}
                                            </p>
                                        ) : (
                                            <div className="prose prose-sm max-w-none text-left">
                                                <ReactMarkdown
                                                    components={{
                                                        p: ({ children }) => (
                                                            <p className="text-slate-700 leading-relaxed mb-3 last:mb-0">
                                                                {children}
                                                            </p>
                                                        ),
                                                        strong: ({
                                                            children,
                                                        }) => (
                                                            <strong className="font-semibold text-slate-900">
                                                                {children}
                                                            </strong>
                                                        ),
                                                        em: ({ children }) => (
                                                            <em className="italic">
                                                                {children}
                                                            </em>
                                                        ),
                                                        code: ({
                                                            children,
                                                            className,
                                                        }) => {
                                                            const isInline =
                                                                !className;
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
                                                        a: ({
                                                            children,
                                                            href,
                                                        }) => (
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

                                                {message.confidence !==
                                                    undefined && (
                                                    <div className="mt-3 pt-3 border-t border-slate-100">
                                                        <div className="flex items-center gap-2 mb-1">
                                                            <span className="text-xs font-medium text-slate-500">
                                                                Certainty
                                                            </span>
                                                            <span
                                                                className={`text-xs font-semibold ${
                                                                    message.confidence >
                                                                    0.75
                                                                        ? "text-green-600"
                                                                        : message.confidence >
                                                                          0.3
                                                                        ? "text-amber-600"
                                                                        : "text-red-600"
                                                                }`}
                                                            >
                                                                {Math.round(
                                                                    message.confidence *
                                                                        100
                                                                )}
                                                                %
                                                            </span>
                                                        </div>
                                                        <div className="w-full h-2 bg-slate-100 rounded-full overflow-hidden">
                                                            <div
                                                                className={`h-full rounded-full transition-all duration-500 ${
                                                                    message.confidence >
                                                                    0.75
                                                                        ? "bg-green-500"
                                                                        : message.confidence >
                                                                          0.3
                                                                        ? "bg-amber-500"
                                                                        : "bg-red-500"
                                                                }`}
                                                                style={{
                                                                    width: `${Math.round(
                                                                        message.confidence *
                                                                            100
                                                                    )}%`,
                                                                }}
                                                            />
                                                        </div>
                                                        {/* Low confidence messages are automatically routed to HITL review by the backend */}
                                                        {message.confidence <
                                                            (confidenceThresholdPercent
                                                                ? confidenceThresholdPercent /
                                                                  100
                                                                : 0.8) && (
                                                            <div className="mt-2 flex items-center gap-1.5 text-xs">
                                                                <AlertCircle className="h-3 w-3 text-amber-500" />
                                                                <span className="text-amber-600">
                                                                    Sent to team
                                                                    for review
                                                                </span>
                                                            </div>
                                                        )}
                                                    </div>
                                                )}

                                                {message.citations &&
                                                    message.citations.length >
                                                        0 && (
                                                        <div className="mt-4 pt-3 border-t border-slate-100">
                                                            <p className="text-xs font-semibold text-slate-500 mb-2 uppercase tracking-wider">
                                                                Sources
                                                            </p>
                                                            <div className="flex flex-wrap gap-2">
                                                                {message.citations.map(
                                                                    (
                                                                        citation,
                                                                        idx
                                                                    ) => (
                                                                        <button
                                                                            key={
                                                                                idx
                                                                            }
                                                                            onClick={() => {
                                                                                setSelectedCitation(
                                                                                    citation
                                                                                );
                                                                                setSelectedMessageText(
                                                                                    message.content
                                                                                );
                                                                            }}
                                                                            className="flex items-center gap-1.5 px-2.5 py-1.5 bg-slate-50 hover:bg-sky-50 border border-slate-200 hover:border-sky-200 rounded text-xs font-medium text-slate-600 hover:text-sky-700 transition-colors"
                                                                        >
                                                                            <FileText
                                                                                size={
                                                                                    12
                                                                                }
                                                                            />
                                                                            <span className="truncate max-w-[150px]">
                                                                                {citation.document_name ||
                                                                                    citation.source}
                                                                            </span>
                                                                        </button>
                                                                    )
                                                                )}
                                                            </div>
                                                        </div>
                                                    )}

                                                {message.trustLevel ? (
                                                    <div className="mt-4 pt-3 border-t border-slate-100">
                                                        <TrustBadge
                                                            trustLevel={
                                                                message.trustLevel
                                                            }
                                                            confidenceScore={
                                                                message.confidenceScore
                                                            }
                                                        />
                                                    </div>
                                                ) : null}
                                            </div>
                                        )}
                                    </div>
                                )}

                                {/* Only show feedback bar for completed messages (not while streaming) */}
                                {message.role === "assistant" &&
                                    onSubmitFeedback &&
                                    message.content &&
                                    !streaming && (
                                        <FeedbackBar
                                            messageId={message.id}
                                            answerId={message.answerId}
                                            state={feedbackState[message.id]}
                                            onSubmit={onSubmitFeedback}
                                        />
                                    )}
                            </div>

                            {message.role === "user" && (
                                <Avatar className="h-8 w-8 mt-1">
                                    <AvatarImage
                                        src={userProfile?.avatar_url}
                                        alt={userProfile?.name || "User"}
                                    />
                                    <AvatarFallback className="bg-blue-500 text-white text-xs">
                                        <User className="w-full h-full" />
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
                                <User className="w-full h-full" />
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
