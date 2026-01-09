"use client";

import type { AnalyticsMetrics } from "@/hooks/useAnalytics";

interface InterventionTrendChartProps {
    data: AnalyticsMetrics["chartData"]; // Array of { period, interventionRate }
}

export function InterventionTrendChart({ data }: InterventionTrendChartProps) {
    // Render a fixed-height chart area with positioned labels and SVG
    return (
        <div className="h-40 relative">
            {/* Y-axis labels positioned absolutely */}
            <div className="absolute left-0 top-[12.5%] -translate-y-1/2 text-xs text-slate-400 font-medium">
                100%
            </div>
            <div className="absolute left-0 top-1/2 -translate-y-1/2 text-xs text-slate-400 font-medium">
                50%
            </div>
            <div className="absolute left-0 bottom-[12.5%] translate-y-1/2 text-xs text-slate-400 font-medium">
                0%
            </div>

            <svg
                className="w-full h-full"
                viewBox="0 0 400 160"
                preserveAspectRatio="none"
                style={{ marginLeft: "32px" }}
            >
                {(() => {
                    const pts = data;
                    const n = pts.length;
                    const w = 390; // Reduced from 400 to add padding
                    const h = 120;
                    const padTop = 20;
                    const padLeft = 5; // Small left padding
                    const xStep =
                        n > 1 ? (w - padLeft * 2) / (n - 1) : w - padLeft * 2;
                    const clamp01 = (v: number) =>
                        Math.max(0, Math.min(100, v));
                    const toY = (v: number) =>
                        padTop + (h - (clamp01(v) / 100) * h);
                    const d = pts
                        .map((p, i) => {
                            const x = padLeft + i * xStep;
                            const y = toY(p.interventionRate);
                            return `${i === 0 ? "M" : "L"} ${x} ${y}`;
                        })
                        .join(" ");
                    return (
                        <>
                            {/* Grid lines */}
                            <line
                                x1={0}
                                y1={padTop}
                                x2={400}
                                y2={padTop}
                                stroke="#e2e8f0"
                                strokeWidth="1"
                                strokeDasharray="2,2"
                            />
                            <line
                                x1={0}
                                y1={padTop + h / 2}
                                x2={400}
                                y2={padTop + h / 2}
                                stroke="#e2e8f0"
                                strokeWidth="1"
                                strokeDasharray="2,2"
                            />
                            <line
                                x1={0}
                                y1={padTop + h}
                                x2={400}
                                y2={padTop + h}
                                stroke="#e2e8f0"
                                strokeWidth="1"
                                strokeDasharray="2,2"
                            />
                            {/* Line chart */}
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
        </div>
    );
}
