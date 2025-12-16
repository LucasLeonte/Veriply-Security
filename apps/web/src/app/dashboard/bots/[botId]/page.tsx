"use client";

import { DashboardLayout } from "@/components";
import { BotDocumentAccess } from "@/components/bot/BotDocumentAccess";
import { useParams } from "next/navigation";
import { ArrowLeft, Settings, FileText } from "lucide-react";
import Link from "next/link";
import { useState } from "react";
import { useGroup } from "@/contexts/GroupContext";

type TabType = "settings" | "documents";

export default function BotSettingsPage() {
    const params = useParams();
    const botId = params.botId as string;
    const { currentGroup } = useGroup();
    const [activeTab, setActiveTab] = useState<TabType>("documents");

    if (!currentGroup) {
        return (
            <DashboardLayout>
                <div className="text-center py-12">
                    <p className="text-slate-600">Please select a group first</p>
                </div>
            </DashboardLayout>
        );
    }

    return (
        <DashboardLayout>
            <div className="space-y-6">
                {/* Breadcrumb */}
                <div className="flex items-center gap-2">
                    <Link
                        href="/dashboard/bots"
                        className="flex items-center gap-2 text-sm text-slate-600 hover:text-slate-900 transition-colors"
                    >
                        <ArrowLeft size={16} />
                        Back to Bots
                    </Link>
                </div>

                {/* Header */}
                <div>
                    <h2 className="text-2xl font-semibold text-slate-900">
                        Bot Settings
                    </h2>
                    <p className="text-sm text-slate-600 mt-1">
                        Configure bot access and settings
                    </p>
                </div>

                {/* Tabs */}
                <div className="border-b border-slate-200">
                    <nav className="flex gap-6">
                        <button
                            onClick={() => setActiveTab("documents")}
                            className={`flex items-center gap-2 px-1 py-3 text-sm font-medium border-b-2 transition-colors ${
                                activeTab === "documents"
                                    ? "border-emerald-600 text-emerald-600"
                                    : "border-transparent text-slate-600 hover:text-slate-900"
                            }`}
                        >
                            <FileText size={16} />
                            Document Access
                        </button>
                        <button
                            onClick={() => setActiveTab("settings")}
                            className={`flex items-center gap-2 px-1 py-3 text-sm font-medium border-b-2 transition-colors ${
                                activeTab === "settings"
                                    ? "border-emerald-600 text-emerald-600"
                                    : "border-transparent text-slate-600 hover:text-slate-900"
                            }`}
                        >
                            <Settings size={16} />
                            General Settings
                        </button>
                    </nav>
                </div>

                {/* Content */}
                <div className="py-4">
                    {activeTab === "documents" && (
                        <div className="space-y-4">
                            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 text-sm text-blue-800">
                                <p className="font-medium mb-1">Document Access Control</p>
                                <p className="text-blue-700">
                                    Control which documents and folders this bot can access.
                                    Folder settings apply to all documents in that folder unless
                                    overridden by explicit document settings.
                                </p>
                            </div>

                            <BotDocumentAccess botId={botId} groupId={currentGroup.id} />
                        </div>
                    )}

                    {activeTab === "settings" && (
                        <div className="bg-white border border-slate-200 rounded-lg p-6">
                            <p className="text-slate-600">
                                General settings coming soon...
                            </p>
                        </div>
                    )}
                </div>
            </div>
        </DashboardLayout>
    );
}
