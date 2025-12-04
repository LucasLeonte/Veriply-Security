"use client";

import { DashboardLayout } from "@/components";

export default function KnowledgeBasePage() {
    return (
        <DashboardLayout>
            <div className="space-y-6">
                <h2 className="text-2xl font-semibold text-slate-900">
                    Knowledge Base
                </h2>
                <div className="bg-white rounded-lg border border-slate-200 p-6">
                    <p className="text-slate-600">
                        Knowledge Base page - Manage your verified answers here.
                    </p>
                </div>
            </div>
        </DashboardLayout>
    );
}
