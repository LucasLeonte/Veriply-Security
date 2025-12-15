"use client";

import React, { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
    LayoutDashboard,
    Bot,
    Inbox,
    BookOpen,
    BarChart3,
    Settings,
    Menu,
    ChevronDown,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "./ui/button";
import {
    Sheet,
    SheetContent,
    SheetTrigger,
    SheetTitle,
} from "./ui/sheet";
import { useHITLQueue } from "@/hooks/useHITLQueue";

const NAVIGATION_ITEMS = [
    { href: "/dashboard", icon: LayoutDashboard, label: "Dashboard" },
    { href: "/dashboard/bots", icon: Bot, label: "Bots" },
    { href: "/inbox", icon: Inbox, label: "Review Queue" },
    { href: "/knowledge-base", icon: BookOpen, label: "Knowledge Base" },
    { href: "/analytics", icon: BarChart3, label: "Analytics" },
    { href: "/settings", icon: Settings, label: "Settings" },
];

interface SidebarProps {
    className?: string;
}

export function Sidebar({ className }: SidebarProps) {
    const pathname = usePathname();
    const { stats } = useHITLQueue();

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
                "hidden md:flex flex-col w-64 bg-white border-r border-slate-200 h-screen fixed left-0 top-0 pt-4 px-4",
                className
            )}
        >
            {/* Current Group */}
            <div className="mb-4 rounded-xl border border-slate-200 bg-white p-3 shadow-sm">
                <button className="w-full flex items-center justify-between px-2 py-1.5 rounded-lg hover:bg-slate-50">
                    <div className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-sky-400 to-emerald-400 flex items-center justify-center text-white text-xs font-bold">
                            GR
                        </div>
                        <div className="text-left">
                            <p className="text-sm font-semibold text-slate-900">
                                Current Group
                            </p>
                            <p className="text-xs text-slate-500">Switch group</p>
                        </div>
                    </div>
                    <ChevronDown className="w-4 h-4 text-slate-400" />
                </button>
            </div>

            {/* Navigation Links */}
            <div className="flex-1 space-y-1">
                {navItems.map((item) => {
                    const Icon = item.icon;
                    const badge =
                        item.href === "/inbox" && stats.pending > 0
                            ? stats.pending
                            : null;

                    return (
                        <Link
                            key={item.href}
                            href={item.href}
                            className={cn(
                                "flex items-center gap-3 px-3 py-2 rounded-lg transition-colors text-sm font-medium border border-transparent",
                                item.isActive
                                    ? "bg-sky-50 text-sky-700 border-sky-100"
                                    : "text-slate-600 hover:bg-slate-50"
                            )}
                        >
                            <Icon className="w-5 h-5 flex-shrink-0" />
                            <span className="flex-1">{item.label}</span>
                            {badge && (
                                <span className="ml-auto px-2 py-0.5 text-xs font-medium rounded-full bg-amber-100 text-amber-700">
                                    {badge}
                                </span>
                            )}
                        </Link>
                    );
                })}
            </div>

            {/* Footer */}
            <div className="pb-4 pt-4 border-t border-slate-100">
                <div className="flex items-center gap-3 px-2">
                    <div className="w-8 h-8 rounded-full bg-slate-200 flex items-center justify-center text-slate-600 text-sm font-medium">
                        D
                    </div>
                    <div className="flex-1">
                        <p className="text-sm font-medium text-slate-900">Dario</p>
                        <p className="text-xs text-slate-500">Knowledge Manager</p>
                    </div>
                </div>
            </div>
        </nav>
    );
}

export function MobileSidebar() {
    const pathname = usePathname();
    const [open, setOpen] = useState(false);
    const { stats } = useHITLQueue();

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
                            const badge =
                                item.href === "/inbox" && stats.pending > 0
                                    ? stats.pending
                                    : null;

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
                                    <span className="flex-1">
                                        {item.label}
                                    </span>
                                    {badge && (
                                        <span className="ml-auto px-2 py-0.5 text-xs font-medium rounded-full bg-amber-600 text-white">
                                            {badge}
                                        </span>
                                    )}
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
