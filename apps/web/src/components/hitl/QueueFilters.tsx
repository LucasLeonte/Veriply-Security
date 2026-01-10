"use client";

import React, { useState, useEffect } from "react";
import { Filter as FilterIcon, X, Calendar } from "lucide-react";
import { Button } from "@/components/ui/button";

export interface FilterState {
    botId?: string;
    dateFrom?: string;
    dateTo?: string;
    status?: "pending" | "in-progress";
}

interface Bot {
    id: string;
    name: string;
}

interface QueueFiltersProps {
    filters: FilterState;
    onFiltersChange: (filters: FilterState) => void;
    onClose?: () => void;
}

export function QueueFilters({
    filters,
    onFiltersChange,
    onClose,
}: QueueFiltersProps) {
    const [bots, setBots] = useState<Bot[]>([]);
    const [isLoadingBots, setIsLoadingBots] = useState(true);

    // Fetch bots for dropdown (AC 5.5)
    useEffect(() => {
        const fetchBots = async () => {
            try {
                const response = await fetch("/api/hitl/bots");
                if (response.ok) {
                    const data = await response.json();
                    setBots(data.bots || []);
                }
            } catch (error) {
                
            } finally {
                setIsLoadingBots(false);
            }
        };
        fetchBots();
    }, []);

    const handleFilterChange = (key: keyof FilterState, value: string) => {
        onFiltersChange({
            ...filters,
            [key]: value || undefined,
        });
    };

    const clearFilters = () => {
        onFiltersChange({});
    };

    const activeFilterCount = Object.values(filters).filter(Boolean).length;

    return (
        <div className="bg-white rounded-lg border border-slate-200 shadow-lg p-4">
            <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                    <FilterIcon className="w-4 h-4 text-slate-600" />
                    <h3 className="text-sm font-semibold text-slate-900">
                        Filters
                    </h3>
                    {activeFilterCount > 0 && (
                        <span className="px-2 py-0.5 text-xs font-medium bg-sky-100 text-sky-700 rounded-full">
                            {activeFilterCount} active
                        </span>
                    )}
                </div>
                {onClose && (
                    <button
                        onClick={onClose}
                        className="text-slate-400 hover:text-slate-600"
                    >
                        <X className="w-4 h-4" />
                    </button>
                )}
            </div>

            <div className="space-y-4">
                {/* Bot Filter */}
                <div>
                    <label className="block text-xs font-medium text-slate-700 mb-1.5">
                        Bot
                    </label>
                    <select
                        value={filters.botId || ""}
                        onChange={(e) =>
                            handleFilterChange("botId", e.target.value)
                        }
                        className="w-full px-3 py-2 text-sm border border-slate-300 rounded-md focus:outline-none focus:ring-2 focus:ring-sky-500 focus:border-sky-500"
                        disabled={isLoadingBots}
                    >
                        <option value="">All Bots</option>
                        {bots.map((bot) => (
                            <option key={bot.id} value={bot.id}>
                                {bot.name}
                            </option>
                        ))}
                    </select>
                </div>

                {/* Date Range Filter */}
                <div>
                    <label className="block text-xs font-medium text-slate-700 mb-1.5">
                        Date Range
                    </label>
                    <div className="grid grid-cols-2 gap-2">
                        <div>
                            <label className="block text-xs text-slate-500 mb-1">
                                From
                            </label>
                            <input
                                type="date"
                                value={filters.dateFrom || ""}
                                onChange={(e) =>
                                    handleFilterChange(
                                        "dateFrom",
                                        e.target.value
                                    )
                                }
                                className="w-full px-3 py-2 text-sm border border-slate-300 rounded-md focus:outline-none focus:ring-2 focus:ring-sky-500 focus:border-sky-500"
                            />
                        </div>
                        <div>
                            <label className="block text-xs text-slate-500 mb-1">
                                To
                            </label>
                            <input
                                type="date"
                                value={filters.dateTo || ""}
                                onChange={(e) =>
                                    handleFilterChange("dateTo", e.target.value)
                                }
                                className="w-full px-3 py-2 text-sm border border-slate-300 rounded-md focus:outline-none focus:ring-2 focus:ring-sky-500 focus:border-sky-500"
                            />
                        </div>
                    </div>
                </div>

                {/* Status Filter */}
                <div>
                    <label className="block text-xs font-medium text-slate-700 mb-1.5">
                        Status
                    </label>
                    <select
                        value={filters.status || ""}
                        onChange={(e) =>
                            handleFilterChange(
                                "status",
                                e.target.value as "pending" | "in-progress" | ""
                            )
                        }
                        className="w-full px-3 py-2 text-sm border border-slate-300 rounded-md focus:outline-none focus:ring-2 focus:ring-sky-500 focus:border-sky-500"
                    >
                        <option value="">All Statuses</option>
                        <option value="pending">Pending</option>
                        <option value="in-progress">In Progress</option>
                    </select>
                </div>

                {/* Actions */}
                {activeFilterCount > 0 && (
                    <div className="pt-2 border-t border-slate-200">
                        <Button
                            onClick={clearFilters}
                            variant="outline"
                            size="sm"
                            className="w-full"
                        >
                            Clear All Filters
                        </Button>
                    </div>
                )}
            </div>
        </div>
    );
}
