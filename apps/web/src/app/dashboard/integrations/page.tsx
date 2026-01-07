"use client";

import { useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Card } from "@/components/ui/card";
import { AlertCircle, CheckCircle2 } from "lucide-react";
import { DashboardLayout } from "@/components";
import GmailConnection from "@/components/integrations/GmailConnection";
import OutlookConnection from "@/components/integrations/OutlookConnection";
import { EmailIntegration, listIntegrations } from "@/lib/api/integrations";

export default function IntegrationsPage() {
    const router = useRouter();
    const searchParams = useSearchParams();
    const [integrations, setIntegrations] = useState<EmailIntegration[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [successMessage, setSuccessMessage] = useState<string | null>(null);
    const [authToken, setAuthToken] = useState<string>("");

    // Get auth token from localStorage or cookies (client-side only)
    useEffect(() => {
        if (typeof window !== "undefined") {
            let token = localStorage.getItem("access_token") || sessionStorage.getItem("access_token") || "";
            if (!token) {
                // try cookie fallback
                const match = document.cookie
                    .split(";")
                    .map((c) => c.trim())
                    .find((c) => c.startsWith("access_token="));
                if (match) {
                    token = decodeURIComponent(match.split("=")[1]);
                }
            }
            setAuthToken(token);
        }
    }, []);

    // Check for success message from OAuth callback
    useEffect(() => {
        const connected = searchParams.get("connected");
        if (connected === "gmail") {
            setSuccessMessage("Gmail connected successfully!");
            router.replace("/dashboard/emails");
            setTimeout(() => setSuccessMessage(null), 5000);
        } else if (connected === "outlook") {
            setSuccessMessage("Outlook connected successfully!");
            router.replace("/dashboard/emails");
            setTimeout(() => setSuccessMessage(null), 5000);
        }
    }, [searchParams, router]);

    const fetchIntegrations = async () => {
        if (!authToken) {
            setLoading(false);
            return; // Wait for token to be loaded
        }

        setLoading(true);
        setError(null);

        try {
            const response = await listIntegrations(authToken);
            setIntegrations(response.integrations);
        } catch (err: any) {
            console.error("Failed to load integrations:", err);
            setError(err.message || "Failed to load integrations");
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchIntegrations();
    }, [authToken]); // Re-fetch when token is loaded

    const gmailIntegration =
        integrations.find((i) => i.provider === "gmail") || null;
    const outlookIntegration =
        integrations.find((i) => i.provider === "outlook") || null;

    const handleGmailDisconnect = () => {
        // Refresh integrations list
        fetchIntegrations();
    };

    const handleOutlookDisconnect = () => {
        fetchIntegrations();
    };

    return (
        <DashboardLayout>
            <div className="container max-w-4xl mx-auto py-8 px-4">
                <div className="mb-8">
                    <h1 className="text-3xl font-bold text-slate-900 mb-2">
                        Email Integrations
                    </h1>
                    <p className="text-slate-600">
                        Connect your email accounts to enable automated draft generation
                        and monitoring.
                    </p>
                </div>

                {successMessage && (
                    <div className="mb-6 p-4 bg-green-50 border border-green-200 rounded-lg flex items-center gap-3">
                        <CheckCircle2 className="h-5 w-5 text-green-600" />
                        <span className="text-sm text-green-800">{successMessage}</span>
                    </div>
                )}

                {error && (
                    <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg flex items-center gap-3">
                        <AlertCircle className="h-5 w-5 text-red-600" />
                        <span className="text-sm text-red-800">{error}</span>
                    </div>
                )}

                {!authToken && !loading && (
                    <div className="mb-6 p-4 bg-yellow-50 border border-yellow-200 rounded-lg flex items-center gap-3">
                        <AlertCircle className="h-5 w-5 text-yellow-600" />
                        <span className="text-sm text-yellow-800">
                            Not authenticated. Please log in to manage integrations.
                        </span>
                    </div>
                )}

                <div className="space-y-4">
                    <GmailConnection
                        integration={gmailIntegration}
                        onDisconnect={handleGmailDisconnect}
                        token={authToken}
                    />

                    <OutlookConnection
                        integration={outlookIntegration}
                        onDisconnect={handleOutlookDisconnect}
                        token={authToken}
                    />
                </div>

                {loading && (
                    <div className="mt-8 text-center">
                        <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-sky-600 border-r-transparent"></div>
                        <p className="mt-2 text-sm text-slate-600">Loading integrations...</p>
                    </div>
                )}
            </div>
        </DashboardLayout>
    );
}
