"use client";

import React from "react";
import { useRouter } from "next/navigation";
import { ChevronDown } from "lucide-react";
import { Avatar, AvatarImage, AvatarFallback } from "./ui/avatar";
import { Button } from "./ui/button";
import { cn } from "@/lib/utils";
import { MobileSidebar } from "./Sidebar";

interface HeaderProps {
    className?: string;
    userInitials?: string;
    userName?: string;
}

export function Header({
    className,
    userInitials = "JD",
    userName = "John Doe",
}: HeaderProps) {
    const router = useRouter();
    const [userMenuOpen, setUserMenuOpen] = React.useState(false);

    const handleProfile = () => {
        router.push("/profile");
        setUserMenuOpen(false);
    };

    const handleSettings = () => {
        router.push("/settings");
        setUserMenuOpen(false);
    };

    const handleSignOut = async () => {
        // Call logout endpoint to clear httpOnly cookie
        try {
            await fetch('/api/v1/auth/logout', {
                method: 'POST',
                credentials: 'include', // Include cookies
            });
        } catch (err) {
            console.error('Logout error:', err);
        }
        
        // Redirect to login (cookie is automatically cleared by browser)
        router.push("/login");
        setUserMenuOpen(false);
    };

    return (
        <header
            className={cn(
                "sticky top-0 z-40 w-full bg-white border-b border-slate-300",
                className
            )}
        >
            <div className="flex items-center justify-between h-16 px-4 md:px-6">
                {/* Mobile Menu Trigger */}
                <div className="md:hidden">
                    <MobileSidebar />
                </div>

                {/* Title Area */}
                <div className="flex-1">
                    <h1 className="text-lg md:text-xl font-semibold text-slate-950">
                        Dashboard
                    </h1>
                </div>

                {/* User Menu */}
                <div className="flex items-center gap-4">
                    <div className="relative">
                        <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => setUserMenuOpen(!userMenuOpen)}
                            className="flex items-center gap-2 text-slate-700 hover:bg-slate-100"
                        >
                            <Avatar className="h-8 w-8">
                                <AvatarImage
                                    src={`https://api.dicebear.com/7.x/avataaars/svg?seed=${userName}`}
                                />
                                <AvatarFallback className="text-xs">
                                    {userInitials}
                                </AvatarFallback>
                            </Avatar>
                            <span className="hidden sm:inline text-sm font-medium">
                                {userName}
                            </span>
                            <ChevronDown className="w-4 h-4 text-slate-400" />
                        </Button>

                        {/* User Menu Dropdown */}
                        {userMenuOpen && (
                            <div className="absolute right-0 mt-2 w-48 rounded-lg shadow-lg bg-white border border-slate-300 py-1 z-50">
                                <button onClick={handleProfile} className="w-full text-left px-4 py-2 text-sm text-slate-700 hover:bg-slate-100">
                                    Profile
                                </button>
                                <button onClick={handleSettings} className="w-full text-left px-4 py-2 text-sm text-slate-700 hover:bg-slate-100">
                                    Settings
                                </button>
                                <button onClick={handleSignOut} className="w-full text-left px-4 py-2 text-sm text-slate-700 hover:bg-slate-100 border-t border-slate-300">
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
