"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { DashboardLayout } from "@/components";

export default function DashboardPage() {
    const router = useRouter();

    useEffect(() => {
        const token = localStorage.getItem("access_token");
        if (!token) {
            router.push("/login");
        }
    }, [router]);

    return (
        <DashboardLayout>
            <div className="space-y-6">
                <h2 className="text-2xl font-semibold text-slate-900">
                    Dashboard
                </h2>
                <div className="bg-white rounded-lg border border-slate-200 p-6">
                    <p className="text-slate-600">
                        Dashboard content goes here. Navigate using the sidebar.
                    </p>
                </div>
            </div>
        </DashboardLayout>
    );
}
