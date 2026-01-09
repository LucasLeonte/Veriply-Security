"use client";

import { DashboardLayout } from "@/components";
import { BotDocumentAccess } from "@/components/bot/BotDocumentAccess";
import ChatInterface from "@/components/chat/ChatInterface";
import ChatHistoryPanel from "@/components/chat/ChatHistoryPanel";
import { WidgetConfigClient } from "@/app/dashboard/groups/[groupId]/bots/[botId]/widget/widget-client";
import { useParams, useSearchParams } from "next/navigation";
import {
    ArrowLeft,
    Settings,
    FileText,
    MessageCircle,
    Clock3,
    Settings2,
    BookOpen,
} from "lucide-react";
import Link from "next/link";
import { useEffect, useState } from "react";
import { useGroup } from "@/contexts/GroupContext";
import { botsApi } from "@/lib/api/bots";
import { Bot } from "@/types/bot";
import BotGeneralSettings from "@/components/bot/BotGeneralSettings";
import VerifiedKBTab from "@/components/bot/VerifiedKBTab";

type TabType = "settings" | "documents" | "chat" | "history" | "widget" | "verified-kb";

export default function BotSettingsPage() {
    const params = useParams();
    const searchParams = useSearchParams();
    const botId = params.botId as string;
    const { currentGroup } = useGroup();
    const [activeTab, setActiveTab] = useState<TabType>("chat");
    const [bot, setBot] = useState<Bot | null>(null);
    const [loading, setLoading] = useState<boolean>(true);
    const [error, setError] = useState<string | null>(null);

    // Set active tab from query parameter
    useEffect(() => {
        const tab = searchParams.get("tab") as TabType | null;
        if (
            tab &&
            ["chat", "documents", "settings", "history", "widget", "verified-kb"].includes(tab)
        ) {
            setActiveTab(tab);
        }
    }, [searchParams]);

    useEffect(() => {
        if (!currentGroup) return;
        setLoading(true);
        botsApi
            .getBotDetails(currentGroup.id, botId)
            .then(setBot)
            .catch((e) => setError(e.message || "Failed to load bot"))
            .finally(() => setLoading(false));
    }, [currentGroup, botId]);

    if (!currentGroup) {
        return (
            <DashboardLayout>
                <div className="text-center py-12">
                    <p className="text-slate-600">
                        Please select a group first
                    </p>
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

                {/* Tabs */}
                <div className="border-b border-slate-200">
                    <nav className="flex gap-6 flex-wrap">
                        <button
                            onClick={() => setActiveTab("chat")}
                            className={`flex items-center gap-2 px-1 py-3 text-sm font-medium border-b-2 transition-colors ${
                                activeTab === "chat"
                                    ? "border-emerald-600 text-emerald-600"
                                    : "border-transparent text-slate-600 hover:text-slate-900"
                            }`}
                        >
                            <MessageCircle size={16} />
                            Chat
                        </button>
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
                        <button
                            onClick={() => setActiveTab("history")}
                            className={`flex items-center gap-2 px-1 py-3 text-sm font-medium border-b-2 transition-colors ${
                                activeTab === "history"
                                    ? "border-emerald-600 text-emerald-600"
                                    : "border-transparent text-slate-600 hover:text-slate-900"
                            }`}
                        >
                            <Clock3 size={16} />
                            History
                        </button>
                        <button
                            onClick={() => setActiveTab("widget")}
                            className={`flex items-center gap-2 px-1 py-3 text-sm font-medium border-b-2 transition-colors ${
                                activeTab === "widget"
                                    ? "border-emerald-600 text-emerald-600"
                                    : "border-transparent text-slate-600 hover:text-slate-900"
                            }`}
                        >
                            <Settings2 size={16} />
                            Widget Configuration
                        </button>
                        <button
                            onClick={() => setActiveTab("verified-kb")}
                            className={`flex items-center gap-2 px-1 py-3 text-sm font-medium border-b-2 transition-colors ${
                                activeTab === "verified-kb"
                                    ? "border-emerald-600 text-emerald-600"
                                    : "border-transparent text-slate-600 hover:text-slate-900"
                            }`}
                        >
                            <BookOpen size={16} />
                            Verified KB
                        </button>
                    </nav>
                </div>

                {/* Content */}
                <div className="py-4">
                    {activeTab === "chat" && (
                        <div className="space-y-4">
                            <div className="bg-emerald-50 border border-emerald-200 rounded-lg p-4 text-sm text-emerald-800">
                                <p className="font-medium mb-1">
                                    Test Your Bot
                                </p>
                                <p className="text-emerald-700">
                                    Chat with your bot to test its responses and
                                    document access. The bot will search through
                                    documents you've granted access to.
                                </p>
                            </div>

                            {loading ? (
                                <div className="p-6 text-slate-600">
                                    Loading bot…
                                </div>
                            ) : error ? (
                                <div className="p-6 text-red-700 bg-red-50 border border-red-200 rounded">
                                    {error}
                                </div>
                            ) : bot ? (
                                <ChatInterface
                                    botId={botId}
                                    botName={bot.name}
                                    botAvatar={bot.avatar_url}
                                    description={bot.description}
                                    isPublic={bot.is_public}
                                    confidenceThreshold={
                                        bot.confidence_threshold
                                    }
                                />
                            ) : null}
                        </div>
                    )}

                    {activeTab === "documents" && (
                        <div className="space-y-4">
                            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 text-sm text-blue-800">
                                <p className="font-medium mb-1">
                                    Document Access Control
                                </p>
                                <p className="text-blue-700">
                                    Control which documents and folders this bot
                                    can access. Folder settings apply to all
                                    documents in that folder unless overridden
                                    by explicit document settings.
                                </p>
                            </div>

                            <BotDocumentAccess
                                botId={botId}
                                groupId={currentGroup.id}
                            />
                        </div>
                    )}

                    {activeTab === "settings" && currentGroup && (
                        <div className="bg-white border border-slate-200 rounded-lg p-6">
                            <BotGeneralSettings
                                groupId={currentGroup.id}
                                botId={botId}
                            />
                        </div>
                    )}

                    {activeTab === "history" && (
                        <div className="space-y-4">
                            <div className="bg-slate-50 border border-slate-200 rounded-lg p-4 text-sm text-slate-800">
                                <p className="font-medium mb-1">
                                    Conversation History
                                </p>
                                <p className="text-slate-700">
                                    View past conversations for this bot.
                                    History is available to owners/admins only.
                                </p>
                            </div>
                            <ChatHistoryPanel
                                botId={botId}
                                onResumeChat={() => setActiveTab("chat")}
                            />
                        </div>
                    )}

                    {activeTab === "widget" && currentGroup && (
                        <div className="space-y-4">
                            <WidgetConfigClient
                                groupId={currentGroup.id}
                                botId={botId}
                                hideNav
                            />
                        </div>
                    )}

                    {activeTab === "verified-kb" && currentGroup && (
                        <VerifiedKBTab groupId={currentGroup.id} />
                    )}
                </div>
            </div>
        </DashboardLayout>
    );
}
