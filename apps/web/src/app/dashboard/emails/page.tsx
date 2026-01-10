"use client";

import { useState, useEffect, useCallback } from "react";
import { DashboardLayout } from "@/components";
import Link from "next/link";
import { EmailList } from "@/components/emails/EmailList";
import { EmailDetail } from "@/components/emails/EmailDetail";
import { getAccessToken } from "@/lib/auth";
import { EmailRule, listEmailRules, createEmailRule, updateEmailRule, deleteEmailRule, reorderEmailRules, testEmailRule, getMonitoringStatus, setMonitoringPause, MonitoringStatus } from "@/lib/api/emailRules";
import { EmailIntegration, listIntegrations, disconnectIntegration, setDefaultReplyBot, GmailMessage } from "@/lib/api/integrations";
import { botsApi } from "@/lib/api/bots";
import { Bot } from "@/types/bot";
import { useGroup } from "@/contexts/GroupContext";
import RuleForm from "../../../components/email-rules/RuleForm";
import RulesList from "../../../components/email-rules/RulesList";
import TestRuleModal from "../../../components/email-rules/TestRuleModal";
import { Mail, Plus, Inbox, Send, Menu, Trash2, Settings as SettingsIcon, CheckCircle, XCircle, ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { Separator } from "@/components/ui/separator";

export default function EmailsPage() {
    // View State
    const [view, setView] = useState<"MAIL" | "SETTINGS">("MAIL");

    // Mail State
    const [token, setToken] = useState<string | null>(null);
    const [integrations, setIntegrations] = useState<EmailIntegration[]>([]);
    const [loadingIntegrations, setLoadingIntegrations] = useState(true);
    const [activeFolder, setActiveFolder] = useState<"INBOX" | "SENT">("INBOX");
    const [selectedEmailId, setSelectedEmailId] = useState<string | null>(null);
    const [isMobileListOpen, setIsMobileListOpen] = useState(true);

    // Settings/Rules State
    const [bots, setBots] = useState<Bot[]>([]);
    const [rules, setRules] = useState<EmailRule[]>([]);
    const [selectedIntegrationId, setSelectedIntegrationId] = useState<string | null>(null);
    const [showTestModal, setShowTestModal] = useState<{ open: boolean; ruleId?: string }>({ open: false });
    const [loadingRules, setLoadingRules] = useState(false); // Renamed from loading
    const [error, setError] = useState<string | null>(null);
    const [monitoring, setMonitoring] = useState<MonitoringStatus | null>(null);
    const [monitoringError, setMonitoringError] = useState<string | null>(null);
    const [savingDefaultBot, setSavingDefaultBot] = useState<string | null>(null);
    const { currentGroup } = useGroup();

    // -- Effects --

    useEffect(() => {
        const t = getAccessToken();
        if (t) {
            setToken(t);
        }
    }, []);

    useEffect(() => {
        if (!token) return;
        (async () => {
            try {
                const ints = await listIntegrations(token);
                setIntegrations(ints.integrations);
                if (ints.integrations.length > 0) {
                    setSelectedIntegrationId(ints.integrations[0].id);
                }
            } catch (e: unknown) {
                const msg = e instanceof Error ? e.message : "Failed to load integrations";
                setError(msg);
            } finally {
                setLoadingIntegrations(false);
            }
        })();
    }, [token]);

    useEffect(() => {
        if (!currentGroup) return;
        (async () => {
            try {
                const resp = await botsApi.listBots(currentGroup.id, 50, 0);
                setBots(resp.bots);
            } catch (e: unknown) {
                const msg = e instanceof Error ? e.message : "Failed to load bots";
                setError(msg);
            }
        })();
    }, [currentGroup]);

    const refreshRules = useCallback(async () => {
        if (!token) return;
        setLoadingRules(true);
        try {
            const data = await listEmailRules(token, selectedIntegrationId || undefined);
            setRules(data);
        } catch (e: unknown) {
            const msg = e instanceof Error ? e.message : "Failed to load rules";
            setError(msg);
        } finally {
            setLoadingRules(false);
        }
    }, [token, selectedIntegrationId]);

    const refreshMonitoring = useCallback(async () => {
        if (!token || !selectedIntegrationId) return;
        try {
            const status = await getMonitoringStatus(token, selectedIntegrationId);
            setMonitoring(status);
            setMonitoringError(null);
        } catch (e: unknown) {
            const msg = e instanceof Error ? e.message : "Failed to load monitoring status";
            setMonitoringError(msg);
        }
    }, [token, selectedIntegrationId]);

    const onSetDefaultBot = useCallback(async (integrationId: string, botId: string | null) => {
        if (!token) return;
        try {
            setSavingDefaultBot(integrationId);
            await setDefaultReplyBot(token, integrationId, botId);
            const ints = await listIntegrations(token);
            setIntegrations(ints.integrations);
        } catch (e: unknown) {
            const msg = e instanceof Error ? e.message : "Failed to set default bot";
            setError(msg);
        } finally {
            setSavingDefaultBot(null);
        }
    }, [token]);

    useEffect(() => {
        if (token) {
            refreshRules();
            refreshMonitoring();
        }
    }, [token, selectedIntegrationId, refreshRules, refreshMonitoring]);

    useEffect(() => {
        if (!token || !selectedIntegrationId || view !== "SETTINGS") return;
        const id = setInterval(() => {
            refreshMonitoring();
        }, 15000);
        return () => clearInterval(id);
    }, [token, selectedIntegrationId, view, refreshMonitoring]);

    // -- Handlers --

    const handleSelectEmail = (msg: GmailMessage) => {
        setSelectedEmailId(msg.id);
        setIsMobileListOpen(false);
    };

    const onCreateRule = async (payload: Parameters<typeof createEmailRule>[1]) => {
        if (!token) return;
        await createEmailRule(token, payload);
        await refreshRules();
    };

    const onUpdateRule = async (id: string, payload: Parameters<typeof updateEmailRule>[2]) => {
        if (!token) return;
        await updateEmailRule(token, id, payload);
        await refreshRules();
    };

    const onDeleteRule = async (id: string) => {
        if (!token) return;
        await deleteEmailRule(token, id);
        await refreshRules();
    };

    const onReorder = async (orderedIds: string[]) => {
        if (!token) return;
        await reorderEmailRules(token, orderedIds);
        await refreshRules();
    };

    const onTestRule = async (id: string, sample: { subject: string; body: string; sender?: string; folder?: string; labels?: string[] }) => {
        if (!token) return { matched: false, explanation: "No token" };
        return await testEmailRule(token, id, sample);
    };

    const onTogglePause = async () => {
        if (!token || !selectedIntegrationId) return;
        const next = !(monitoring?.is_paused ?? false);
        try {
            const updated = await setMonitoringPause(token, selectedIntegrationId, next);
            setMonitoring(updated);
            setMonitoringError(null);
        } catch (e: unknown) {
            const msg = e instanceof Error ? e.message : "Failed to update pause state";
            setMonitoringError(msg);
        }
    };

    const handleDisconnect = async (integrationId: string) => {
        if (!token) return;
        if (!confirm("Are you sure you want to disconnect this email account?")) return;
        try {
            await disconnectIntegration(integrationId, token);
            setIntegrations(integrations.filter(i => i.id !== integrationId));
            if (selectedIntegrationId === integrationId) {
                const remaining = integrations.filter(i => i.id !== integrationId);
                setSelectedIntegrationId(remaining.length > 0 ? remaining[0].id : null);
            }
            setError(null);
        } catch (e: unknown) {
            const msg = e instanceof Error ? e.message : "Failed to disconnect integration";
            setError(msg);
        }
    };

    const fmt = (s?: string | null) => {
        if (!s) return "—";
        try { return new Date(s).toLocaleString(); } catch { return s; }
    };

    // -- Render --

    const selectedIntegration = integrations.find(i => i.id === selectedIntegrationId);

    if (loadingIntegrations && token) {
        return (
            <DashboardLayout>
                <div className="flex h-[calc(100vh-4rem)] items-center justify-center">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
                </div>
            </DashboardLayout>
        );
    }

    if (integrations.length === 0 && token) {
        return (
            <DashboardLayout>
                <div className="min-h-[60vh] flex items-center justify-center">
                    <div className="text-center max-w-md px-4">
                        <div className="w-20 h-20 bg-indigo-100 rounded-full flex items-center justify-center mx-auto mb-6">
                            <Mail className="w-10 h-10 text-indigo-600" />
                        </div>
                        <h1 className="text-3xl font-bold text-gray-900 mb-3">Welcome to Email Hub</h1>
                        <p className="text-gray-600 mb-8 leading-relaxed">Connect your email account to get started.</p>
                        <Link
                            href="/dashboard/integrations"
                            className="inline-flex items-center gap-2 bg-indigo-600 text-white px-8 py-3 rounded-lg font-semibold hover:bg-indigo-700 shadow-lg transition-all"
                        >
                            <Plus className="w-5 h-5" />
                            Connect Email Account
                        </Link>
                    </div>
                </div>
            </DashboardLayout>
        );
    }

    return (
        <DashboardLayout disableContentPadding={true}>
            {view === "MAIL" ? (
                <div className="flex h-full bg-white">
                    {/* Left Sidebar / List Column */}
                    <div className={cn(
                        "flex flex-col border-r bg-gray-50/50 w-full md:w-[400px] lg:w-[450px] shrink-0 transition-all duration-300 absolute md:relative z-10 h-full",
                        isMobileListOpen ? "translate-x-0" : "-translate-x-full md:translate-x-0"
                    )}>
                        {/* Header */}
                        <div className="h-16 flex items-center justify-between px-4 border-b bg-white shrink-0">
                            <div className="flex items-center gap-2">
                                <h1 className="text-lg font-semibold text-gray-900">Inbox</h1>
                                <span className="bg-indigo-100 text-indigo-700 text-xs px-2 py-0.5 rounded-full font-medium">Beta</span>
                            </div>
                            <Button variant="ghost" size="icon" title="Settings & Rules" onClick={() => setView("SETTINGS")}>
                                <SettingsIcon className="h-5 w-5 text-gray-500" />
                            </Button>
                        </div>

                        {/* Folder Tabs */}
                        <div className="p-2 border-b bg-white shrink-0">
                            <div className="grid grid-cols-2 gap-1 bg-gray-100 p-1 rounded-lg">
                                <button
                                    onClick={() => setActiveFolder("INBOX")}
                                    className={cn(
                                        "flex items-center justify-center gap-2 py-1.5 text-sm font-medium rounded-md transition-all",
                                        activeFolder === "INBOX" ? "bg-white text-gray-900 shadow-sm" : "text-gray-500 hover:text-gray-700"
                                    )}
                                >
                                    <Inbox className="w-4 h-4" /> Inbox
                                </button>
                                <button
                                    onClick={() => setActiveFolder("SENT")}
                                    className={cn(
                                        "flex items-center justify-center gap-2 py-1.5 text-sm font-medium rounded-md transition-all",
                                        activeFolder === "SENT" ? "bg-white text-gray-900 shadow-sm" : "text-gray-500 hover:text-gray-700"
                                    )}
                                >
                                    <Send className="w-4 h-4" /> Sent
                                </button>
                            </div>
                        </div>

                        {/* Email List */}
                        <div className="flex-1 overflow-y-auto">
                            {token ? (
                                <EmailList
                                    token={token}
                                    folder={activeFolder}
                                    selectedId={selectedEmailId}
                                    onSelect={handleSelectEmail}
                                    provider={selectedIntegration?.provider}
                                />
                            ) : (
                                <div className="p-8 text-center text-gray-500">Loading...</div>
                            )}
                        </div>
                    </div>

                    {/* Right Detail Column */}
                    <div className="flex-1 flex flex-col h-full overflow-hidden bg-white relative">
                        {selectedEmailId && token ? (
                            <EmailDetail
                                token={token}
                                messageId={selectedEmailId}
                                folder={activeFolder}
                                onClose={() => setIsMobileListOpen(true)} // Back button for mobile
                            />
                        ) : (
                            <div className="flex-1 flex flex-col items-center justify-center text-gray-400 bg-slate-50">
                                <Mail className="w-16 h-16 mb-4 opacity-20" />
                                <p className="text-lg font-medium">Select an email to view</p>
                            </div>
                        )}
                    </div>
                </div>
            ) : (
                // Settings & Rules View
                <div className="h-full overflow-y-auto bg-slate-100">
                    <div className="max-w-7xl mx-auto p-6 space-y-6">
                        {/* Header */}
                        <div className="flex items-center gap-4 mb-6">
                            <Button variant="ghost" onClick={() => setView("MAIL")} className="gap-2">
                                <ArrowLeft className="w-4 h-4" /> Back to Inbox
                            </Button>
                            <div>
                                <h1 className="text-2xl font-bold text-gray-900">Settings & Rules</h1>
                                <p className="text-gray-600">Configure email integrations and automation rules</p>
                            </div>
                        </div>

                        {/* Connected Accounts */}
                        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                            <div className="flex items-center justify-between mb-4">
                                <div>
                                    <h2 className="text-xl font-semibold text-gray-900">Connected Accounts</h2>
                                    <p className="text-sm text-gray-600 mt-1">Manage your email integrations</p>
                                </div>
                                <Link
                                    href="/dashboard/integrations"
                                    className="inline-flex items-center gap-2 bg-indigo-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-indigo-700 transition-colors"
                                >
                                    <Plus className="w-4 h-4" />
                                    Add Account
                                </Link>
                            </div>

                            <div className="space-y-3">
                                {integrations.map((integration) => (
                                    <div
                                        key={integration.id}
                                        className="flex items-center justify-between p-4 bg-gray-50 rounded-lg border border-gray-200 hover:border-gray-300 transition-colors"
                                    >
                                        <div className="flex items-center gap-4">
                                            <div className="w-12 h-12 bg-white rounded-lg border border-gray-200 flex items-center justify-center">
                                                <Mail className="w-6 h-6 text-indigo-600" />
                                            </div>
                                            <div>
                                                <h3 className="font-semibold text-gray-900 capitalize">{integration.provider}</h3>
                                                <div className="flex items-center gap-2 mt-1">
                                                    {integration.status === 'connected' ? (
                                                        <>
                                                            <CheckCircle className="w-4 h-4 text-green-600" />
                                                            <span className="text-sm text-green-600 font-medium">Connected</span>
                                                        </>
                                                    ) : (
                                                        <>
                                                            <XCircle className="w-4 h-4 text-orange-600" />
                                                            <span className="text-sm text-orange-600 font-medium">Disconnected</span>
                                                        </>
                                                    )}
                                                    {integration.last_sync_time && (
                                                        <span className="text-xs text-gray-500">• Last sync: {fmt(integration.last_sync_time)}</span>
                                                    )}
                                                </div>
                                                <div className="flex items-center gap-2 mt-2">
                                                    <label className="text-sm text-gray-700">Default Bot:</label>
                                                    <select
                                                        className="border rounded px-2 py-1 text-sm"
                                                        value={integration.default_reply_bot_id ?? ""}
                                                        disabled={savingDefaultBot === integration.id}
                                                        onChange={(e) => {
                                                            const v = e.target.value;
                                                            onSetDefaultBot(integration.id, v === "" ? null : v);
                                                        }}
                                                    >
                                                        <option value="">— None —</option>
                                                        {bots.map((b) => (
                                                            <option key={b.id} value={b.id}>{b.name}</option>
                                                        ))}
                                                    </select>
                                                </div>
                                            </div>
                                        </div>
                                        <button
                                            onClick={() => handleDisconnect(integration.id)}
                                            className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-red-600 hover:bg-red-50 rounded-lg border border-red-200 hover:border-red-300 transition-colors"
                                        >
                                            <Trash2 className="w-4 h-4" />
                                            Disconnect
                                        </button>
                                    </div>
                                ))}
                            </div>
                        </div>

                        {/* Monitoring Rules */}
                        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                            <div className="mb-6">
                                <h2 className="text-xl font-semibold text-gray-900">Monitoring Rules</h2>
                                <p className="text-sm text-gray-600 mt-1">Configure email monitoring and auto-response rules</p>
                            </div>

                            <RuleForm
                                integrations={integrations}
                                bots={bots}
                                defaultIntegrationId={selectedIntegrationId || undefined}
                                onCreate={onCreateRule}
                                onIntegrationChange={setSelectedIntegrationId}
                            />
                        </div>

                        {/* Monitoring Status */}
                        {selectedIntegrationId && (
                            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                                <div className="flex items-center justify-between mb-6">
                                    <div>
                                        <h2 className="text-xl font-semibold text-gray-900">Monitoring Status</h2>
                                        <p className="text-sm text-gray-600 mt-1">Email polling status for selected integration</p>
                                    </div>
                                    <button
                                        onClick={onTogglePause}
                                        className={`px-4 py-2 rounded-lg text-sm font-semibold transition-all ${monitoring?.is_paused
                                            ? 'bg-green-600 hover:bg-green-700 text-white shadow-md'
                                            : 'bg-yellow-500 hover:bg-yellow-600 text-white shadow-md'
                                            }`}
                                    >
                                        {monitoring?.is_paused ? '▶ Resume Monitoring' : '⏸ Pause Monitoring'}
                                    </button>
                                </div>

                                {monitoringError && (
                                    <div className="mb-4 p-3 rounded-lg bg-red-50 border border-red-200 text-red-700 text-sm">
                                        {monitoringError}
                                    </div>
                                )}

                                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                                    <div className="p-4 bg-gray-50 rounded-lg border border-gray-200">
                                        <div className="text-xs font-medium text-gray-500 uppercase tracking-wider mb-1">Last Poll</div>
                                        <div className="text-sm font-semibold text-gray-900">{fmt(monitoring?.last_poll_at)}</div>
                                    </div>
                                    <div className="p-4 bg-gray-50 rounded-lg border border-gray-200">
                                        <div className="text-xs font-medium text-gray-500 uppercase tracking-wider mb-1">Last Success</div>
                                        <div className="text-sm font-semibold text-gray-900">{fmt(monitoring?.last_success_at)}</div>
                                    </div>
                                    <div className="p-4 bg-gray-50 rounded-lg border border-gray-200">
                                        <div className="text-xs font-medium text-gray-500 uppercase tracking-wider mb-1">Next Poll</div>
                                        <div className="text-sm font-semibold text-gray-900">{fmt(monitoring?.next_poll_at)}</div>
                                    </div>
                                    <div className="p-4 bg-gray-50 rounded-lg border border-gray-200">
                                        <div className="text-xs font-medium text-gray-500 uppercase tracking-wider mb-1">Error Count</div>
                                        <div className="text-sm font-semibold text-gray-900">{monitoring?.error_count ?? 0}</div>
                                    </div>
                                </div>

                                {monitoring?.last_error_at && (
                                    <div className="mt-4 p-4 bg-red-50 rounded-lg border border-red-200">
                                        <div className="text-xs font-medium text-red-700 uppercase tracking-wider mb-1">Last Error</div>
                                        <div className="text-sm text-red-900">
                                            {fmt(monitoring?.last_error_at)} — {monitoring?.last_error_message || 'Unknown error'}
                                        </div>
                                    </div>
                                )}
                            </div>
                        )}

                        {/* Rules List */}
                        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                            <h2 className="text-xl font-semibold text-gray-900 mb-4">Active Rules</h2>
                            <RulesList
                                rules={rules}
                                bots={bots}
                                onUpdate={onUpdateRule}
                                onDelete={onDeleteRule}
                                onReorder={onReorder}
                                onTest={(id: string) => setShowTestModal({ open: true, ruleId: id })}
                            />

                            {loadingRules && (
                                <div className="text-center py-8 text-gray-500">Loading rules...</div>
                            )}
                        </div>

                        {error && (
                            <div className="p-4 rounded-lg bg-red-50 border border-red-200 text-red-700">
                                {error}
                            </div>
                        )}

                        <TestRuleModal
                            open={showTestModal.open}
                            onClose={() => setShowTestModal({ open: false })}
                            ruleId={showTestModal.ruleId}
                            onTest={onTestRule}
                        />
                    </div>
                </div>
            )}
        </DashboardLayout>
    );
}
