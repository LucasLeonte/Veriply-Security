"use client";

import React from "react";
import { AuthProvider } from "@/contexts/auth-context";
import { GroupProvider } from "@/contexts/GroupContext";
import { ToastProvider } from "@/components/ui/toast";

export function Providers({ children }: { children: React.ReactNode }) {
    return (
        <ToastProvider>
            <AuthProvider>
                <GroupProvider>{children}</GroupProvider>
            </AuthProvider>
        </ToastProvider>
    );
}
