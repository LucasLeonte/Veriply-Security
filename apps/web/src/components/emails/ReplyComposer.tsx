"use client";

import { useEffect, useState } from "react";
import { generateGmailReply } from "@/lib/api/integrations";

interface ReplyComposerProps {
    isOpen: boolean;
    onClose: () => void;
    token: string;
    messageId: string;
    originalText: string;
}

export function ReplyComposer({
    isOpen,
    onClose,
    token,
    messageId,
    originalText,
}: ReplyComposerProps) {
    const [reply, setReply] = useState<string>("");
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        if (isOpen && messageId) {
            generateReply();
        }
    }, [isOpen, messageId]);

    const generateReply = async () => {
        setIsLoading(true);
        setError(null);
        try {
            const result = await generateGmailReply(token, messageId, originalText);
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

    if (!isOpen) return null;

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
                        />
                        <div className="flex justify-end space-x-3">
                            <button
                                onClick={onClose}
                                className="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-md"
                            >
                                Close
                            </button>
                            <button
                                onClick={copyToClipboard}
                                className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700"
                            >
                                Copy to Clipboard
                            </button>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}
