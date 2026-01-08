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
import type { Bot } from "@/types/bot";
import type { Document as KBDocument } from "@/types/document";
import {
    Bot as BotIcon,
    Inbox,
    BookOpen,
    Mail,
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
    const [botsPreview, setBotsPreview] = useState<Bot[]>([]);
    const [docsTotal, setDocsTotal] = useState<number | null>(null);
    const [recentDocs, setRecentDocs] = useState<KBDocument[]>([]);
    const {
        stats: queueStats,
        isLoading: queueLoading,
        items: queueItems,
    } = useHITLQueue("oldest");
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
                setBotsPreview([]);
                setRecentDocs([]);
                return;
            }
            try {
                const botsRes = await botsApi.listBots(currentGroup.id, 3, 0);
                setBotsTotal(botsRes.total_count ?? botsRes.bots.length);
                setBotsPreview(
                    (botsRes.bots || [])
                        .slice(0, 3)
                        .sort((a, b) =>
                            (b.updated_at || "").localeCompare(
                                a.updated_at || ""
                            )
                        )
                );
            } catch {
                setBotsTotal(null);
                setBotsPreview([]);
            }
            try {
                const docsRes = await documentsApi.listDocuments(
                    currentGroup.id,
                    1,
                    3
                );
                setDocsTotal(docsRes.total);
                setRecentDocs((docsRes.documents || []).slice(0, 3));
            } catch {
                setDocsTotal(null);
                setRecentDocs([]);
            }
        })();
    }, [currentGroup?.id]);

    const disabledHint = useMemo(
        () => !currentGroup && "Select a group to manage resources",
        [currentGroup]
    );

    const timeAgo = (iso?: string) => {
        if (!iso) return "";
        const t = new Date(iso).getTime();
        if (Number.isNaN(t)) return "";
        const diff = Math.max(0, Date.now() - t) / 1000;
        if (diff < 60) return `${Math.floor(diff)}s ago`;
        if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
        if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
        return `${Math.floor(diff / 86400)}d ago`;
    };

    const statusBadge = (status?: string) => {
        const s = (status || "").toLowerCase();
        if (s === "ready") return "bg-emerald-100 text-emerald-700";
        if (s === "processing") return "bg-amber-100 text-amber-700";
        if (s === "uploading") return "bg-sky-100 text-sky-700";
        if (s === "failed" || s === "error") return "bg-rose-100 text-rose-700";
        return "bg-slate-100 text-slate-600";
    };

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
                                            const h = 120;
                                            const padTop = 20;
                                            const xStep =
                                                n > 1 ? w / (n - 1) : w;
                                            const toY = (v: number) =>
                                                padTop +
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
                                                <path
                                                    d={d}
                                                    stroke="#7c3aed"
                                                    strokeWidth="2"
                                                    fill="none"
                                                    strokeLinecap="round"
                                                />
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

                {/* Analytics details: Rejection Reasons & Knowledge Gaps */}
                <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
                    <div className="rounded-xl border border-slate-200 bg-white p-5">
                        <div className="flex items-center justify-between">
                            <h3 className="font-semibold text-slate-900">
                                Rejection Reasons
                            </h3>
                        </div>
                        <div className="mt-4 space-y-3">
                            {!metrics ||
                            analyticsLoading ||
                            !metrics.rejectionReasons?.length ? (
                                <div className="text-sm text-slate-400">
                                    No data
                                </div>
                            ) : (
                                metrics.rejectionReasons
                                    .slice(0, 4)
                                    .map((r) => (
                                        <div key={r.reason}>
                                            <div className="flex items-center justify-between text-sm">
                                                <span
                                                    className="text-slate-700 truncate pr-2"
                                                    title={r.reason}
                                                >
                                                    {r.reason}
                                                </span>
                                                <span className="text-slate-500">
                                                    {r.count} •{" "}
                                                    {r.percent.toFixed(1)}%
                                                </span>
                                            </div>
                                            <div className="mt-1 h-2 w-full rounded-full bg-slate-100">
                                                <div
                                                    className="h-2 rounded-full bg-rose-500"
                                                    style={{
                                                        width: `${Math.max(
                                                            0,
                                                            Math.min(
                                                                100,
                                                                r.percent
                                                            )
                                                        )}%`,
                                                    }}
                                                />
                                            </div>
                                        </div>
                                    ))
                            )}
                        </div>
                    </div>
                    <div className="rounded-xl border border-slate-200 bg-white p-5">
                        <div className="flex items-center justify-between">
                            <h3 className="font-semibold text-slate-900">
                                Top Knowledge Gaps
                            </h3>
                        </div>
                        <ul className="mt-4 divide-y divide-slate-100">
                            {!metrics ||
                            analyticsLoading ||
                            !metrics.knowledgeGaps?.length ? (
                                <li className="py-1 text-sm text-slate-400">
                                    No data
                                </li>
                            ) : (
                                metrics.knowledgeGaps.slice(0, 4).map((k) => (
                                    <li key={k.question} className="py-2">
                                        <p
                                            className="text-sm text-slate-900 truncate"
                                            title={k.question}
                                        >
                                            {k.question}
                                        </p>
                                        <p className="text-xs text-slate-500">
                                            Asked {k.askCount}×
                                        </p>
                                    </li>
                                ))
                            )}
                        </ul>
                    </div>
                </div>

                {/* Section previews */}
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
                        {!!botsPreview.length && (
                            <ul className="mt-4 divide-y divide-slate-100">
                                {botsPreview.map((b) => (
                                    <li
                                        key={b.id}
                                        className="py-2 flex items-center justify-between"
                                    >
                                        <div className="min-w-0">
                                            <p className="text-sm font-medium text-slate-900 truncate">
                                                {b.name}
                                            </p>
                                            <p className="text-xs text-slate-500 truncate">
                                                Updated {timeAgo(b.updated_at)}
                                                {b.doc_count
                                                    ? ` • ${b.doc_count} docs`
                                                    : ""}
                                            </p>
                                        </div>
                                        <span
                                            className={`text-xs px-2 py-1 rounded-full ${statusBadge(
                                                b.status
                                            )}`}
                                        >
                                            {b.status}
                                        </span>
                                    </li>
                                ))}
                            </ul>
                        )}
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
                        {!!queueItems?.length && (
                            <ul className="mt-4 divide-y divide-slate-100">
                                {queueItems.slice(0, 3).map((q) => (
                                    <li
                                        key={q.id}
                                        className="py-2 flex items-start gap-3"
                                    >
                                        <span
                                            className={`mt-1 inline-flex items-center justify-center h-6 w-6 rounded-full text-xs ${
                                                q.type === "email"
                                                    ? "bg-indigo-100 text-indigo-700"
                                                    : "bg-sky-100 text-sky-700"
                                            }`}
                                        >
                                            {q.type === "email" ? "E" : "C"}
                                        </span>
                                        <div className="min-w-0 flex-1">
                                            <p
                                                className="text-sm text-slate-900 truncate"
                                                title={q.userQuestion}
                                            >
                                                {q.userQuestion}
                                            </p>
                                            <p className="text-xs text-slate-500">
                                                {timeAgo(q.timestamp)} • conf{" "}
                                                {Math.round(
                                                    (q.confidence ?? 0) * 100
                                                )}
                                                %
                                            </p>
                                        </div>
                                    </li>
                                ))}
                            </ul>
                        )}
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
                        {!!recentDocs.length && (
                            <ul className="mt-4 divide-y divide-slate-100">
                                {recentDocs.map((d) => (
                                    <li
                                        key={d.id}
                                        className="py-2 flex items-center justify-between"
                                    >
                                        <div className="min-w-0">
                                            <p
                                                className="text-sm text-slate-900 truncate"
                                                title={d.title || d.filename}
                                            >
                                                {d.title || d.filename}
                                            </p>
                                            <p className="text-xs text-slate-500 truncate">
                                                Updated {timeAgo(d.updated_at)}
                                            </p>
                                        </div>
                                        <span
                                            className={`text-xs px-2 py-1 rounded-full ${statusBadge(
                                                d.status
                                            )}`}
                                        >
                                            {d.status}
                                        </span>
                                    </li>
                                ))}
                            </ul>
                        )}
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
                        {queueItems?.some((q) => q.type === "email") && (
                            <ul className="mt-4 divide-y divide-slate-100">
                                {queueItems
                                    .filter((q) => q.type === "email")
                                    .slice(0, 2)
                                    .map((q) => (
                                        <li
                                            key={q.id}
                                            className="py-2 flex items-start gap-3"
                                        >
                                            <span className="mt-1 inline-flex items-center justify-center h-6 w-6 rounded-full text-xs bg-indigo-100 text-indigo-700">
                                                E
                                            </span>
                                            <div className="min-w-0 flex-1">
                                                <p
                                                    className="text-sm text-slate-900 truncate"
                                                    title={q.userQuestion}
                                                >
                                                    {q.userQuestion}
                                                </p>
                                                <p className="text-xs text-slate-500">
                                                    {timeAgo(q.timestamp)}
                                                </p>
                                            </div>
                                        </li>
                                    ))}
                            </ul>
                        )}
                    </div>
                </div>
            </div>
        </DashboardLayout>
    );
}
