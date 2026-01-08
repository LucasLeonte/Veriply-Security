"use client";

import { useEffect, useState } from "react";
import { formatDistanceToNow } from "date-fns";
import { getGmailMessage, importGmailMessage } from "@/lib/api/integrations";
import { ReplyComposer } from "./ReplyComposer";
import { ArrowLeft, MoreVertical, Paperclip, Reply, Trash2, Import as ImportIcon, Loader2 } from "lucide-react";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";

interface EmailDetailProps {
    token: string;
    messageId: string;
    onClose?: () => void; // For mobile view
}

export function EmailDetail({ token, messageId, onClose }: EmailDetailProps) {
    const [thread, setThread] = useState<any>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [importing, setImporting] = useState(false);
    const [showReply, setShowReply] = useState(false);

    useEffect(() => {
        let mounted = true;

        async function fetchMessage() {
            setLoading(true);
            setError(null);
            setThread(null);

            try {
                const data = await getGmailMessage(token, messageId);
                if (mounted) setThread(data);
            } catch (err) {
                if (mounted) setError(err instanceof Error ? err.message : "Failed to load email");
            } finally {
                if (mounted) setLoading(false);
            }
        }

        if (messageId) {
            fetchMessage();
        }

        return () => { mounted = false; };
    }, [token, messageId]);

    const handleImport = async () => {
        setImporting(true);
        try {
            await importGmailMessage(token, messageId);
            alert("Email thread imported to Knowledge Base!");
        } catch (e) {
            alert("Failed to import email.");
        } finally {
            setImporting(false);
        }
    };

    if (loading) {
        return (
            <div className="h-full flex items-center justify-center bg-white">
                <Loader2 className="h-8 w-8 animate-spin text-indigo-600" />
            </div>
        );
    }

    if (error) {
        return (
            <div className="h-full flex flex-col items-center justify-center bg-white text-gray-500 gap-2">
                <p>{error}</p>
                <Button variant="outline" onClick={() => window.location.reload()}>Retry</Button>
            </div>
        );
    }

    if (!thread || !thread.messages) return null;

    const messages = thread.messages || [];
    const lastMessage = messages[messages.length - 1];

    return (
        <div className="h-full flex flex-col bg-white">
            {/* Header Toolbar */}
            <div className="h-16 border-b flex items-center justify-between px-6 shrink-0 bg-white shadow-sm z-10">
                <div className="flex items-center gap-2">
                    {onClose && (
                        <Button variant="ghost" size="icon" onClick={onClose} className="md:hidden">
                            <ArrowLeft className="h-5 w-5" />
                        </Button>
                    )}
                    <div className="flex gap-2">
                        <Button variant="ghost" size="icon" title="Archive">
                            <Trash2 className="h-5 w-5 text-gray-500 hover:text-red-600" />
                        </Button>
                        <Button
                            variant="outline"
                            size="sm"
                            title="Save Thread to Knowledge Base"
                            onClick={handleImport}
                            disabled={importing}
                            className="gap-2 text-indigo-600 border-indigo-200 hover:bg-indigo-50"
                        >
                            <ImportIcon className={`h-4 w-4 ${importing ? 'animate-pulse' : ''}`} />
                            Save Thread to KB
                        </Button>
                    </div>
                </div>
                <div className="flex items-center gap-2">
                    <span className="text-xs text-muted-foreground mr-2 bg-gray-100 px-2 py-1 rounded-full">
                        {messages.length} message{messages.length !== 1 ? 's' : ''}
                    </span>
                    <Button variant="ghost" size="icon">
                        <MoreVertical className="h-5 w-5 text-gray-500" />
                    </Button>
                </div>
            </div>

            {/* Scrollable Content */}
            <div className="flex-1 overflow-y-auto bg-gray-50/50">
                <div className="max-w-4xl mx-auto p-8">
                    {/* Thread Subject */}
                    <h1 className="text-2xl font-semibold text-gray-900 mb-8 px-4">{thread.subject}</h1>

                    {/* Messages List */}
                    <div className="space-y-6">
                        {messages.map((msg: any, index: number) => (
                            <div
                                key={msg.id}
                                className={`bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden ${index === messages.length - 1 ? 'ring-2 ring-indigo-500/10' : ''
                                    }`}
                            >
                                {/* Message Header */}
                                <div className="bg-white px-6 py-4 flex items-start gap-4 border-b border-gray-50">
                                    <Avatar className="h-10 w-10 mt-1">
                                        <AvatarFallback className={`text-sm font-medium ${index === messages.length - 1 ? 'bg-indigo-600 text-white' : 'bg-gray-100 text-gray-600'
                                            }`}>
                                            {msg.from?.charAt(0).toUpperCase() || "?"}
                                        </AvatarFallback>
                                    </Avatar>
                                    <div className="flex-1 min-w-0">
                                        <div className="flex items-center justify-between">
                                            <div className="font-semibold text-gray-900 truncate">
                                                {msg.from}
                                            </div>
                                            <div className="text-xs text-gray-500 whitespace-nowrap ml-2">
                                                {msg.date && formatDistanceToNow(new Date(msg.date), { addSuffix: true })}
                                            </div>
                                        </div>
                                        <div className="text-sm text-gray-500 truncate">
                                            to {msg.to}
                                        </div>
                                    </div>
                                </div>

                                {/* Message Body */}
                                <div className="p-6 prose prose-slate max-w-none text-gray-800 text-sm leading-relaxed">
                                    {msg.body ? (
                                        <div dangerouslySetInnerHTML={{ __html: msg.body }} />
                                    ) : (
                                        <div className="whitespace-pre-wrap font-sans">{msg.snippet}</div>
                                    )}
                                </div>
                            </div>
                        ))}
                    </div>

                    <div className="h-8" /> {/* Spacer */}

                    {/* Reply Area Button */}
                    {!showReply && (
                        <div className="sticky bottom-8 flex justify-center">
                            <Button
                                className="gap-2 shadow-lg hover:shadow-xl transition-all rounded-full px-6 h-12 bg-white text-indigo-600 border border-indigo-100 hover:bg-indigo-50"
                                onClick={() => setShowReply(true)}
                            >
                                <span className="text-lg">✨</span>
                                <span className="font-medium">Draft AI Reply</span>
                            </Button>
                        </div>
                    )}

                    {/* Reply Composer Inline */}
                    {showReply && (
                        <div className="mt-8 border bg-white rounded-xl shadow-lg overflow-hidden animate-in slide-in-from-bottom-4 duration-300">
                            <ReplyComposer
                                isOpen={true}
                                onClose={() => setShowReply(false)}
                                token={token}
                                messageId={lastMessage.id}
                                threadId={thread.id} // Use thread ID from the fetch
                                originalText={lastMessage.snippet} // Ideally pass full body context
                                to={lastMessage.from}
                                subject={thread.subject}
                                inline={true}
                            />
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
