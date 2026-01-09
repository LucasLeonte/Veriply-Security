// ... imports
import { useState, useEffect } from "react";
import { formatDistanceToNow } from "date-fns";
import { GmailMessage, listGmailMessages, importGmailMessage } from "@/lib/api/integrations";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { cn } from "@/lib/utils";
import { Loader2, AlertCircle, MailIcon } from "lucide-react";
import { Button } from "@/components/ui/button";

interface EmailListProps {
    token: string;
    folder: "INBOX" | "SENT";
    selectedId?: string | null;
    onSelect?: (message: GmailMessage) => void;
    provider?: string;
}

export function EmailList({ token, folder, selectedId, onSelect, provider }: EmailListProps) {
    const [messages, setMessages] = useState<GmailMessage[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        if (provider === 'gmail') {
            loadMessages();
        }
    }, [folder, token, provider]);

    const loadMessages = async () => {
        setIsLoading(true);
        setError(null);
        try {
            const data = await listGmailMessages(token, folder);
            setMessages(data.messages);
        } catch (e) {
            console.error("Error loading emails:", e);
            const msg = e instanceof Error ? e.message : "Failed to load emails.";
            setError(msg);
        } finally {
            setIsLoading(false);
        }
    };

    if (provider !== 'gmail' && provider !== 'GMAIL') {
        return (
            <div className="p-12 text-center text-gray-500">
                <p>Only Gmail is currently supported in this view.</p>
                <p className="text-sm mt-2">Selected provider: {provider || 'Unknown'}</p>
            </div>
        );
    }

    if (isLoading) {
        return (
            <div className="flex justify-center p-12">
                <Loader2 className="animate-spin h-6 w-6 text-indigo-600" />
            </div>
        );
    }

    if (error) {
        if (error.includes("integration not found")) {
            return (
                <div className="h-full flex flex-col items-center justify-center p-8 text-center space-y-4">
                    <div className="bg-indigo-50 p-4 rounded-full">
                        <MailIcon className="h-8 w-8 text-indigo-600" />
                    </div>
                    <h3 className="text-lg font-semibold text-gray-900">Connect your Email</h3>
                    <p className="text-sm text-gray-500 max-w-xs">
                        Connect your Gmail account to start managing your emails with AI assistance.
                    </p>
                    <Button onClick={() => window.location.href = '/dashboard/integrations'}>
                        Connect Gmail
                    </Button>
                </div>
            );
        }

        return (
            <div className="h-full flex flex-col items-center justify-center p-8 text-center space-y-4">
                <AlertCircle className="h-8 w-8 text-red-500" />
                <p className="text-gray-900 font-medium">Failed to load emails</p>
                <p className="text-sm text-gray-500">{error}</p>
                <Button variant="outline" onClick={() => loadMessages()}>
                    Retry
                </Button>
            </div>
        );
    }



    if (messages.length === 0) {
        return (
            <div className="text-center p-12 text-gray-500 bg-gray-50/50">
                No emails found.
            </div>
        );
    }

    return (
        <div className="divide-y divide-gray-100">
            {messages.map((msg) => (
                <div
                    key={msg.id}
                    onClick={() => onSelect?.(msg)}
                    className={cn(
                        "group flex flex-col gap-1 p-4 cursor-pointer transition-colors hover:bg-gray-50/80 border-l-[3px] border-transparent",
                        selectedId === msg.id ? "bg-indigo-50/50 border-indigo-600" : ""
                    )}
                >
                    <div className="flex items-center justify-between mb-1">
                        <div className="flex items-center gap-2 overflow-hidden">
                            <Avatar className="h-6 w-6 shrink-0">
                                <AvatarFallback className="text-[10px] bg-indigo-100 text-indigo-700 font-medium">
                                    {(folder === "INBOX" ? msg.from : msg.to)?.charAt(0).toUpperCase() || "?"}
                                </AvatarFallback>
                            </Avatar>
                            <span className={cn(
                                "text-sm truncate",
                                // Simple logic: if unread (not available in API yet), bold. 
                                // For now just make everything regular unless selected
                                selectedId === msg.id ? "font-semibold text-gray-900" : "font-medium text-gray-700"
                            )}>
                                {folder === "INBOX" ? msg.from : `To: ${msg.to}`}
                            </span>
                        </div>
                        <span className="text-xs text-gray-400 shrink-0 tabular-nums">
                            {msg.date ? formatDistanceToNow(new Date(msg.date), { addSuffix: true }) : ""}
                        </span>
                    </div>

                    <h4 className={cn(
                        "text-sm text-gray-900 truncate pr-4",
                        selectedId === msg.id ? "font-medium" : "font-normal"
                    )}>
                        {msg.subject || "(No Subject)"}
                    </h4>

                    <p className="text-xs text-gray-500 line-clamp-2 leading-relaxed">
                        {msg.snippet}
                    </p>
                </div>
            ))}
        </div>
    );
}
