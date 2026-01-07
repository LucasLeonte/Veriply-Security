"use client";

import { useState, useEffect } from "react";
import { DashboardLayout } from "@/components";
import { EmailList } from "@/components/emails/EmailList";
import { getAccessToken } from "@/lib/auth";

// import { useAuth } from "@/lib/auth"; // Unused


export default function EmailsPage() {
    const [activeTab, setActiveTab] = useState<"INBOX" | "SENT">("INBOX");
    // We need the token. Assuming it's in localStorage or context. 
    // For MVP/Hackathon speed, let's grab it from localStorage if not cleanly available via hook
    // Or better, check how other pages do it. `inbox/page.tsx` didn't show explicit token usage 
    // because `useHITLQueue` likely handles it. 

    // Let's implement a safe token retrieval.
    const [token, setToken] = useState<string | null>(null);

    useEffect(() => {
        const storedToken = getAccessToken();
        if (storedToken) {
            setToken(storedToken);
        }
    }, []);

    return (
        <DashboardLayout>
            <div className="space-y-6">
                <div className="flex justify-between items-center">
                    <div>
                        <h1 className="text-2xl font-bold text-gray-900">Email Hub</h1>
                        <p className="text-gray-500">View emails, save to Knowledge Base, and draft replies with AI.</p>
                    </div>
                </div>

                <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
                    <div className="border-b border-gray-200">
                        <nav className="-mb-px flex">
                            <button
                                onClick={() => setActiveTab("INBOX")}
                                className={`whitespace-nowrap py-4 px-6 border-b-2 font-medium text-sm transition-colors ${activeTab === "INBOX"
                                    ? "border-indigo-500 text-indigo-600"
                                    : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
                                    }`}
                            >
                                Inbox
                            </button>
                            <button
                                onClick={() => setActiveTab("SENT")}
                                className={`whitespace-nowrap py-4 px-6 border-b-2 font-medium text-sm transition-colors ${activeTab === "SENT"
                                    ? "border-indigo-500 text-indigo-600"
                                    : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
                                    }`}
                            >
                                Sent
                            </button>
                        </nav>
                    </div>

                    <div className="p-6">
                        {token ? (
                            <EmailList token={token} folder={activeTab} />
                        ) : (
                            <div className="text-center py-10 text-gray-500">
                                Loading authentication...
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </DashboardLayout>
    );
}
