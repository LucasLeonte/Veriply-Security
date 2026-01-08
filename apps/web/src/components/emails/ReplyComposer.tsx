"use client";

import { useEffect, useState } from "react";
import { generateGmailReply, sendGmailReply } from "@/lib/api/integrations";

interface ReplyComposerProps {
    isOpen: boolean;
    onClose: () => void;
    token: string;
    messageId: string;
    threadId: string;
    originalText: string;
    to: string;
    subject?: string;
    botId?: string;
}

export function ReplyComposer({
    isOpen,
    onClose,
    token,
    messageId,
    threadId,
    originalText,
    to,
    subject,
    botId,
}: ReplyComposerProps) {
    const [reply, setReply] = useState<string>("");
    const [isLoading, setIsLoading] = useState(false);
    const [isSending, setIsSending] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [success, setSuccess] = useState(false);

    useEffect(() => {
        if (isOpen && messageId) {
            generateReply();
        }
    }, [isOpen, messageId]);

    const generateReply = async () => {
        setIsLoading(true);
        setError(null);
        try {
            const result = await generateGmailReply(token, messageId, originalText, {
                subject,
                botId,
            });
            setReply(result.reply);
        } catch (e) {
            setError("Failed to generate reply. Please try again.");
            console.error(e);
        } finally {
            setIsLoading(false);
        }
    };

    const copyToClipboard = () => {
        navigator.clipboard.writeText(reply);
        alert("Copied to clipboard!");
    };

    const sendReply = async () => {
        setIsSending(true);
        setError(null);
        try {
            await sendGmailReply(
                token,
                threadId,
                messageId,
                to,
                subject || "No Subject",
                reply
            );
            setSuccess(true);
            setTimeout(() => {
                onClose();
                setSuccess(false);
            }, 2000);
        } catch (e) {
            setError("Failed to send reply. Please try again.");
            console.error(e);
        } finally {
            setIsSending(false);
        }
    };

    if (!isOpen) return null;

    if (success) {
        return (
            <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
                <div className="bg-white rounded-lg shadow-xl w-full max-w-md p-6 text-center">
                    <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                        <svg className="w-8 h-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                        </svg>
                    </div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-2">Reply Sent!</h3>
                    <p className="text-gray-600">Your email has been sent successfully.</p>
                </div>
            </div>
        );
    }

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
            <div className="bg-white rounded-lg shadow-xl w-full max-w-2xl p-6 relative">
                <button
                    onClick={onClose}
                    className="absolute top-4 right-4 text-gray-400 hover:text-gray-600"
                >
                    ✕
                </button>
                <h2 className="text-xl font-semibold mb-4 text-gray-900">AI Draft Reply</h2>

                {isLoading ? (
                    <div className="flex items-center justify-center h-48">
                        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
                        <span className="ml-3 text-gray-500">Generating draft...</span>
                    </div>
                ) : error ? (
                    <div className="bg-red-50 text-red-600 p-4 rounded-md">
                        {error}
                        <button
                            onClick={generateReply}
                            className="ml-4 underline hover:text-red-800"
                        >
                            Retry
                        </button>
                    </div>
                ) : (
                    <div className="space-y-4">
                        <textarea
                            className="w-full h-64 p-4 border border-gray-200 rounded-md focus:ring-2 focus:ring-indigo-500 focus:border-transparent text-gray-800"
                            value={reply}
                            onChange={(e) => setReply(e.target.value)}
                            disabled={isSending}
                        />
                        <div className="flex justify-end space-x-3">
                            <button
                                onClick={onClose}
                                className="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-md"
                                disabled={isSending}
                            >
                                Close
                            </button>
                            <button
                                onClick={copyToClipboard}
                                className="px-4 py-2 border border-indigo-600 text-indigo-600 rounded-md hover:bg-indigo-50"
                                disabled={isSending}
                            >
                                Copy to Clipboard
                            </button>
                            <button
                                onClick={sendReply}
                                className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                                disabled={isSending || !reply.trim()}
                            >
                                {isSending ? (
                                    <>
                                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                                        Sending...
                                    </>
                                ) : (
                                    "Send Reply"
                                )}
                            </button>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}
