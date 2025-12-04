"use client";

import React, { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
    LayoutDashboard,
    Bot,
    Inbox,
    BookOpen,
    Settings,
    Menu,
    X,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "./ui/button";
import {
    Sheet,
    SheetContent,
    SheetTrigger,
    SheetTitle,
    SheetHeader,
} from "./ui/sheet";

const NAVIGATION_ITEMS = [
    { href: "/dashboard", icon: LayoutDashboard, label: "Dashboard" },
    { href: "/dashboard/bots", icon: Bot, label: "Bots" },
    { href: "/inbox", icon: Inbox, label: "Inbox" },
    { href: "/knowledge-base", icon: BookOpen, label: "Knowledge Base" },
    { href: "/settings", icon: Settings, label: "Settings" },
];

interface SidebarProps {
    className?: string;
}

export function Sidebar({ className }: SidebarProps) {
    const pathname = usePathname();

    const navItems = NAVIGATION_ITEMS.map((item) => ({
        ...item,
        isActive:
            pathname === item.href ||
            (pathname.startsWith(item.href + "/") &&
                item.href !== "/dashboard"),
    }));

    return (
        <nav
            className={cn(
                "hidden md:flex flex-col w-64 bg-slate-950 border-r border-slate-700 h-screen fixed left-0 top-0 pt-4 px-4",
                className
            )}
        >
            {/* Logo */}
            <div className="mb-8 flex items-center gap-2 px-2">
                <div className="w-8 h-8 rounded-lg bg-emerald-600 flex items-center justify-center">
                    <span className="text-white text-sm font-bold">V</span>
                </div>
                <span className="text-white font-semibold text-lg">
                    Veriply
                </span>
            </div>

            {/* Navigation Links */}
            <div className="flex-1 space-y-2">
                {navItems.map((item) => {
                    const Icon = item.icon;
                    return (
                        <Link
                            key={item.href}
                            href={item.href}
                            className={cn(
                                "flex items-center gap-3 px-3 py-2 rounded-lg transition-colors text-sm font-medium",
                                item.isActive
                                    ? "bg-emerald-600 text-white"
                                    : "text-slate-400 hover:bg-slate-800 hover:text-slate-100"
                            )}
                        >
                            <Icon className="w-5 h-5 flex-shrink-0" />
                            <span>{item.label}</span>
                        </Link>
                    );
                })}
            </div>

            {/* Footer */}
            <div className="pb-4 border-t border-slate-700 pt-4">
                <p className="text-xs text-slate-500 px-2">© 2025 Veriply</p>
            </div>
        </nav>
    );
}

export function MobileSidebar() {
    const pathname = usePathname();
    const [open, setOpen] = useState(false);

    const navItems = NAVIGATION_ITEMS.map((item) => ({
        ...item,
        isActive: pathname.startsWith(item.href),
    }));

    return (
        <Sheet open={open} onOpenChange={setOpen}>
            <SheetTrigger asChild className="md:hidden">
                <Button variant="ghost" size="icon" className="text-slate-700">
                    <Menu className="w-5 h-5" />
                </Button>
            </SheetTrigger>
            <SheetContent side="left" className="w-64 bg-slate-950 p-0">
                <SheetTitle className="sr-only">Navigation Menu</SheetTitle>
                <div className="flex flex-col h-full pt-4">
                    {/* Logo */}
                    <div className="mb-8 flex items-center gap-2 px-4">
                        <div className="w-8 h-8 rounded-lg bg-emerald-600 flex items-center justify-center">
                            <span className="text-white text-sm font-bold">
                                V
                            </span>
                        </div>
                        <span className="text-white font-semibold text-lg">
                            Veriply
                        </span>
                    </div>

                    {/* Navigation Links */}
                    <div className="flex-1 space-y-2 px-4">
                        {navItems.map((item) => {
                            const Icon = item.icon;
                            return (
                                <Link
                                    key={item.href}
                                    href={item.href}
                                    onClick={() => setOpen(false)}
                                    className={cn(
                                        "flex items-center gap-3 px-3 py-2 rounded-lg transition-colors text-sm font-medium",
                                        item.isActive
                                            ? "bg-emerald-600 text-white"
                                            : "text-slate-400 hover:bg-slate-800 hover:text-slate-100"
                                    )}
                                >
                                    <Icon className="w-5 h-5 flex-shrink-0" />
                                    <span>{item.label}</span>
                                </Link>
                            );
                        })}
                    </div>

                    {/* Footer */}
                    <div className="pb-4 border-t border-slate-700 pt-4 px-4">
                        <p className="text-xs text-slate-500">© 2025 Veriply</p>
                    </div>
                </div>
            </SheetContent>
        </Sheet>
    );
}
