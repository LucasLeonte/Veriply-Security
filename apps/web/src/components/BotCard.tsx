"use client";

import React from "react";
import { Bot } from "@/types/bot";
import { MoreVertical, FileText, Target, Copy, Trash2 } from "lucide-react";
import { format } from "date-fns";
import { useRouter } from "next/navigation";

interface BotCardProps {
    bot: Bot;
    onDuplicate?: (bot: Bot) => void;
    onDelete?: (bot: Bot) => void;
}

export function BotCard({
    bot,
    onDuplicate,
    onDelete,
}: BotCardProps) {
    const [showMenu, setShowMenu] = React.useState(false);
    const router = useRouter();

    const handleCardClick = (e: React.MouseEvent) => {
        // Don't navigate if clicking on the menu button or menu items
        if (
            (e.target as HTMLElement).closest(".menu-trigger") ||
            (e.target as HTMLElement).closest(".menu-content")
        ) {
            return;
        }
        router.push(`/dashboard/bots/${bot.id}`);
    };

    const getStatusBadge = (isActive?: boolean) => {
        if (isActive) {
            return "bg-emerald-100 text-emerald-700 border-emerald-200";
        } else {
            return "bg-slate-100 text-slate-600 border-slate-200";
        }
    };

    const getStatusText = (isActive?: boolean) => {
        return isActive ? "Active" : "Inactive";
    };

    return (
        <div
            className="group bg-white rounded-xl border border-slate-200 hover:border-sky-200 hover:shadow-lg transition-all duration-200 cursor-pointer overflow-hidden"
            onClick={handleCardClick}
        >
            {/* Header with Avatar and Menu */}
            <div className="p-6 pb-4">
                <div className="flex items-start gap-4">
                    {/* Avatar */}
                    <div className="flex-shrink-0">
                        <div className="h-14 w-14 rounded-lg bg-gradient-to-br from-sky-100 to-emerald-100 border-2 border-white shadow-md flex items-center justify-center">
                            {bot.avatar_url ? (
                                // eslint-disable-next-line @next/next/no-img-element
                                <img
                                    src={bot.avatar_url}
                                    alt={bot.name}
                                    className="h-full w-full object-cover rounded-lg"
                                />
                            ) : (
                                <span className="text-xl font-bold text-sky-600">
                                    {bot.name?.charAt(0)?.toUpperCase() || "B"}
                                </span>
                            )}
                        </div>
                    </div>

                    {/* Name and Description */}
                    <div className="flex-1 min-w-0">
                        <h3 className="font-semibold text-lg text-slate-900 group-hover:text-sky-600 transition-colors truncate">
                            {bot.name}
                        </h3>
                        {bot.description && (
                            <p className="text-sm text-slate-600 line-clamp-2 mt-1">
                                {bot.description}
                            </p>
                        )}
                    </div>

                    {/* Menu */}
                    <div className="relative flex-shrink-0">
                        <button
                            onClick={(e) => {
                                e.stopPropagation();
                                setShowMenu(!showMenu);
                            }}
                            className="p-2 hover:bg-slate-100 rounded-lg transition-colors menu-trigger"
                        >
                            <MoreVertical size={18} className="text-slate-500" />
                        </button>

                        {showMenu && (
                            <div className="absolute right-0 mt-2 w-48 bg-white border border-slate-200 rounded-lg shadow-lg z-10 menu-content overflow-hidden">
                                <button
                                    onClick={(e) => {
                                        e.stopPropagation();
                                        router.push(`/dashboard/bots/${bot.id}?tab=settings`);
                                        setShowMenu(false);
                                    }}
                                    className="flex items-center gap-2 w-full text-left px-4 py-2.5 hover:bg-slate-50 text-sm text-slate-700 transition-colors"
                                >
                                    <svg
                                        xmlns="http://www.w3.org/2000/svg"
                                        width="16"
                                        height="16"
                                        viewBox="0 0 24 24"
                                        fill="none"
                                        stroke="currentColor"
                                        strokeWidth="2"
                                        strokeLinecap="round"
                                        strokeLinejoin="round"
                                    >
                                        <path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z" />
                                        <circle cx="12" cy="12" r="3" />
                                    </svg>
                                    Settings
                                </button>
                                {onDuplicate && (
                                    <button
                                        onClick={(e) => {
                                            e.stopPropagation();
                                            onDuplicate(bot);
                                            setShowMenu(false);
                                        }}
                                        className="flex items-center gap-2 w-full text-left px-4 py-2.5 hover:bg-slate-50 text-sm text-slate-700 border-t border-slate-100 transition-colors"
                                    >
                                        <Copy size={16} />
                                        Duplicate
                                    </button>
                                )}
                                {onDelete && (
                                    <button
                                        onClick={(e) => {
                                            e.stopPropagation();
                                            onDelete(bot);
                                            setShowMenu(false);
                                        }}
                                        className="flex items-center gap-2 w-full text-left px-4 py-2.5 hover:bg-red-50 text-sm text-red-600 border-t border-slate-100 transition-colors"
                                    >
                                        <Trash2 size={16} />
                                        Delete
                                    </button>
                                )}
                            </div>
                        )}
                    </div>
                </div>
            </div>

            {/* Stats */}
            <div className="px-6 pb-4">
                <div className="flex items-center gap-4 text-sm">
                    <div className="flex items-center gap-1.5 text-slate-600">
                        <FileText size={16} className="text-slate-400" />
                        <span className="font-medium">{bot.doc_count ?? 0}</span>
                        <span className="text-slate-500">docs</span>
                    </div>
                    <div className="flex items-center gap-1.5 text-slate-600">
                        <Target size={16} className="text-slate-400" />
                        <span className="font-medium">{bot.confidence_threshold}%</span>
                    </div>
                </div>
            </div>

            {/* Footer */}
            <div className="px-6 py-3 bg-slate-50 border-t border-slate-100 flex items-center justify-between">
                <span className={`inline-flex items-center px-2.5 py-1 text-xs font-medium rounded-md border ${getStatusBadge(bot.is_active)}`}>
                    {getStatusText(bot.is_active)}
                </span>
                <span className="text-xs text-slate-500">
                    {bot.last_updated
                        ? format(new Date(bot.last_updated), "MMM d, yyyy")
                        : bot.created_at
                            ? format(new Date(bot.created_at), "MMM d, yyyy")
                            : "Recently"}
                </span>
            </div>
        </div>
    );
}
