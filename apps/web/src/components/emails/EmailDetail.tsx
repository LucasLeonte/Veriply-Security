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
    const [message, setMessage] = useState<any>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [importing, setImporting] = useState(false);
    const [showReply, setShowReply] = useState(false);

    useEffect(() => {
        let mounted = true;

        async function fetchMessage() {
            setLoading(true);
            setError(null);
            setMessage(null);

            try {
                const data = await getGmailMessage(token, messageId);
                if (mounted) setMessage(data);
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
            alert("Email imported to Knowledge Base!");
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

    if (!message) return null;

    // Helper to extract body (prefer HTML, fallback to snippet or text)
    // Real Gmail API returns 'payload.body.data' or 'payload.parts'
    // We'll simplistic logic for now assuming the backend might have simplified it or we parse basics
    const getBody = () => {
        // If backend returned a simplified object
        if (message.body) return <div dangerouslySetInnerHTML={{ __html: message.body }} />;

        // Fallback to snippet if full body parsing is complex on backend still
        return <div className="whitespace-pre-wrap font-sans text-gray-800">{message.snippet}</div>;
    };

    return (
        <div className="h-full flex flex-col bg-white">
            {/* Header Toolbar */}
            <div className="h-16 border-b flex items-center justify-between px-6 shrink-0 bg-white">
                <div className="flex items-center gap-2">
                    {onClose && (
                        <Button variant="ghost" size="icon" onClick={onClose} className="md:hidden">
                            <ArrowLeft className="h-5 w-5" />
                        </Button>
                    )}
                    <div className="flex gap-1">
                        <Button variant="ghost" size="icon" title="Archive">
                            <Trash2 className="h-5 w-5 text-gray-500 hover:text-red-600" />
                        </Button>
                        <Button
                            variant="ghost"
                            size="icon"
                            title="Import to Knowledge Base"
                            onClick={handleImport}
                            disabled={importing}
                        >
                            <ImportIcon className={`h-5 w-5 ${importing ? 'animate-pulse text-indigo-600' : 'text-gray-500'}`} />
                        </Button>
                    </div>
                </div>
                <div className="flex items-center gap-2">
                    <span className="text-xs text-muted-foreground mr-2">
                        {message.date && formatDistanceToNow(new Date(message.date), { addSuffix: true })}
                    </span>
                    <Button variant="ghost" size="icon">
                        <MoreVertical className="h-5 w-5 text-gray-500" />
                    </Button>
                </div>
            </div>

            {/* Scrollable Content */}
            <div className="flex-1 overflow-y-auto">
                <div className="max-w-4xl mx-auto p-8">
                    {/* Subject */}
                    <h1 className="text-2xl font-semibold text-gray-900 mb-6">{message.subject}</h1>

                    {/* Sender Info */}
                    <div className="flex items-center gap-4 mb-8">
                        <Avatar className="h-10 w-10">
                            <AvatarFallback className="bg-indigo-100 text-indigo-700 font-medium">
                                {message.from?.charAt(0).toUpperCase() || "?"}
                            </AvatarFallback>
                        </Avatar>
                        <div className="flex-1 min-w-0">
                            <div className="font-medium text-gray-900 truncate">
                                {message.from}
                            </div>
                            <div className="text-sm text-gray-500 truncate">
                                to {message.to}
                            </div>
                        </div>
                    </div>

                    {/* Email Body */}
                    <div className="prose prose-slate max-w-none text-gray-800">
                        {getBody()}
                    </div>

                    <Separator className="my-8" />

                    {/* Reply Area Button */}
                    {!showReply && (
                        <Button
                            className="gap-2"
                            variant="outline"
                            onClick={() => setShowReply(true)}
                        >
                            <Reply className="h-4 w-4" /> Reply
                        </Button>
                    )}

                    {/* Reply Composer Inline */}
                    {showReply && (
                        <div className="mt-4 border rounded-lg p-4 bg-gray-50">
                            <ReplyComposer
                                isOpen={true}
                                onClose={() => setShowReply(false)}
                                token={token}
                                messageId={message.id}
                                threadId={message.threadId}
                                originalText={message.snippet} // Ideally pass full body context
                                to={message.from}
                                subject={message.subject}
                                inline={true} // We might need to modify Composer to support inline mode
                            />
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
