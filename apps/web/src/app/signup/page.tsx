"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";

export default function SignupPage() {
    const router = useRouter();
    const [name, setName] = useState("");
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [rememberMe, setRememberMe] = useState(false);
    const [termsAccepted, setTermsAccepted] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [loading, setLoading] = useState(false);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError(null);

        if (!name.trim()) return setError("Name is required");
        if (!email) return setError("Email is required");
        if (!password || password.length < 8)
            return setError("Password must be at least 8 characters");
        if (!termsAccepted)
            return setError(
                "You must accept the Terms of Service and Privacy Policy"
            );

        setLoading(true);
        try {
            const apiUrl =
                process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";
            const res = await fetch(`${apiUrl}/api/v1/auth/register`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ email, password, tenant_name: name }),
            });

            if (!res.ok) {
                const err = await res.json().catch(() => ({}));
                setError(err.detail || "Signup failed");
                return;
            }

            const data = await res.json();
            if (data.access_token) {
                if (rememberMe) {
                    localStorage.setItem("access_token", data.access_token);
                } else {
                    sessionStorage.setItem("access_token", data.access_token);
                }
            }

            // Redirect to group selection
            router.push("/groups");
        } catch (e) {
            setError(e instanceof Error ? e.message : "Signup failed");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 flex flex-col items-center justify-center p-4">
            <div className="relative w-full max-w-md">
                <div className="text-center mb-8">
                    <h1 className="text-4xl font-bold text-slate-900 mb-2">
                        Create account
                    </h1>
                    <p className="text-slate-600">Sign up to get started</p>
                </div>

                <div className="bg-white rounded-lg shadow-lg border border-slate-200 p-8 backdrop-blur-sm bg-white/90">
                    {error && (
                        <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-800 text-sm">
                            <p className="font-medium">{error}</p>
                        </div>
                    )}

                    <form onSubmit={handleSubmit} className="space-y-4">
                        <div>
                            <label className="block text-sm font-medium text-slate-700 mb-2">
                                Full name
                            </label>
                            <input
                                value={name}
                                onChange={(e) => setName(e.target.value)}
                                className="w-full px-3 py-2 border border-slate-300 rounded-lg"
                                placeholder="Jane Doe"
                                disabled={loading}
                            />
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-slate-700 mb-2">
                                Email
                            </label>
                            <input
                                type="email"
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                className="w-full px-3 py-2 border border-slate-300 rounded-lg"
                                placeholder="you@example.com"
                                disabled={loading}
                            />
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-slate-700 mb-2">
                                Password
                            </label>
                            <input
                                type="password"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                className="w-full px-3 py-2 border border-slate-300 rounded-lg"
                                placeholder="At least 8 characters"
                                disabled={loading}
                            />
                        </div>

                        <div className="flex items-center gap-2">
                            <input
                                type="checkbox"
                                id="rememberMe"
                                checked={rememberMe}
                                onChange={(e) =>
                                    setRememberMe(e.target.checked)
                                }
                                className="w-4 h-4 text-sky-500 border-slate-300 rounded focus:ring-sky-500"
                            />
                            <label
                                htmlFor="rememberMe"
                                className="text-sm text-slate-700 select-none"
                            >
                                Keep me signed in
                            </label>
                        </div>

                        <div className="flex items-start gap-2 pt-2">
                            <input
                                type="checkbox"
                                id="termsAccepted"
                                checked={termsAccepted}
                                onChange={(e) =>
                                    setTermsAccepted(e.target.checked)
                                }
                                className="w-4 h-4 mt-1 text-sky-500 border-slate-300 rounded focus:ring-sky-500"
                            />
                            <label
                                htmlFor="termsAccepted"
                                className="text-sm text-slate-700 select-none"
                            >
                                I agree to the{" "}
                                <Link
                                    href="/terms-of-service"
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="text-sky-500 hover:underline"
                                >
                                    Terms of Service
                                </Link>{" "}
                                and{" "}
                                <Link
                                    href="/privacy-policy"
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="text-sky-500 hover:underline"
                                >
                                    Privacy Policy
                                </Link>
                            </label>
                        </div>

                        <div className="pt-4">
                            <button
                                type="submit"
                                disabled={loading}
                                className="w-full px-4 py-2 bg-sky-500 hover:bg-sky-600 text-white rounded-lg font-medium"
                            >
                                {loading ? "Creating..." : "Create account"}
                            </button>
                        </div>
                    </form>

                    <div className="mt-4 text-center text-sm">
                        <button
                            type="button"
                            onClick={() => router.push("/login")}
                            className="text-slate-600 hover:underline"
                        >
                            Already have an account? Log in
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}
