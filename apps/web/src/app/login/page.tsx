"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Mail, Lock, Eye, EyeOff } from "lucide-react";

export default function LoginPage() {
    const router = useRouter();
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [showPassword, setShowPassword] = useState(false);
    const [rememberMe, setRememberMe] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [loading, setLoading] = useState(false);
    const [success, setSuccess] = useState(false);

    // Check for session expired error
    useEffect(() => {
        try {
            const errorParam = new URLSearchParams(
                typeof window !== "undefined" ? window.location.search : ""
            ).get("error");
            if (errorParam === "session_expired") {
                setError("Your session has expired. Please log in again.");
            }
        } catch {
            // ignore parsing issues in non-browser environments (tests)
        }
    }, []);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError(null);
        setSuccess(false);

        // Validate inputs
        if (!email) {
            setError("Email is required");
            return;
        }

        if (!password) {
            setError("Password is required");
            return;
        }

        if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
            setError("Please enter a valid email address");
            return;
        }

        if (password.length < 8) {
            setError("Password must be at least 8 characters");
            return;
        }

        try {
            setLoading(true);

            // Call login API endpoint first
            const apiUrl =
                process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";
            const response = await fetch(`${apiUrl}/api/v1/auth/login`, {
                method: "POST",
                credentials: "include", // Required for cookies to be set/sent
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({
                    email,
                    password,
                    tenant_name: email.split("@")[0], // Not used for login, but included for schema compatibility
                }),
            });

            if (!response.ok) {
                const errorData = await response.json();
                setError(errorData.detail || "Login failed");
                return;
            }

            // Extract token from response and store based on rememberMe
            const data = await response.json();

            if (data.access_token) {
                if (rememberMe) {
                    localStorage.setItem("access_token", data.access_token);
                } else {
                    sessionStorage.setItem("access_token", data.access_token);
                }
            } else {
                setError("Login failed: no access token returned");
            }

            setSuccess(true);

            // Redirect to group selection page after brief delay
            setTimeout(() => {
                router.push("/groups");
            }, 500);
        } catch (err) {
            setError(err instanceof Error ? err.message : "Login failed");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 flex flex-col items-center justify-center p-4">
            {/* Background decoration */}
            <div className="absolute inset-0 overflow-hidden pointer-events-none">
                <div className="absolute -top-40 -right-40 w-80 h-80 bg-sky-200 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-blob"></div>
                <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-blue-200 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-blob animation-delay-2000"></div>
                <div className="absolute top-1/2 left-1/2 w-80 h-80 bg-slate-200 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-blob animation-delay-4000"></div>
            </div>

            {/* Login Card */}
            <div className="relative w-full max-w-md">
                {/* Header */}
                <div className="text-center mb-8">
                    <h1 className="text-4xl font-bold text-slate-900 mb-2">
                        Veriply
                    </h1>
                    <p className="text-slate-600">Log in to your account</p>
                    <div className="mt-2 text-sm">
                        <span className="text-slate-500">
                            Don&apos;t have an account?
                        </span>
                        <button
                            type="button"
                            onClick={() => router.push("/signup")}
                            className="text-sky-600 hover:underline ml-1"
                        >
                            Create account
                        </button>
                    </div>
                </div>

                {/* Form Card */}
                <div className="bg-white rounded-lg shadow-lg border border-slate-200 p-8 backdrop-blur-sm bg-white/90">
                    {/* Error Message */}
                    {error && (
                        <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-800 text-sm">
                            <p className="font-medium">{error}</p>
                        </div>
                    )}

                    {/* Success Message */}
                    {success && (
                        <div className="mb-4 p-4 bg-green-50 border border-green-200 rounded-lg text-green-800 text-sm">
                            <p className="font-medium">
                                Login successful! Redirecting...
                            </p>
                        </div>
                    )}

                    {/* Login Form */}
                    <form onSubmit={handleSubmit} className="space-y-4">
                        {/* Email Field */}
                        <div>
                            <label
                                htmlFor="email"
                                className="block text-sm font-medium text-slate-700 mb-2"
                            >
                                Email Address
                            </label>
                            <div className="relative">
                                <Mail className="absolute left-3 top-3 w-5 h-5 text-slate-400" />
                                <input
                                    type="email"
                                    id="email"
                                    value={email}
                                    onChange={(e) => setEmail(e.target.value)}
                                    placeholder="you@example.com"
                                    disabled={loading}
                                    className="w-full pl-10 pr-4 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-sky-500 focus:border-transparent bg-slate-50 transition disabled:opacity-50 disabled:cursor-not-allowed"
                                />
                            </div>
                        </div>

                        {/* Password Field */}
                        <div>
                            <label
                                htmlFor="password"
                                className="block text-sm font-medium text-slate-700 mb-2"
                            >
                                Password
                            </label>
                            <div className="relative">
                                <Lock className="absolute left-3 top-3 w-5 h-5 text-slate-400" />
                                <input
                                    type={showPassword ? "text" : "password"}
                                    id="password"
                                    value={password}
                                    onChange={(e) =>
                                        setPassword(e.target.value)
                                    }
                                    placeholder="••••••••"
                                    disabled={loading}
                                    className="w-full pl-10 pr-10 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-sky-500 focus:border-transparent bg-slate-50 transition disabled:opacity-50 disabled:cursor-not-allowed"
                                />
                                <button
                                    type="button"
                                    onClick={() =>
                                        setShowPassword(!showPassword)
                                    }
                                    disabled={loading}
                                    className="absolute right-3 top-3 text-slate-400 hover:text-slate-600 transition disabled:opacity-50"
                                >
                                    {showPassword ? (
                                        <EyeOff className="w-5 h-5" />
                                    ) : (
                                        <Eye className="w-5 h-5" />
                                    )}
                                </button>
                            </div>
                        </div>

                        {/* Remember Me & Forgot Password */}
                        <div className="flex items-center justify-between text-sm">
                            <label className="flex items-center gap-2">
                                <input
                                    type="checkbox"
                                    checked={rememberMe}
                                    onChange={(e) =>
                                        setRememberMe(e.target.checked)
                                    }
                                    className="w-4 h-4 rounded border-slate-300 text-sky-600 focus:ring-sky-500"
                                    disabled={loading}
                                />
                                <span className="text-slate-700">
                                    Remember me
                                </span>
                            </label>
                            <button
                                type="button"
                                onClick={() => router.push("/forgot-password")}
                                className="text-sky-600 hover:text-sky-700 font-medium"
                            >
                                Forgot password?
                            </button>
                        </div>

                        {/* Submit Button */}
                        <button
                            type="submit"
                            disabled={loading}
                            className="w-full bg-gradient-to-r from-sky-500 to-sky-600 hover:from-sky-600 hover:to-sky-700 text-white font-medium py-2 px-4 rounded-lg transition duration-200 disabled:opacity-50 disabled:cursor-not-allowed mt-6 shadow-md hover:shadow-lg"
                        >
                            {loading ? "Logging in..." : "Log in"}
                        </button>
                    </form>
                </div>
            </div>

            <style jsx>{`
                @keyframes blob {
                    0%,
                    100% {
                        transform: translate(0, 0) scale(1);
                    }
                    33% {
                        transform: translate(30px, -50px) scale(1.1);
                    }
                    66% {
                        transform: translate(-20px, 20px) scale(0.9);
                    }
                }

                .animate-blob {
                    animation: blob 7s infinite;
                }

                .animation-delay-2000 {
                    animation-delay: 2s;
                }

                .animation-delay-4000 {
                    animation-delay: 4s;
                }
            `}</style>
        </div>
    );
}
