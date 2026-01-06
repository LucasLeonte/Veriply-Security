"use client";

import React from "react";
import { AnalyticsMetrics } from "@/hooks/useAnalytics";

interface AnalyticsDashboardProps {
    metrics: AnalyticsMetrics | null;
    isLoading: boolean;
}

export function AnalyticsDashboard({
    metrics,
    isLoading,
}: AnalyticsDashboardProps) {
    if (isLoading) {
        return (
            <div className="flex items-center justify-center p-8">
                <div className="text-slate-600">Loading analytics...</div>
            </div>
        );
    }

    if (!metrics) {
        return (
            <div className="flex items-center justify-center p-8">
                <div className="text-slate-600">
                    No analytics data available
                </div>
            </div>
        );
    }

    return (
        <div className="max-w-7xl mx-auto p-6">
            {/* Header */}
            <div className="mb-8">
                <h1 className="text-2xl font-semibold text-slate-900">
                    Analytics HARDCODED
                </h1>
                <p className="text-slate-500 mt-1">
                    Track your AI performance and team productivity
                </p>
            </div>

            {/* Stats Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
                <div className="bg-white rounded-xl p-5 border border-slate-200">
                    <p className="text-sm text-slate-500 mb-1">Total Queries</p>
                    <p className="text-2xl font-semibold text-slate-900">
                        {metrics.totalQueries.toLocaleString()}
                    </p>
                    <p className="text-xs text-slate-500 mt-2">
                        All-time metric
                    </p>
                </div>
                <div className="bg-white rounded-xl p-5 border border-slate-200">
                    <p className="text-sm text-slate-500 mb-1">Auto-Resolved</p>
                    <p className="text-2xl font-semibold text-slate-900">
                        {metrics.autoResolvedPercent}%
                    </p>
                    <p className="text-xs text-green-600 mt-2">
                        ↑ Excellent performance
                    </p>
                </div>
                <div className="bg-white rounded-xl p-5 border border-slate-200">
                    <p className="text-sm text-slate-500 mb-1">
                        Avg Response Time
                    </p>
                    <p className="text-2xl font-semibold text-slate-900">
                        {metrics.avgResponseTime.toFixed(2)}s
                    </p>
                    <p className="text-xs text-slate-500 mt-2">Within target</p>
                </div>
                <div className="bg-white rounded-xl p-5 border border-slate-200">
                    <p className="text-sm text-slate-500 mb-1">Trust Score</p>
                    <p className="text-2xl font-semibold text-slate-900">
                        {metrics.trustScore}%
                    </p>
                    <p className="text-xs text-green-600 mt-2">👍 Excellent</p>
                </div>
            </div>

            {/* Charts Row */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
                {/* HITL Rate Chart */}
                <div className="bg-white rounded-xl p-6 border border-slate-200">
                    <div className="flex items-center justify-between mb-6">
                        <h3 className="font-medium text-slate-900">
                            HITL Intervention Rate
                        </h3>
                        <select className="text-sm border-0 text-slate-500 focus:ring-0 bg-transparent cursor-pointer">
                            <option>Last 7 days</option>
                            <option>Last 30 days</option>
                            <option>Last 90 days</option>
                        </select>
                    </div>
                    {/* Bar Chart */}
                    <div className="h-48 flex items-end gap-2">
                        {metrics.chartData.map((data, idx) => (
                            <div key={idx} className="flex-1 relative">
                                <div
                                    className="w-full bg-sky-500 rounded-t"
                                    style={{
                                        height: `${Math.max(
                                            data.interventionRate * 3,
                                            5
                                        )}px`,
                                    }}
                                    title={`${data.period}: ${data.interventionRate}%`}
                                />
                            </div>
                        ))}
                    </div>
                    <p className="text-sm text-slate-500 mt-4 text-center">
                        AI is learning! Intervention rate down from{" "}
                        {metrics.chartData[0]?.interventionRate}% to{" "}
                        {
                            metrics.chartData[metrics.chartData.length - 1]
                                ?.interventionRate
                        }
                        %
                    </p>
                </div>

                {/* Rejection Reasons */}
                <div className="bg-white rounded-xl p-6 border border-slate-200">
                    <h3 className="font-medium text-slate-900 mb-6">
                        Rejection Reasons
                    </h3>
                    <div className="space-y-4">
                        {metrics.rejectionReasons.map((reason, idx) => (
                            <div key={idx}>
                                <div className="flex items-center justify-between mb-2">
                                    <span className="text-sm text-slate-700">
                                        {reason.reason}
                                    </span>
                                    <span className="text-sm font-medium text-slate-900">
                                        {reason.percent}%
                                    </span>
                                </div>
                                <div className="w-full bg-slate-200 rounded-full h-2">
                                    <div
                                        className="bg-orange-500 h-2 rounded-full"
                                        style={{ width: `${reason.percent}%` }}
                                    />
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            </div>

            {/* Knowledge Gaps */}
            <div className="bg-white rounded-xl p-6 border border-slate-200">
                <div className="flex items-center justify-between mb-4">
                    <h3 className="font-medium text-slate-900">
                        Unanswered Questions (Knowledge Gaps)
                    </h3>
                    <button className="text-sm text-sky-600 hover:text-sky-700 font-medium">
                        View all
                    </button>
                </div>
                <div className="space-y-3">
                    {metrics.knowledgeGaps.map((gap, idx) => (
                        <div
                            key={idx}
                            className="flex items-center justify-between p-3 bg-slate-50 rounded-lg"
                        >
                            <span className="text-sm text-slate-700">
                                &quot;{gap.question}&quot;
                            </span>
                            <span className="text-xs text-slate-500">
                                Asked {gap.askCount} time
                                {gap.askCount !== 1 ? "s" : ""}
                            </span>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
}
