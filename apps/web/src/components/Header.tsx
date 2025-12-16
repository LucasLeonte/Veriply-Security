"use client";

import React from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { ChevronDown } from "lucide-react";
import { Avatar, AvatarImage, AvatarFallback } from "./ui/avatar";
import { Button } from "./ui/button";
import { cn } from "@/lib/utils";
import { MobileSidebar } from "./Sidebar";

interface HeaderProps {
    className?: string;
}

export function Header({ className }: HeaderProps) {
    const router = useRouter();
    const pathname = usePathname();
    const [userMenuOpen, setUserMenuOpen] = React.useState(false);
    const [displayName, setDisplayName] = React.useState<string>("");
    const [initials, setInitials] = React.useState<string>("--");
    const [avatarUrl, setAvatarUrl] = React.useState<string | undefined>(
        undefined
    );

    const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

    const deriveInitials = (input?: string) => {
        if (!input) return "";
        const parts = input.trim().split(/\s+/);
        if (parts.length === 1) {
            return parts[0].slice(0, 2).toUpperCase();
        }
        return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
    };

    React.useEffect(() => {
        let active = true;
        const loadProfile = async () => {
            try {
                const token =
                    typeof window !== "undefined"
                        ? localStorage.getItem("access_token")
                        : null;
                if (!token) {
                    // no token, show generic display
                    return;
                }

                const response = await fetch(`${apiUrl}/api/v1/profile/me`, {
                    method: "GET",
                    headers: {
                        Authorization: `Bearer ${token}`,
                    },
                });

                if (!response.ok) {
                    // keep existing display if fetch fails
                    return;
                }

                const data = await response.json();
                if (!active) return;

                const nameFromProfile = data?.name || data?.email || "";
                setDisplayName(nameFromProfile);
                setInitials(deriveInitials(nameFromProfile) || "--");
                if (data?.avatar_url) {
                    setAvatarUrl(data.avatar_url as string);
                }
            } catch (err) {
                console.error("Failed to load profile for header:", err);
                // leave fallbacks as-is
            }
        };

        loadProfile();
        return () => {
            active = false;
        };
    }, [apiUrl]);

    const handleProfile = () => {
        router.push("/profile");
        setUserMenuOpen(false);
    };

    const handleSettings = () => {
        router.push("/settings");
        setUserMenuOpen(false);
    };

    const handleSignOut = async () => {
        // Clear client storage token so subsequent calls fail fast
        if (typeof window !== "undefined") {
            localStorage.removeItem("access_token");
        }

        // Call logout endpoint to clear any httpOnly cookies (best-effort)
        try {
            await fetch("/api/v1/auth/logout", {
                method: "POST",
                credentials: "include", // Include cookies
            });
        } catch (err) {
            console.error("Logout error:", err);
        }

        // Redirect to login (cookie is automatically cleared by browser)
        router.push("/login");
        setUserMenuOpen(false);
    };

    const tabs = [
        { href: "/inbox", label: "HITL Dashboard" },
        { href: "/dashboard", label: "Chat Widget" },
        { href: "/analytics", label: "Analytics" },
    ];

    return (
        <header
            className={cn(
                "sticky top-0 z-40 w-full bg-white border-b border-slate-200",
                className
            )}
        >
            <div className="flex items-center justify-between h-14 px-4 md:px-6">
                {/* Mobile Menu Trigger */}
                <div className="md:hidden">
                    <MobileSidebar />
                </div>

                {/* Brand */}
                <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-lg bg-sky-500 flex items-center justify-center">
                        <span className="text-white text-sm font-bold">V</span>
                    </div>
                    <span className="font-semibold text-slate-900">
                        Veriply
                    </span>
                    <span className="text-slate-300">|</span>
                    <span className="text-sm text-slate-500">
                        Design Direction: Cool Slate
                    </span>
                </div>

                {/* Tabs + User */}
                <div className="flex items-center gap-4">
                    <div className="hidden md:flex items-center gap-1">
                        {tabs.map((tab) => {
                            const active = pathname === tab.href;
                            return (
                                <Link
                                    key={tab.href}
                                    href={tab.href}
                                    className={cn(
                                        "px-4 py-2 text-sm font-medium rounded-lg transition-colors",
                                        active
                                            ? "bg-sky-50 text-sky-700"
                                            : "text-slate-600 hover:bg-slate-50"
                                    )}
                                >
                                    {tab.label}
                                </Link>
                            );
                        })}
                    </div>

                    <div className="relative">
                        <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => setUserMenuOpen(!userMenuOpen)}
                            className="flex items-center gap-2 text-slate-700 hover:bg-slate-100"
                        >
                            <Avatar className="h-8 w-8">
                                <AvatarImage
                                    src={
                                        avatarUrl ||
                                        `https://api.dicebear.com/7.x/avataaars/svg?seed=${encodeURIComponent(
                                            displayName || "user"
                                        )}`
                                    }
                                />
                                <AvatarFallback className="text-xs">
                                    {initials || "?"}
                                </AvatarFallback>
                            </Avatar>
                            <span className="hidden sm:inline text-sm font-medium">
                                {displayName || ""}
                            </span>
                            <ChevronDown className="w-4 h-4 text-slate-400" />
                        </Button>

                        {/* User Menu Dropdown */}
                        {userMenuOpen && (
                            <div className="absolute right-0 mt-2 w-48 rounded-lg shadow-lg bg-white border border-slate-200 py-1 z-50">
                                <button
                                    onClick={handleProfile}
                                    className="w-full text-left px-4 py-2 text-sm text-slate-700 hover:bg-slate-50"
                                >
                                    Profile
                                </button>
                                <button
                                    onClick={handleSettings}
                                    className="w-full text-left px-4 py-2 text-sm text-slate-700 hover:bg-slate-50"
                                >
                                    Settings
                                </button>
                                <button
                                    onClick={handleSignOut}
                                    className="w-full text-left px-4 py-2 text-sm text-slate-700 hover:bg-slate-50 border-t border-slate-100"
                                >
                                    Sign out
                                </button>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </header>
    );
}
