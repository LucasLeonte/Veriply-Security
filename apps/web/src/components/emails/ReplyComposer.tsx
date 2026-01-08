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
    inline?: boolean;
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
    inline = false,
}: ReplyComposerProps) {
    const [reply, setReply] = useState<string>("");
    const [isLoading, setIsLoading] = useState(false);
    const [isSending, setIsSending] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [success, setSuccess] = useState(false);

    useEffect(() => {
        if (isOpen && messageId) {
            // Only generate if empty (don't overwrite user changes)
            if (!reply) generateReply();
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
                setReply(""); // Reset
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
        const SuccessContent = (
            <div className="bg-white rounded-lg p-6 text-center w-full">
                <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                    <svg className="w-8 h-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                </div>
                <h3 className="text-lg font-semibold text-gray-900 mb-2">Reply Sent!</h3>
                <p className="text-gray-600">Your email has been sent successfully.</p>
            </div>
        );

        if (inline) return SuccessContent;

        return (
            <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
                <div className="bg-white rounded-lg shadow-xl w-full max-w-md p-6 relative">
                    {SuccessContent}
                </div>
            </div>
        );
    }

    const Content = (
        <div className={`bg-white rounded-xl w-full ${inline ? '' : 'shadow-2xl max-w-2xl p-8 relative ring-1 ring-gray-200'}`}>
            {!inline && (
                <button
                    onClick={onClose}
                    className="absolute top-6 right-6 text-gray-400 hover:text-gray-600 transition-colors"
                >
                    ✕
                </button>
            )}

            <div className="mb-6">
                <h2 className="text-2xl font-bold bg-gradient-to-r from-indigo-600 to-violet-600 bg-clip-text text-transparent inline-flex items-center gap-2">
                    <span>✨</span> Draft AI Reply
                </h2>
                <p className="text-sm text-gray-500 mt-1">
                    Describe how you want to reply, and let AI generate the draft.
                </p>
            </div>

            {isLoading ? (
                <div className="flex flex-col items-center justify-center h-64 bg-gray-50 rounded-xl border border-dashed border-gray-200">
                    <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-indigo-600 mb-4"></div>
                    <span className="text-gray-600 font-medium animate-pulse">Generating your draft...</span>
                </div>
            ) : error ? (
                <div className="bg-red-50 text-red-600 p-6 rounded-xl border border-red-100 flex items-center justify-between">
                    <span>{error}</span>
                    <button
                        onClick={generateReply}
                        className="font-medium underline hover:text-red-800"
                    >
                        Try Again
                    </button>
                </div>
            ) : (
                <div className="space-y-6">
                    <div className="relative">
                        <textarea
                            className="w-full h-64 p-6 bg-gray-50 border-0 rounded-xl focus:ring-2 focus:ring-indigo-100 text-gray-800 placeholder:text-gray-400 resize-none text-base leading-relaxed selection:bg-indigo-100"
                            value={reply}
                            onChange={(e) => setReply(e.target.value)}
                            disabled={isSending}
                            placeholder="Type your reply here..."
                        />
                        <div className="absolute bottom-4 right-4 text-xs text-gray-400">
                            AI Generated
                        </div>
                    </div>

                    <div className="flex justify-end items-center gap-3 pt-2">
                        {!inline && (
                            <button
                                onClick={onClose}
                                className="px-5 py-2.5 text-gray-600 hover:bg-gray-100 rounded-lg font-medium transition-colors"
                                disabled={isSending}
                            >
                                Cancel
                            </button>
                        )}
                        <button
                            onClick={copyToClipboard}
                            className="px-5 py-2.5 text-indigo-600 bg-indigo-50 hover:bg-indigo-100 rounded-lg font-medium transition-colors flex items-center gap-2"
                            disabled={isSending}
                        >
                            📋 Copy
                        </button>
                        <button
                            onClick={sendReply}
                            className="px-6 py-2.5 bg-gradient-to-r from-indigo-600 to-violet-600 text-white rounded-lg font-medium hover:shadow-lg hover:to-indigo-700 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 shadow-sm"
                            disabled={isSending || !reply.trim()}
                        >
                            {isSending ? (
                                <>
                                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                                    Sending...
                                </>
                            ) : (
                                <>
                                    🚀 Send Reply
                                </>
                            )}
                        </button>
                    </div>
                </div>
            )}
        </div>
    );

    if (inline) return Content;

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
            {Content}
        </div>
    );
}
