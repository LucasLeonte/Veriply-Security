"use client";

import React from "react";
import { Bot } from "@/types/bot";
import { MoreVertical, FileText, Clock, Target } from "lucide-react";
import { format } from "date-fns";
import { useRouter } from "next/navigation";

interface BotCardProps {
    bot: Bot;
    onSettings?: (bot: Bot) => void;
    onDuplicate?: (bot: Bot) => void;
    onDelete?: (bot: Bot) => void;
}

export function BotCard({
    bot,
    onSettings,
    onDuplicate,
    onDelete,
}: BotCardProps) {
    const [showMenu, setShowMenu] = React.useState(false);
    const router = useRouter();

    const handleCardClick = (e: React.MouseEvent) => {
        // Don't navigate if clicking on the menu button or menu items
        if ((e.target as HTMLElement).closest('.menu-trigger') || 
            (e.target as HTMLElement).closest('.menu-content')) {
            return;
        }
        router.push(`/dashboard/bots/${bot.id}`);
    };

    return (
        <div 
            className="border rounded-lg p-4 hover:shadow-md transition-shadow cursor-pointer"
            onClick={handleCardClick}
        >
            <div className="flex justify-between items-start mb-3">
                <div className="flex-1">
                    <h3 className="font-semibold text-lg text-gray-900 hover:text-blue-600 cursor-pointer">
                        {bot.name}
                    </h3>
                    {bot.description && (
                        <p className="text-sm text-gray-600 line-clamp-2 mt-1">
                            {bot.description}
                        </p>
                    )}
                </div>

                <div className="relative">
                    <button
                        onClick={(e) => {
                            e.stopPropagation();
                            setShowMenu(!showMenu);
                        }}
                        className="p-1 hover:bg-gray-100 rounded menu-trigger"
                    >
                        <MoreVertical size={18} className="text-gray-500" />
                    </button>

                    {showMenu && (
                        <div className="absolute right-0 mt-1 w-48 bg-white border rounded shadow-md z-10 menu-content">
                            {onSettings && (
                                <button
                                    onClick={(e) => {
                                        e.stopPropagation();
                                        onSettings(bot);
                                        setShowMenu(false);
                                    }}
                                    className="block w-full text-left px-4 py-2 hover:bg-gray-100 text-sm"
                                >
                                    Settings
                                </button>
                            )}
                            {onDuplicate && (
                                <button
                                    onClick={(e) => {
                                        e.stopPropagation();
                                        onDuplicate(bot);
                                        setShowMenu(false);
                                    }}
                                    className="block w-full text-left px-4 py-2 hover:bg-gray-100 text-sm border-t"
                                >
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
                                    className="block w-full text-left px-4 py-2 hover:bg-red-50 text-red-600 text-sm border-t"
                                >
                                    Delete
                                </button>
                            )}
                        </div>
                    )}
                </div>
            </div>

            <div className="grid grid-cols-3 gap-2 text-sm text-gray-600 mt-4">
                <div className="flex items-center gap-1">
                    <FileText size={16} />
                    <span>{bot.doc_count ?? 0} docs</span>
                </div>
                <div className="flex items-center gap-1">
                    <Clock size={16} />
                    <span>
                        {bot.last_updated
                            ? format(new Date(bot.last_updated), "MMM d")
                            : "—"}
                    </span>
                </div>
                <div className="flex items-center gap-1">
                    <Target size={16} />
                    <span>{bot.confidence_threshold}%</span>
                </div>
            </div>

            <div className="mt-3 pt-3 border-t">
                <span className="inline-block px-2 py-1 text-xs font-semibold text-gray-600 bg-gray-100 rounded">
                    Status: {bot.status}
                </span>
            </div>
        </div>
    );
}
