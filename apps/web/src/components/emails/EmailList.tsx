"use client";

import { useState, useEffect } from "react";
import { formatDistanceToNow } from "date-fns";
import {
    GmailMessage,
    importGmailMessage,
    listGmailMessages,
} from "@/lib/api/integrations";
import { ReplyComposer } from "./ReplyComposer";

interface EmailListProps {
    token: string;
    folder: "INBOX" | "SENT";
}

export function EmailList({ token, folder }: EmailListProps) {
    const [messages, setMessages] = useState<GmailMessage[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [importingId, setImportingId] = useState<string | null>(null);

    // Reply Composer State
    const [activeReplyMessage, setActiveReplyMessage] = useState<GmailMessage | null>(null);

    useEffect(() => {
        loadMessages();
    }, [folder, token]);

    const loadMessages = async () => {
        setIsLoading(true);
        setError(null);
        try {
            const data = await listGmailMessages(token, folder);
            setMessages(data.messages);
        } catch (e) {
            console.error("Error loading emails:", e);
            const msg = e instanceof Error ? e.message : "Failed to load emails. Please check your connection.";
            setError(msg);
        } finally {
            setIsLoading(false);
        }
    };

    const handleImport = async (messageId: string) => {
        setImportingId(messageId);
        try {
            await importGmailMessage(token, messageId);
            alert("Email imported to Knowledge Base!");
        } catch (e) {
            alert("Failed to import email.");
            console.error(e);
        } finally {
            setImportingId(null);
        }
    };

    if (isLoading) {
        return (
            <div className="flex justify-center p-12">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="bg-red-50 text-red-600 p-6 rounded-lg text-center break-words">
                <p className="font-semibold mb-2">Error Loading Emails</p>
                <p className="text-sm font-mono mb-4">{error}</p>
                <button
                    onClick={loadMessages}
                    className="mt-4 px-4 py-2 bg-white border border-red-200 rounded-md hover:bg-red-50"
                >
                    Retry
                </button>
            </div>
        );
    }

    if (messages.length === 0) {
        return (
            <div className="text-center p-12 text-gray-500 bg-gray-50 rounded-lg">
                No emails found in your {folder.toLowerCase()}.
            </div>
        );
    }

    return (
        <div className="space-y-4">
            {messages.map((msg) => (
                <div
                    key={msg.id}
                    className="bg-white border border-gray-200 rounded-lg p-4 hover:border-indigo-300 transition-colors shadow-sm"
                >
                    <div className="flex justify-between items-start mb-2">
                        <div>
                            <h3 className="font-semibold text-gray-900 line-clamp-1">
                                {msg.subject}
                            </h3>
                            <div className="text-sm text-gray-500 flex gap-2">
                                <span className="font-medium text-gray-700">
                                    {folder === "INBOX" ? msg.from : `To: ${msg.to}`}
                                </span>
                                <span>•</span>
                                <span>
                                    {msg.date
                                        ? formatDistanceToNow(new Date(msg.date), {
                                            addSuffix: true,
                                        })
                                        : "Unknown date"}
                                </span>
                            </div>
                        </div>
                        <div className="flex space-x-2">
                            {folder === "INBOX" && (
                                <button
                                    onClick={() => setActiveReplyMessage(msg)}
                                    className="px-3 py-1.5 text-xs font-medium text-indigo-600 bg-indigo-50 hover:bg-indigo-100 rounded-md transition-colors"
                                >
                                    Generate Reply
                                </button>
                            )}
                            <button
                                onClick={() => handleImport(msg.id)}
                                disabled={importingId === msg.id}
                                className="px-3 py-1.5 text-xs font-medium text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-md transition-colors disabled:opacity-50"
                            >
                                {importingId === msg.id ? "Importing..." : "Import to KB"}
                            </button>
                        </div>
                    </div>
                    <p className="text-sm text-gray-600 line-clamp-2">{msg.snippet}</p>
                </div>
            ))}

            {activeReplyMessage && (
                <ReplyComposer
                    isOpen={!!activeReplyMessage}
                    onClose={() => setActiveReplyMessage(null)}
                    token={token}
                    messageId={activeReplyMessage.id}
                    threadId={activeReplyMessage.threadId}
                    originalText={activeReplyMessage.snippet}
                    to={activeReplyMessage.from}
                    subject={activeReplyMessage.subject}
                />
            )}
        </div>
    );
}
