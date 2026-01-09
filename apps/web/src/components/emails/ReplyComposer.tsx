"use client";

import { useEffect, useState } from "react";
import { generateGmailReply, sendGmailReply } from "@/lib/api/integrations";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Loader2, Sparkles, Copy, Send, X, RotateCw } from "lucide-react";

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
            <Card className="border-green-200 bg-green-50">
                <CardContent className="pt-6">
                    <div className="flex flex-col items-center text-center">
                        <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center mb-3">
                            <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                            </svg>
                        </div>
                        <h3 className="text-lg font-semibold text-gray-900 mb-1">Reply Sent!</h3>
                        <p className="text-sm text-gray-600">Your email has been sent successfully.</p>
                    </div>
                </CardContent>
            </Card>
        );

        if (inline) return SuccessContent;

        return (
            <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
                <div className="w-full max-w-md">
                    {SuccessContent}
                </div>
            </div>
        );
    }

    const Content = (
        <Card className={inline ? 'border-0 shadow-none' : ''}>
            <CardHeader>
                <div className="flex items-start justify-between">
                    <div className="flex-1">
                        <CardTitle className="flex items-center gap-2 text-xl">
                            <Sparkles className="h-5 w-5 text-primary" />
                            Draft AI Reply
                        </CardTitle>
                        <CardDescription className="mt-1">
                            AI-generated email response based on the conversation
                        </CardDescription>
                    </div>
                    {!inline && (
                        <Button
                            variant="ghost"
                            size="icon"
                            onClick={onClose}
                            className="h-8 w-8"
                        >
                            <X className="h-4 w-4" />
                        </Button>
                    )}
                </div>
            </CardHeader>

            <CardContent className="space-y-4">
                {isLoading ? (
                    <div className="flex flex-col items-center justify-center py-16 px-4 border border-dashed border-gray-300 rounded-lg bg-gray-50">
                        <Loader2 className="h-8 w-8 animate-spin text-primary mb-3" />
                        <p className="text-sm text-muted-foreground">Generating your draft...</p>
                    </div>
                ) : error ? (
                    <div className="bg-destructive/10 text-destructive p-4 rounded-lg border border-destructive/20 flex items-center justify-between gap-3">
                        <p className="text-sm flex-1">{error}</p>
                        <Button
                            variant="outline"
                            size="sm"
                            onClick={generateReply}
                        >
                            <RotateCw className="h-4 w-4 mr-1" />
                            Retry
                        </Button>
                    </div>
                ) : (
                    <>
                        <div className="relative">
                            <textarea
                                className="w-full min-h-[256px] p-4 border border-input rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-0 resize-none text-sm leading-relaxed disabled:opacity-50 disabled:cursor-not-allowed"
                                value={reply}
                                onChange={(e) => setReply(e.target.value)}
                                disabled={isSending}
                                placeholder="Your AI-generated reply will appear here..."
                            />
                            <div className="absolute bottom-3 right-3">
                                <span className="inline-flex items-center gap-1 text-xs text-muted-foreground bg-background/80 px-2 py-1 rounded">
                                    <Sparkles className="h-3 w-3" />
                                    AI Generated
                                </span>
                            </div>
                        </div>

                        <div className="flex justify-end items-center gap-2 pt-2">
                            {!inline && (
                                <Button
                                    variant="outline"
                                    onClick={onClose}
                                    disabled={isSending}
                                >
                                    Cancel
                                </Button>
                            )}
                            <Button
                                variant="outline"
                                onClick={copyToClipboard}
                                disabled={isSending}
                            >
                                <Copy className="h-4 w-4 mr-2" />
                                Copy
                            </Button>
                            <Button
                                onClick={sendReply}
                                disabled={isSending || !reply.trim()}
                            >
                                {isSending ? (
                                    <>
                                        <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                                        Sending...
                                    </>
                                ) : (
                                    <>
                                        <Send className="h-4 w-4 mr-2" />
                                        Send Reply
                                    </>
                                )}
                            </Button>
                        </div>
                    </>
                )}
            </CardContent>
        </Card>
    );

    if (inline) return Content;

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
            <div className="w-full max-w-2xl max-h-[90vh] overflow-y-auto">
                {Content}
            </div>
        </div>
    );
}
