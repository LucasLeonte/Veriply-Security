"use client";

import React from "react";
import { GroupProvider } from "@/contexts/GroupContext";

export function Providers({ children }: { children: React.ReactNode }) {
    return <GroupProvider>{children}</GroupProvider>;
}
