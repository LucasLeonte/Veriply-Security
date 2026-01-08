"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { DashboardLayout } from "@/components";
import { DashboardPreviewCard } from "@/components/DashboardPreviewCard";
import { InterventionTrendChart } from "@/components/InterventionTrendChart";
import { getAccessToken } from "@/lib/auth";
import { useGroup } from "@/contexts/GroupContext";
import { botsApi } from "@/lib/api/bots";
import { documentsApi } from "@/lib/api/documents";
import { useHITLQueue } from "@/hooks/useHITLQueue";
import type { ReviewQueueItem } from "@/hooks/useHITLQueue";
import { useAnalytics } from "@/hooks/useAnalytics";
import type { Bot } from "@/types/bot";
import type { Document as KBDocument } from "@/types/document";
import {
    Bot as BotIcon,
    Inbox,
    BookOpen,
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
    } = useHITLQueue("oldest", { groupId: currentGroup?.id });
    const { metrics, isLoading: analyticsLoading } = useAnalytics(
        currentGroup?.id
    );

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

                {/* KPI row */}
                <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
                    <div className="flex items-center gap-4 rounded-xl border border-slate-200 bg-white p-5">
                        <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-sky-100 text-sky-700">
                            <MessageSquare className="h-5 w-5" />
                        </div>
                        <div className="flex-1">
                            <p className="text-sm text-slate-500">
                                Conversations
                            </p>
                            <p className="text-2xl font-semibold text-slate-900">
                                {analyticsLoading
                                    ? "…"
                                    : metrics?.totalQueries ?? "—"}
                            </p>
                            <p className="text-xs text-slate-400 mt-1">
                                Total user queries
                            </p>
                        </div>
                    </div>
                    <div className="flex items-center gap-4 rounded-xl border border-slate-200 bg-white p-5">
                        <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-emerald-100 text-emerald-700">
                            <CheckCircle2 className="h-5 w-5" />
                        </div>
                        <div className="flex-1">
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
                            <p className="text-xs text-slate-400 mt-1">
                                Auto-resolved without review
                            </p>
                        </div>
                    </div>
                    <div className="flex items-center gap-4 rounded-xl border border-slate-200 bg-white p-5">
                        <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-rose-100 text-rose-700">
                            <AlertTriangle className="h-5 w-5" />
                        </div>
                        <div className="flex-1">
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
                            <p className="text-xs text-slate-400 mt-1">
                                Required human review
                            </p>
                        </div>
                    </div>
                    <div className="flex items-center gap-4 rounded-xl border border-slate-200 bg-white p-5">
                        <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-amber-100 text-amber-700">
                            <Clock className="h-5 w-5" />
                        </div>
                        <div className="flex-1">
                            <p className="text-sm text-slate-500">
                                Avg. Response
                            </p>
                            <p className="text-2xl font-semibold text-slate-900">
                                {analyticsLoading
                                    ? "…"
                                    : formatDuration(metrics?.avgResponseTime)}
                            </p>
                            <p className="text-xs text-slate-400 mt-1">
                                Time to generate answer
                            </p>
                        </div>
                    </div>
                </div>

                {/* Chart */}
                <div className="rounded-xl border border-slate-200 bg-white p-5">
                    <div className="flex items-center justify-between">
                        <div>
                            <h3 className="font-semibold text-slate-900">
                                Intervention Rate Trend
                            </h3>
                            <p className="text-sm text-slate-500">
                                Daily % of queries requiring human review
                            </p>
                        </div>
                        <Link
                            href="/analytics"
                            className="text-sm text-violet-700 hover:underline"
                        >
                            View full analytics
                        </Link>
                    </div>
                    <div className="mt-4">
                        {!metrics ||
                        analyticsLoading ||
                        !metrics.chartData?.length ? (
                            <div className="flex h-40 items-center justify-center text-slate-400 text-sm">
                                No data
                            </div>
                        ) : (
                            <InterventionTrendChart data={metrics.chartData} />
                        )}
                    </div>
                </div>

                {/* Analytics details: Rejection Reasons & Knowledge Gaps */}
                <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
                    <div className="rounded-xl border border-slate-200 bg-white p-5">
                        <div>
                            <h3 className="font-semibold text-slate-900">
                                Rejection Reasons
                            </h3>
                            <p className="text-sm text-slate-500 mt-1">
                                Why users rejected AI answers
                            </p>
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
                        <div>
                            <h3 className="font-semibold text-slate-900">
                                Top Knowledge Gaps
                            </h3>
                            <p className="text-sm text-slate-500 mt-1">
                                Questions with low confidence scores
                            </p>
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
                    <DashboardPreviewCard
                        icon={BotIcon}
                        iconBgColor="bg-sky-100"
                        iconTextColor="text-sky-700"
                        title="Bots"
                        description="Build and manage assistants"
                        totalCount={
                            botsTotal === null ? "—" : `${botsTotal} total`
                        }
                        actions={[
                            {
                                href: currentGroup ? "/dashboard/bots" : "#",
                                label: "Open Bots",
                                variant: "primary",
                                disabled: !currentGroup,
                                disabledHint: disabledHint || "",
                            },
                            {
                                href: currentGroup
                                    ? "/dashboard/bots?create=1"
                                    : "#",
                                label: "New Bot",
                                variant: "secondary",
                                disabled: !currentGroup,
                                disabledHint: disabledHint || "",
                            },
                        ]}
                        items={botsPreview}
                        keyExtractor={(b: Bot) => b.id}
                        renderItem={(b: Bot) => (
                            <div className="py-2 flex items-center justify-between">
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
                            </div>
                        )}
                    />

                    {/* Review Queue */}
                    <DashboardPreviewCard
                        icon={Inbox}
                        iconBgColor="bg-rose-100"
                        iconTextColor="text-rose-700"
                        title="Review Queue"
                        description="Low-confidence answers to triage"
                        totalCount={
                            queueLoading
                                ? "…"
                                : `${queueStats.pending ?? 0} pending`
                        }
                        actions={[
                            {
                                href: "/inbox",
                                label: "Open Queue",
                                variant: "primary",
                            },
                        ]}
                        items={queueItems?.slice(0, 3) ?? []}
                        keyExtractor={(q: ReviewQueueItem) => q.id}
                        renderItem={(q: ReviewQueueItem) => (
                            <div className="py-2 flex items-start gap-3">
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
                                        {Math.round((q.confidence ?? 0) * 100)}%
                                    </p>
                                </div>
                            </div>
                        )}
                    />

                    {/* Knowledge Base */}
                    <DashboardPreviewCard
                        icon={BookOpen}
                        iconBgColor="bg-emerald-100"
                        iconTextColor="text-emerald-700"
                        title="Knowledge Base"
                        description="Documents and sources"
                        totalCount={
                            docsTotal === null ? "—" : `${docsTotal} docs`
                        }
                        actions={[
                            {
                                href: currentGroup
                                    ? "/dashboard/knowledge-base"
                                    : "#",
                                label: "Open KB",
                                variant: "primary",
                                disabled: !currentGroup,
                                disabledHint: disabledHint || "",
                            },
                            {
                                href: currentGroup
                                    ? "/dashboard/knowledge-base?upload=1"
                                    : "#",
                                label: "Upload",
                                variant: "secondary",
                                disabled: !currentGroup,
                                disabledHint: disabledHint || "",
                            },
                        ]}
                        items={recentDocs}
                        keyExtractor={(d: KBDocument) => d.id}
                        renderItem={(d: KBDocument) => (
                            <div className="py-2 flex items-center justify-between">
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
                            </div>
                        )}
                    />
                </div>
            </div>
        </DashboardLayout>
    );
}
