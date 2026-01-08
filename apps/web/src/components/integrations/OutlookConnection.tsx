"use client";

import { useState } from "react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { AlertCircle, CheckCircle2, Loader2, XCircle } from "lucide-react";
import { EmailIntegration, getOutlookAuthUrl, disconnectIntegration, setDefaultReplyBot } from "@/lib/api/integrations";
import { Bot } from "@/types/bot";

interface OutlookConnectionProps {
    integration: EmailIntegration | null;
    onDisconnect: () => void;
    token: string;
    bots: Bot[];
    onUpdated?: () => void;
}

export default function OutlookConnection({
    integration,
    onDisconnect,
    token,
    bots,
    onUpdated,
}: OutlookConnectionProps) {
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [savingBot, setSavingBot] = useState(false);

    const handleConnect = () => {
        if (!token) {
            setError("You need to be logged in before connecting Outlook.");
            return;
        }
        // Redirect to OAuth flow with token so backend can resolve tenant/user
        window.location.href = getOutlookAuthUrl(token);
    };

    const handleDisconnect = async () => {
        if (!integration) return;

        const confirmed = window.confirm(
            "Are you sure you want to disconnect your Outlook account? This will stop automated email monitoring."
        );

        if (!confirmed) return;

        setLoading(true);
        setError(null);

        try {
            await disconnectIntegration(integration.id, token);
            onDisconnect();
        } catch (err: any) {
            setError(err.message || "Failed to disconnect Outlook");
        } finally {
            setLoading(false);
        }
    };

    const isConnected = integration && integration.status === "connected";

    const handleSetDefaultBot = async (botId: string | null) => {
        if (!integration) return;
        try {
            setSavingBot(true);
            await setDefaultReplyBot(token, integration.id, botId);
            onUpdated?.();
        } catch (e: any) {
            setError(e?.message || "Failed to set default bot");
        } finally {
            setSavingBot(false);
        }
    };

    return (
        <Card className="p-6">
            <div className="flex items-start justify-between">
                <div className="flex items-center gap-4">
                    <div className="h-12 w-12 rounded-lg bg-blue-100 flex items-center justify-center">
                        <svg
                            className="h-6 w-6 text-blue-600"
                            fill="currentColor"
                            viewBox="0 0 24 24"
                        >
                            <path d="M7 2v20l15-10L7 2z" />
                        </svg>
                    </div>
                    <div>
                        <h3 className="text-lg font-semibold text-slate-900">Outlook</h3>
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
                                Connect Outlook
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
                    <div className="flex flex-col gap-3">
                        <div>
                            <label className="block text-sm font-medium text-slate-700 mb-1">Default reply bot</label>
                            <div className="flex items-center gap-2">
                                <select
                                    className="w-full max-w-xs border rounded px-3 py-2"
                                    value={integration?.default_reply_bot_id || ""}
                                    onChange={(e) => handleSetDefaultBot(e.target.value || null)}
                                    disabled={savingBot}
                                >
                                    <option value="">— None (no KB fallback) —</option>
                                    {bots.map((b) => (
                                        <option key={b.id} value={b.id}>{b.name}</option>
                                    ))}
                                </select>
                                {savingBot && <Loader2 className="h-4 w-4 animate-spin text-slate-500" />}
                            </div>
                            <p className="text-xs text-slate-500 mt-1">Used when no monitoring rule matches.</p>
                        </div>

                        <p className="text-xs text-slate-600">
                            <strong>Permissions granted:</strong> Read emails, send emails
                        </p>
                    </div>
                </div>
            )}
        </Card>
    );
}
