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
    Mail,
    Menu,
    ChevronDown,
    ListFilter,
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
import { GroupSwitcher } from "./GroupSwitcher";
import { useGroup } from "@/contexts/GroupContext";

const NAVIGATION_ITEMS = [
    { href: "/dashboard", icon: LayoutDashboard, label: "Dashboard" },
    { href: "/dashboard/bots", icon: Bot, label: "Bots" },
    { href: "/inbox", icon: Inbox, label: "Review Queue" },
    { href: "/dashboard/knowledge-base", icon: BookOpen, label: "Knowledge Base" },
    { href: "/dashboard/emails", icon: Mail, label: "Email Hub" },
    { 
        href: "/dashboard/integrations", 
        icon: Settings, 
        label: "Email Integrations",
        submenu: [
            { href: "/dashboard/integrations", label: "Manage Integrations" },
            { href: "/dashboard/email-rules", label: "Monitoring Rules" },
        ]
    },
    { href: "/analytics", icon: BarChart3, label: "Analytics" },
    { href: "/settings", icon: Settings, label: "Settings" },
];

interface SidebarProps {
    className?: string;
}

export function Sidebar({ className }: SidebarProps) {
    const pathname = usePathname();
    const { stats } = useHITLQueue();
    const { currentGroup } = useGroup();
    const [expandedItems, setExpandedItems] = useState<string[]>([]);

    const toggleExpanded = (href: string) => {
        setExpandedItems(prev => 
            prev.includes(href) 
                ? prev.filter(h => h !== href)
                : [...prev, href]
        );
    };

    const navItems = NAVIGATION_ITEMS.map((item) => ({
        ...item,
        isActive:
            pathname === item.href ||
            (pathname.startsWith(item.href + "/") &&
                item.href !== "/dashboard") ||
            (item.submenu?.some(sub => pathname === sub.href)),
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
                <GroupSwitcher />
            </div>

            {/* Navigation Links */}
            <div className="flex-1 space-y-1">
                {navItems.map((item) => {
                    const Icon = item.icon;
                    const badge =
                        item.href === "/inbox" && stats.pending > 0
                            ? stats.pending
                            : null;
                    const isExpanded = expandedItems.includes(item.href);
                    const hasSubmenu = item.submenu && item.submenu.length > 0;

                    return (
                        <div key={item.href}>
                            {hasSubmenu ? (
                                <button
                                    onClick={() => toggleExpanded(item.href)}
                                    className={cn(
                                        "w-full flex items-center gap-3 px-3 py-2 rounded-lg transition-colors text-sm font-medium border border-transparent",
                                        item.isActive
                                            ? "bg-sky-50 text-sky-700 border-sky-100"
                                            : "text-slate-600 hover:bg-slate-50"
                                    )}
                                >
                                    <Icon className="w-5 h-5 flex-shrink-0" />
                                    <span className="flex-1 text-left">{item.label}</span>
                                    <ChevronDown className={cn(
                                        "w-4 h-4 transition-transform",
                                        isExpanded && "rotate-180"
                                    )} />
                                </button>
                            ) : (
                                <Link
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
                            )}
                            
                            {/* Submenu */}
                            {hasSubmenu && isExpanded && (
                                <div className="ml-8 mt-1 space-y-1">
                                    {item.submenu.map((subItem) => (
                                        <Link
                                            key={subItem.href}
                                            href={subItem.href}
                                            className={cn(
                                                "block px-3 py-1.5 text-sm rounded-lg transition-colors",
                                                pathname === subItem.href
                                                    ? "text-sky-700 bg-sky-50 font-medium"
                                                    : "text-slate-600 hover:bg-slate-50"
                                            )}
                                        >
                                            {subItem.label}
                                        </Link>
                                    ))}
                                </div>
                            )}
                        </div>
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
