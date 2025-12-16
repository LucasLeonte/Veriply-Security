"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Mail, ArrowLeft } from "lucide-react";

export default function ForgotPasswordPage() {
    const router = useRouter();
    const [email, setEmail] = useState("");
    const [error, setError] = useState<string | null>(null);
    const [success, setSuccess] = useState(false);
    const [loading, setLoading] = useState(false);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError(null);
        setSuccess(false);

        if (!email) {
            setError("Email is required");
            return;
        }

        if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
            setError("Please enter a valid email address");
            return;
        }

        try {
            setLoading(true);

            const apiUrl =
                process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";
            const response = await fetch(
                `${apiUrl}/api/v1/auth/forgot-password`,
                {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ email }),
                }
            );

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({
                    detail: `HTTP ${response.status}: ${response.statusText}`,
                }));
                console.error("Forgot password error:", {
                    status: response.status,
                    statusText: response.statusText,
                    error: errorData,
                });
                setError(
                    errorData.detail ||
                        "Failed to send reset email. Please check that the email exists in our system."
                );
                return;
            }

            setSuccess(true);
            setEmail("");
        } catch (err) {
            console.error("Forgot password exception:", err);
            setError(
                err instanceof Error
                    ? err.message
                    : "Failed to send reset email"
            );
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 flex flex-col items-center justify-center p-4">
            <div className="relative w-full max-w-md">
                <div className="text-center mb-8">
                    <h1 className="text-4xl font-bold text-slate-900 mb-2">
                        Reset password
                    </h1>
                    <p className="text-slate-600">
                        Enter your email to receive a password reset link
                    </p>
                </div>

                <div className="bg-white rounded-lg shadow-lg border border-slate-200 p-8 backdrop-blur-sm bg-white/90">
                    {error && (
                        <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-800 text-sm">
                            <p className="font-medium">{error}</p>
                        </div>
                    )}

                    {success && (
                        <div className="mb-4 p-4 bg-green-50 border border-green-200 rounded-lg text-green-800 text-sm">
                            <p className="font-medium">
                                Password reset link sent! Check your email for
                                instructions.
                            </p>
                        </div>
                    )}

                    <form onSubmit={handleSubmit} className="space-y-4">
                        <div>
                            <label className="block text-sm font-medium text-slate-700 mb-2">
                                Email address
                            </label>
                            <div className="relative">
                                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
                                <input
                                    type="email"
                                    value={email}
                                    onChange={(e) => setEmail(e.target.value)}
                                    className="w-full pl-10 pr-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-sky-500"
                                    placeholder="you@example.com"
                                    disabled={loading || success}
                                />
                            </div>
                        </div>

                        <button
                            type="submit"
                            disabled={loading || success}
                            className="w-full px-4 py-2 bg-sky-500 hover:bg-sky-600 disabled:bg-slate-300 text-white rounded-lg font-medium transition-colors"
                        >
                            {loading
                                ? "Sending..."
                                : success
                                ? "Email sent!"
                                : "Send reset link"}
                        </button>
                    </form>

                    <button
                        type="button"
                        onClick={() => router.push("/login")}
                        className="mt-4 w-full flex items-center justify-center gap-2 text-sky-600 hover:text-sky-700 font-medium"
                    >
                        <ArrowLeft className="w-4 h-4" />
                        Back to login
                    </button>
                </div>
            </div>
        </div>
    );
}
