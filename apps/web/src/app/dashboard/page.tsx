"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { DashboardLayout } from "@/components";
import { getAccessToken } from "@/lib/auth";
import { useGroup } from "@/contexts/GroupContext";
import { botsApi } from "@/lib/api/bots";
import { documentsApi } from "@/lib/api/documents";
import { useHITLQueue } from "@/hooks/useHITLQueue";
import { useAnalytics } from "@/hooks/useAnalytics";
import {
    Bot as BotIcon,
    Inbox,
    BookOpen,
    Mail,
    BarChart3,
    Settings,
    MessageSquare,
    CheckCircle2,
    Clock,
    AlertTriangle,
} from "lucide-react";

export default function DashboardPage() {
    const router = useRouter();
    const { currentGroup } = useGroup();

    // Lightweight stats for cards
    const [botsTotal, setBotsTotal] = useState<number | null>(null);
    const [docsTotal, setDocsTotal] = useState<number | null>(null);
    const { stats: queueStats, isLoading: queueLoading } =
        useHITLQueue("oldest");
    const { metrics, isLoading: analyticsLoading } = useAnalytics();

    const formatPercent = (v?: number) =>
        typeof v === "number" && !Number.isNaN(v) ? `${v.toFixed(1)}%` : "—";

    const formatDuration = (seconds?: number) => {
        if (typeof seconds !== "number" || Number.isNaN(seconds)) return "—";
        const s = Math.round(seconds);
        const m = Math.floor(s / 60);
        const r = s % 60;
        return m > 0 ? `${m}m ${r}s` : `${r}s`;
    };

    useEffect(() => {
        const token = getAccessToken();
        if (!token) {
            router.push("/login");
        }
    }, [router]);

    // Fetch counts for Bots and Knowledge Base when group is selected
    useEffect(() => {
        (async () => {
            if (!currentGroup) {
                setBotsTotal(null);
                setDocsTotal(null);
                return;
            }
            try {
                const botsRes = await botsApi.listBots(currentGroup.id, 1, 0);
                setBotsTotal(botsRes.total_count ?? botsRes.bots.length);
            } catch {
                setBotsTotal(null);
            }
            try {
                const docsRes = await documentsApi.listDocuments(
                    currentGroup.id,
                    1,
                    1
                );
                setDocsTotal(docsRes.total);
            } catch {
                setDocsTotal(null);
            }
        })();
    }, [currentGroup?.id]);

    const disabledHint = useMemo(
        () => !currentGroup && "Select a group to manage resources",
        [currentGroup]
    );

    return (
        <DashboardLayout>
            <div className="space-y-8">
                <div className="flex items-start justify-between">
                    <div>
                        <h2 className="text-2xl font-semibold text-slate-900">
                            Dashboard
                        </h2>
                    </div>
                    <Link
                        href="/settings"
                        className="inline-flex items-center gap-2 px-3 py-2 text-sm rounded-lg border border-slate-300 hover:bg-slate-50"
                    >
                        <Settings className="h-4 w-4" /> Settings
                    </Link>
                </div>

                {!currentGroup && (
                    <div className="p-4 rounded-lg border border-amber-200 bg-amber-50 text-amber-900">
                        Select a group from the sidebar to see group-scoped
                        stats and actions.
                    </div>
                )}

                {/* Analytics overview */}
                <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
                    <div className="lg:col-span-2">
                        <div className="rounded-xl border border-slate-200 bg-white p-5">
                            <div className="flex items-center justify-between">
                                <div>
                                    <h3 className="font-semibold text-slate-900">
                                        Intervention Rate Trend
                                    </h3>
                                    <p className="text-sm text-slate-500">
                                        Last period
                                    </p>
                                </div>
                                <Link
                                    href="/analytics"
                                    className="text-sm text-violet-700 hover:underline"
                                >
                                    View full analytics
                                </Link>
                            </div>
                            <div className="mt-4 h-40">
                                {!metrics ||
                                analyticsLoading ||
                                !metrics.chartData?.length ? (
                                    <div className="flex h-full items-center justify-center text-slate-400 text-sm">
                                        No data
                                    </div>
                                ) : (
                                    <svg
                                        className="w-full h-full"
                                        viewBox="0 0 400 160"
                                        preserveAspectRatio="none"
                                    >
                                        {(() => {
                                            const pts = metrics.chartData;
                                            const n = pts.length;
                                            const w = 400;
                                            const h = 140; // leave 20px top/bottom padding in viewBox
                                            const xStep =
                                                n > 1 ? w / (n - 1) : w;
                                            const toY = (v: number) =>
                                                20 +
                                                (h -
                                                    (Math.max(
                                                        0,
                                                        Math.min(100, v)
                                                    ) /
                                                        100) *
                                                        h);
                                            const d = pts
                                                .map((p, i) => {
                                                    const x = i * xStep;
                                                    const y = toY(
                                                        p.interventionRate
                                                    );
                                                    return `${
                                                        i === 0 ? "M" : "L"
                                                    } ${x} ${y}`;
                                                })
                                                .join(" ");
                                            return (
                                                <>
                                                    <path
                                                        d={d}
                                                        stroke="#7c3aed"
                                                        strokeWidth="2"
                                                        fill="none"
                                                        strokeLinecap="round"
                                                    />
                                                </>
                                            );
                                        })()}
                                    </svg>
                                )}
                            </div>
                        </div>
                    </div>
                    <div className="space-y-4">
                        <div className="flex items-center gap-4 rounded-xl border border-slate-200 bg-white p-5">
                            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-sky-100 text-sky-700">
                                <MessageSquare className="h-5 w-5" />
                            </div>
                            <div>
                                <p className="text-sm text-slate-500">
                                    Conversations
                                </p>
                                <p className="text-2xl font-semibold text-slate-900">
                                    {analyticsLoading
                                        ? "…"
                                        : metrics?.totalQueries ?? "—"}
                                </p>
                            </div>
                        </div>
                        <div className="flex items-center gap-4 rounded-xl border border-slate-200 bg-white p-5">
                            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-emerald-100 text-emerald-700">
                                <CheckCircle2 className="h-5 w-5" />
                            </div>
                            <div>
                                <p className="text-sm text-slate-500">
                                    Resolution Rate
                                </p>
                                <p className="text-2xl font-semibold text-slate-900">
                                    {analyticsLoading
                                        ? "…"
                                        : formatPercent(
                                              metrics?.autoResolvedPercent
                                          )}
                                </p>
                            </div>
                        </div>
                        <div className="flex items-center gap-4 rounded-xl border border-slate-200 bg-white p-5">
                            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-amber-100 text-amber-700">
                                <Clock className="h-5 w-5" />
                            </div>
                            <div>
                                <p className="text-sm text-slate-500">
                                    Avg. Response
                                </p>
                                <p className="text-2xl font-semibold text-slate-900">
                                    {analyticsLoading
                                        ? "…"
                                        : formatDuration(
                                              metrics?.avgResponseTime
                                          )}
                                </p>
                            </div>
                        </div>
                        <div className="flex items-center gap-4 rounded-xl border border-slate-200 bg-white p-5">
                            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-rose-100 text-rose-700">
                                <AlertTriangle className="h-5 w-5" />
                            </div>
                            <div>
                                <p className="text-sm text-slate-500">
                                    Intervention Rate
                                </p>
                                <p className="text-2xl font-semibold text-slate-900">
                                    {analyticsLoading
                                        ? "…"
                                        : formatPercent(
                                              metrics?.hitlInterventionRate
                                          )}
                                </p>
                            </div>
                        </div>
                    </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
                    {/* Bots */}
                    <div className="bg-white border border-slate-200 rounded-xl p-5 flex flex-col">
                        <div className="flex items-center justify-between">
                            <div className="flex items-center gap-3">
                                <div className="p-2 rounded-md bg-sky-100 text-sky-700">
                                    <BotIcon className="h-5 w-5" />
                                </div>
                                <div>
                                    <h3 className="font-medium text-slate-900">
                                        Bots
                                    </h3>
                                    <p className="text-sm text-slate-500">
                                        Build and manage assistants
                                    </p>
                                </div>
                            </div>
                            <span className="text-sm text-slate-500">
                                {botsTotal === null
                                    ? "—"
                                    : `${botsTotal} total`}
                            </span>
                        </div>
                        <div className="mt-4 flex gap-2">
                            <Link
                                href={currentGroup ? "/dashboard/bots" : "#"}
                                aria-disabled={!currentGroup}
                                className={`px-3 py-2 text-sm rounded-lg ${
                                    currentGroup
                                        ? "bg-sky-600 text-white hover:bg-sky-700"
                                        : "bg-slate-100 text-slate-400 cursor-not-allowed"
                                }`}
                                title={disabledHint || undefined}
                            >
                                Open Bots
                            </Link>
                            <Link
                                href={
                                    currentGroup
                                        ? "/dashboard/bots?create=1"
                                        : "#"
                                }
                                aria-disabled={!currentGroup}
                                className={`px-3 py-2 text-sm rounded-lg border ${
                                    currentGroup
                                        ? "border-slate-300 hover:bg-slate-50"
                                        : "border-slate-200 text-slate-400 cursor-not-allowed"
                                }`}
                                title={disabledHint || undefined}
                            >
                                New Bot
                            </Link>
                        </div>
                    </div>

                    {/* Review Queue */}
                    <div className="bg-white border border-slate-200 rounded-xl p-5 flex flex-col">
                        <div className="flex items-center justify-between">
                            <div className="flex items-center gap-3">
                                <div className="p-2 rounded-md bg-rose-100 text-rose-700">
                                    <Inbox className="h-5 w-5" />
                                </div>
                                <div>
                                    <h3 className="font-medium text-slate-900">
                                        Review Queue
                                    </h3>
                                    <p className="text-sm text-slate-500">
                                        Low-confidence answers to triage
                                    </p>
                                </div>
                            </div>
                            <span className="text-sm text-slate-500">
                                {queueLoading
                                    ? "…"
                                    : `${queueStats.pending ?? 0} pending`}
                            </span>
                        </div>
                        <div className="mt-4 flex gap-2">
                            <Link
                                href="/inbox"
                                className="px-3 py-2 text-sm rounded-lg bg-rose-600 text-white hover:bg-rose-700"
                            >
                                Open Queue
                            </Link>
                            <span className="self-center text-xs text-slate-500">
                                {queueLoading
                                    ? ""
                                    : `${queueStats.total ?? 0} total`}
                            </span>
                        </div>
                    </div>

                    {/* Knowledge Base */}
                    <div className="bg-white border border-slate-200 rounded-xl p-5 flex flex-col">
                        <div className="flex items-center justify-between">
                            <div className="flex items-center gap-3">
                                <div className="p-2 rounded-md bg-emerald-100 text-emerald-700">
                                    <BookOpen className="h-5 w-5" />
                                </div>
                                <div>
                                    <h3 className="font-medium text-slate-900">
                                        Knowledge Base
                                    </h3>
                                    <p className="text-sm text-slate-500">
                                        Documents and sources
                                    </p>
                                </div>
                            </div>
                            <span className="text-sm text-slate-500">
                                {docsTotal === null ? "—" : `${docsTotal} docs`}
                            </span>
                        </div>
                        <div className="mt-4 flex gap-2">
                            <Link
                                href={
                                    currentGroup
                                        ? "/dashboard/knowledge-base"
                                        : "#"
                                }
                                aria-disabled={!currentGroup}
                                className={`px-3 py-2 text-sm rounded-lg ${
                                    currentGroup
                                        ? "bg-emerald-600 text-white hover:bg-emerald-700"
                                        : "bg-slate-100 text-slate-400 cursor-not-allowed"
                                }`}
                                title={disabledHint || undefined}
                            >
                                Open KB
                            </Link>
                            <Link
                                href={
                                    currentGroup
                                        ? "/dashboard/knowledge-base?upload=1"
                                        : "#"
                                }
                                aria-disabled={!currentGroup}
                                className={`px-3 py-2 text-sm rounded-lg border ${
                                    currentGroup
                                        ? "border-slate-300 hover:bg-slate-50"
                                        : "border-slate-200 text-slate-400 cursor-not-allowed"
                                }`}
                                title={disabledHint || undefined}
                            >
                                Upload
                            </Link>
                        </div>
                    </div>

                    {/* Email */}
                    <div className="bg-white border border-slate-200 rounded-xl p-5 flex flex-col">
                        <div className="flex items-center justify-between">
                            <div className="flex items-center gap-3">
                                <div className="p-2 rounded-md bg-indigo-100 text-indigo-700">
                                    <Mail className="h-5 w-5" />
                                </div>
                                <div>
                                    <h3 className="font-medium text-slate-900">
                                        Email
                                    </h3>
                                    <p className="text-sm text-slate-500">
                                        Inbox and automations
                                    </p>
                                </div>
                            </div>
                        </div>
                        <div className="mt-4 flex gap-2">
                            <Link
                                href="/dashboard/emails"
                                className="px-3 py-2 text-sm rounded-lg bg-indigo-600 text-white hover:bg-indigo-700"
                            >
                                Open Email
                            </Link>
                            <Link
                                href="/dashboard/email-rules"
                                className="px-3 py-2 text-sm rounded-lg border border-slate-300 hover:bg-slate-50"
                            >
                                Rules
                            </Link>
                        </div>
                    </div>

                    {/* Analytics */}
                    <div className="bg-white border border-slate-200 rounded-xl p-5 flex flex-col">
                        <div className="flex items-center justify-between">
                            <div className="flex items-center gap-3">
                                <div className="p-2 rounded-md bg-violet-100 text-violet-700">
                                    <BarChart3 className="h-5 w-5" />
                                </div>
                                <div>
                                    <h3 className="font-medium text-slate-900">
                                        Analytics
                                    </h3>
                                    <p className="text-sm text-slate-500">
                                        Performance and quality
                                    </p>
                                </div>
                            </div>
                        </div>
                        <div className="mt-4">
                            <Link
                                href="/analytics"
                                className="px-3 py-2 text-sm rounded-lg bg-violet-600 text-white hover:bg-violet-700 inline-flex items-center gap-2"
                            >
                                View Analytics
                            </Link>
                        </div>
                    </div>

                    {/* Settings */}
                    <div className="bg-white border border-slate-200 rounded-xl p-5 flex flex-col">
                        <div className="flex items-center gap-3">
                            <div className="p-2 rounded-md bg-slate-100 text-slate-700">
                                <Settings className="h-5 w-5" />
                            </div>
                            <div>
                                <h3 className="font-medium text-slate-900">
                                    Settings
                                </h3>
                                <p className="text-sm text-slate-500">
                                    Team and workspace
                                </p>
                            </div>
                        </div>
                        <div className="mt-4">
                            <Link
                                href="/settings"
                                className="px-3 py-2 text-sm rounded-lg border border-slate-300 hover:bg-slate-50"
                            >
                                Open Settings
                            </Link>
                        </div>
                    </div>
                </div>
            </div>
        </DashboardLayout>
    );
}
