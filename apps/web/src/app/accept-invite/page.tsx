"use client";

import { useState, useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";

export default function AcceptInvitePage() {
    const router = useRouter();
    const searchParams = useSearchParams();
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [success, setSuccess] = useState(false);
    const token = searchParams.get("token");
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

    useEffect(() => {
        const acceptInvite = async () => {
            try {
                setLoading(true);
                setError(null);

                if (!token) {
                    setError("No invitation token provided");
                    return;
                }

                const response = await fetch(
                    `${apiUrl}/api/v1/auth/accept-invite`,
                    {
                        method: "POST",
                        headers: {
                            "Content-Type": "application/json",
                        },
                        body: JSON.stringify({ token }),
                    }
                );

                if (!response.ok) {
                    const errorData = await response.json();
                    setError(
                        errorData.detail ||
                            "Failed to accept invitation. The link may have expired."
                    );
                    return;
                }

                setSuccess(true);
                setTimeout(() => {
                    router.push("/login");
                }, 2000);
            } catch (err) {
                setError(
                    err instanceof Error ? err.message : "An error occurred"
                );
            } finally {
                setLoading(false);
            }
        };

        acceptInvite();
    }, [token, apiUrl, router]);

    return (
        <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100 p-4">
            <div className="bg-white rounded-lg shadow-xl p-8 w-full max-w-md">
                <h1 className="text-2xl font-bold text-center mb-6 text-slate-900">
                    Team Invitation
                </h1>

                {loading && (
                    <div className="text-center">
                        <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mb-4"></div>
                        <p className="text-slate-600">
                            Accepting invitation...
                        </p>
                    </div>
                )}

                {error && (
                    <div>
                        <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-800">
                            {error}
                        </div>
                        <button
                            onClick={() => router.push("/login")}
                            className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition font-medium"
                        >
                            Go to Login
                        </button>
                    </div>
                )}

                {success && (
                    <div>
                        <div className="mb-4 p-4 bg-green-50 border border-green-200 rounded-lg text-green-800 text-center">
                            <p className="font-semibold">
                                Invitation accepted!
                            </p>
                            <p className="text-sm">Redirecting to login...</p>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}
