"use client";

import { useEffect, useRef } from "react";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { ChatMessage } from "@/types/chat";
import { Loader2 } from "lucide-react";
import ReactMarkdown from "react-markdown";

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

    // Auto-scroll to bottom on new messages
    useEffect(() => {
        const el = messagesEndRef.current as unknown as { scrollIntoView?: (opts?: ScrollIntoViewOptions) => void } | null;
        if (el && typeof el.scrollIntoView === "function") {
            el.scrollIntoView({ behavior: "smooth" });
        }
    }, [messages, streaming]);

    return (
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
                                ? "bg-gradient-to-br from-sky-500 to-sky-600 text-white"
                                : "bg-slate-50 border border-slate-200"
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
                                        // Style markdown elements
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
                                        <div className="mt-3 pt-3 border-t border-slate-200">
                                            <p className="text-xs font-medium text-slate-600 mb-1">Sources ({message.citations.length}):</p>
                                            <div className="space-y-1">
                                                {message.citations.map(
                                                    (citation, idx) => (
                                                        <p
                                                            key={idx}
                                                            className="text-xs text-slate-600"
                                                        >
                                                            {citation.url ? (
                                                                <a
                                                                    href={
                                                                        citation.url
                                                                    }
                                                                    className="text-sky-600 hover:text-sky-700 hover:underline"
                                                                    target="_blank"
                                                                    rel="noopener noreferrer"
                                                                >
                                                                    [Source:{" "}
                                                                    {
                                                                        citation.source
                                                                    }
                                                                    ]
                                                                </a>
                                                            ) : (
                                                                `[Source: ${citation.source}]`
                                                            )}
                                                        </p>
                                                    )
                                                )}
                                            </div>
                                        </div>
                                    )}
                            </div>
                        )}
                    </div>
                    {message.role === "assistant" && message.confidence !== undefined && (
                        <div className="max-w-[70%] text-xs">
                            <div className="flex items-center gap-2 px-1">
                                <span className="text-slate-500">Confidence:</span>
                                <div className="flex items-center gap-1">
                                    <div className="w-12 h-1 bg-slate-200 rounded-full overflow-hidden">
                                        <div
                                            className={`h-full rounded-full ${
                                                message.confidence >= 80
                                                    ? "bg-emerald-500"
                                                    : message.confidence >= 60
                                                    ? "bg-amber-500"
                                                    : "bg-orange-500"
                                            }`}
                                            style={{
                                                width: `${Math.min(message.confidence, 100)}%`,
                                            }}
                                        />
                                    </div>
                                    <span className={`font-medium ${
                                        message.confidence >= 80
                                            ? "text-emerald-600"
                                            : message.confidence >= 60
                                            ? "text-amber-600"
                                            : "text-orange-600"
                                    }`}>
                                        {Math.round(message.confidence)}%
                                    </span>
                                </div>
                            </div>
                        </div>
                    )}
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
    );
}
