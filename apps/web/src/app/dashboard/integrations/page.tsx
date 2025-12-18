"use client";

import { useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Card } from "@/components/ui/card";
import { AlertCircle, CheckCircle2 } from "lucide-react";
import GmailConnection from "@/components/integrations/GmailConnection";
import { EmailIntegration, listIntegrations } from "@/lib/api/integrations";

export default function IntegrationsPage() {
    const router = useRouter();
    const searchParams = useSearchParams();
    const [integrations, setIntegrations] = useState<EmailIntegration[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [successMessage, setSuccessMessage] = useState<string | null>(null);
    const [authToken, setAuthToken] = useState<string>("");

    // Get auth token from localStorage (client-side only)
    useEffect(() => {
        if (typeof window !== "undefined") {
            setAuthToken(localStorage.getItem("access_token") || "");
        }
    }, []);

    // Check for success message from OAuth callback
    useEffect(() => {
        const connected = searchParams.get("connected");
        if (connected === "gmail") {
            setSuccessMessage("Gmail connected successfully!");
            // Clear query param
            router.replace("/dashboard/integrations");
            // Auto-dismiss success message
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

    const handleGmailDisconnect = () => {
        // Refresh integrations list
        fetchIntegrations();
    };

    return (
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

                {/* Placeholder for Outlook integration (Story 6.2) */}
                <Card className="p-6 opacity-50">
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
                                <h3 className="text-lg font-semibold text-slate-900">
                                    Outlook
                                </h3>
                                <p className="text-sm text-slate-600">
                                    Coming soon in Story 6.2
                                </p>
                            </div>
                        </div>
                    </div>
                </Card>
            </div>

            {loading && (
                <div className="mt-8 text-center">
                    <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-sky-600 border-r-transparent"></div>
                    <p className="mt-2 text-sm text-slate-600">Loading integrations...</p>
                </div>
            )}
        </div>
    );
}
