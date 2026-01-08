"use client";

import { ReactNode } from "react";
import { Sidebar } from "./Sidebar";
import { Header } from "./Header";
import { cn } from "@/lib/utils";

interface DashboardLayoutProps {
    children: ReactNode;
    className?: string;
}

export function DashboardLayout({ children, className }: DashboardLayoutProps) {
    return (
        <div className={cn("min-h-screen bg-slate-100", className)}>
            {/* Desktop Sidebar */}
            <Sidebar />

            {/* Main Content */}
            <div className="flex flex-col md:ml-64">
                {/* Header */}
                <Header />

                {/* Page Content */}
                <main className="flex-1 overflow-auto bg-slate-100">
                    <div className="p-4 md:p-6">{children}</div>
                </main>
            </div>
        </div>
    );
}
