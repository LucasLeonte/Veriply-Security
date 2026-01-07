"use client";

import React from "react";
import { GroupProvider } from "@/contexts/GroupContext";
import { ToastProvider } from "@/components/ui/toast";

export function Providers({ children }: { children: React.ReactNode }) {
    return (
        <ToastProvider>
            <GroupProvider>{children}</GroupProvider>
        </ToastProvider>
    );
}
