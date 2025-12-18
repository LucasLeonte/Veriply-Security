"use client";

import { useState } from "react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { AlertCircle, CheckCircle2, Loader2, XCircle } from "lucide-react";
import { EmailIntegration, getGmailAuthUrl, disconnectIntegration } from "@/lib/api/integrations";

interface GmailConnectionProps {
    integration: EmailIntegration | null;
    onDisconnect: () => void;
    token: string;
}

export default function GmailConnection({
    integration,
    onDisconnect,
    token,
}: GmailConnectionProps) {
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const handleConnect = () => {
        // Redirect to OAuth flow
        window.location.href = getGmailAuthUrl();
    };

    const handleDisconnect = async () => {
        if (!integration) return;

        const confirmed = window.confirm(
            "Are you sure you want to disconnect your Gmail account? This will stop automated email monitoring."
        );

        if (!confirmed) return;

        setLoading(true);
        setError(null);

        try {
            await disconnectIntegration(integration.id, token);
            onDisconnect();
        } catch (err: any) {
            setError(err.message || "Failed to disconnect Gmail");
        } finally {
            setLoading(false);
        }
    };

    const isConnected = integration && integration.status === "connected";

    return (
        <Card className="p-6">
            <div className="flex items-start justify-between">
                <div className="flex items-center gap-4">
                    <div className="h-12 w-12 rounded-lg bg-red-100 flex items-center justify-center">
                        <svg
                            className="h-6 w-6 text-red-600"
                            fill="currentColor"
                            viewBox="0 0 24 24"
                        >
                            <path d="M20 4H4c-1.1 0-1.99.9-1.99 2L2 18c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm0 4l-8 5-8-5V6l8 5 8-5v2z" />
                        </svg>
                    </div>
                    <div>
                        <h3 className="text-lg font-semibold text-slate-900">Gmail</h3>
                        <p className="text-sm text-slate-600">
                            {isConnected
                                ? "Connected and monitoring emails"
                                : "Not connected"}
                        </p>
                        {integration?.last_sync_time && (
                            <p className="text-xs text-slate-500 mt-1">
                                Last sync:{" "}
                                {new Date(integration.last_sync_time).toLocaleString()}
                            </p>
                        )}
                    </div>
                </div>

                <div className="flex items-center gap-2">
                    {isConnected ? (
                        <>
                            <CheckCircle2 className="h-5 w-5 text-green-600" />
                            <Button
                                variant="outline"
                                size="sm"
                                onClick={handleDisconnect}
                                disabled={loading}
                            >
                                {loading ? (
                                    <Loader2 className="h-4 w-4 animate-spin" />
                                ) : (
                                    "Disconnect"
                                )}
                            </Button>
                        </>
                    ) : (
                        <>
                            <XCircle className="h-5 w-5 text-slate-400" />
                            <Button size="sm" onClick={handleConnect}>
                                Connect Gmail
                            </Button>
                        </>
                    )}
                </div>
            </div>

            {error && (
                <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg flex items-center gap-2">
                    <AlertCircle className="h-4 w-4 text-red-600" />
                    <span className="text-sm text-red-800">{error}</span>
                </div>
            )}

            {isConnected && (
                <div className="mt-4 pt-4 border-t border-slate-200">
                    <p className="text-xs text-slate-600">
                        <strong>Permissions granted:</strong> Read emails, create drafts,
                        modify messages
                    </p>
                </div>
            )}
        </Card>
    );
}
