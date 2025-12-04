"use client";

import React, { useState, useCallback, useEffect } from "react";
import { Plus, Search, AlertCircle, Loader } from "lucide-react";
import { BotCard } from "@/components/BotCard";
import { CreateBotModal } from "@/components/CreateBotModal";
import { BotSettingsModal } from "@/components/BotSettingsModal";
import { DuplicateBotModal } from "@/components/DuplicateBotModal";
import { DeleteBotModal } from "@/components/DeleteBotModal";
import { useBotsQuery } from "@/hooks/useBotsQuery";
import { DashboardLayout } from "@/components";
import { Bot } from "@/types/bot";

const ITEMS_PER_PAGE = 20;

export default function BotsPage() {
    const [page, setPage] = useState(0);
    const [search, setSearch] = useState("");
    const [sortBy, setSortBy] = useState<"name" | "created_at">("name");
    const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
    const [selectedBotId, setSelectedBotId] = useState<string | null>(null);
    const [isSettingsModalOpen, setIsSettingsModalOpen] = useState(false);
    const [isDuplicateModalOpen, setIsDuplicateModalOpen] = useState(false);
    const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);
    const [botForDuplicate, setBotForDuplicate] = useState<Bot | null>(null);
    const [botForDelete, setBotForDelete] = useState<Bot | null>(null);
    const [successMessage, setSuccessMessage] = useState("");
    const [errorMessage, setErrorMessage] = useState("");

    // Debounce search
    const [debouncedSearch, setDebouncedSearch] = useState(search);

    useEffect(() => {
        const timer = setTimeout(() => setDebouncedSearch(search), 300);
        return () => clearTimeout(timer);
    }, [search]);

    const offset = page * ITEMS_PER_PAGE;
    const { data, isLoading, error, refetch } = useBotsQuery(
        ITEMS_PER_PAGE,
        offset,
        debouncedSearch || undefined,
        sortBy
    );

    // Bot limit logic (assuming FREE tier = 5 bots for now)
    // TODO: Get actual subscription tier from user/tenant context
    const BOT_LIMIT = 5;
    const totalBots = data?.total_count || 0;
    const isAtBotLimit = totalBots >= BOT_LIMIT;

    const showMessage = useCallback(
        (msg: string, type: "success" | "error") => {
            if (type === "success") {
                setSuccessMessage(msg);
                setTimeout(() => setSuccessMessage(""), 3000);
            } else {
                setErrorMessage(msg);
                setTimeout(() => setErrorMessage(""), 3000);
            }
        },
        []
    );

    const handleCreateSuccess = (bot: Bot) => {
        showMessage(`Bot created: ${bot.name}`, "success");
        setPage(0);
        refetch();
    };

    const handleSettingsClick = (bot: Bot) => {
        setSelectedBotId(bot.id);
        setIsSettingsModalOpen(true);
    };

    const handleSettingsSave = () => {
        showMessage(`Settings updated`, "success");
        refetch();
    };

    const handleDuplicate = (bot: Bot) => {
        setBotForDuplicate(bot);
        setIsDuplicateModalOpen(true);
    };

    const handleDuplicateSuccess = (bot: Bot) => {
        showMessage(`Bot duplicated: ${bot.name}`, "success");
        setIsDuplicateModalOpen(false);
        setBotForDuplicate(null);
        refetch();
    };

    const handleDelete = (bot: Bot) => {
        setBotForDelete(bot);
        setIsDeleteModalOpen(true);
    };

    const handleDeleteSuccess = () => {
        showMessage(`Bot deleted successfully`, "success");
        setIsDeleteModalOpen(false);
        setBotForDelete(null);
        refetch();
    };

    const maxPage = data ? Math.ceil(data.total_count / ITEMS_PER_PAGE) : 0;

    return (
        <DashboardLayout>
            <div className="space-y-6">
                {/* Header */}
                <div className="mb-8">
                    <h1 className="text-3xl font-bold text-gray-900 mb-2">
                        Bots
                    </h1>
                    <p className="text-gray-600">
                        Manage your organization&apos;s bots and knowledge bases
                    </p>
                </div>

                {/* Messages */}
                {successMessage && (
                    <div className="mb-4 p-4 bg-green-50 border border-green-200 rounded text-green-700 flex items-center gap-2">
                        <div className="w-2 h-2 rounded-full bg-green-600" />
                        {successMessage}
                    </div>
                )}

                {errorMessage && (
                    <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded text-red-700 flex items-center gap-2">
                        <AlertCircle size={16} />
                        {errorMessage}
                    </div>
                )}

                {/* Controls */}
                <div className="bg-white rounded-lg shadow p-6 mb-6">
                    <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between mb-4">
                        <div className="flex-1">
                            <label htmlFor="search" className="sr-only">
                                Search bots
                            </label>
                            <div className="relative">
                                <Search
                                    className="absolute left-3 top-3 text-gray-400"
                                    size={20}
                                />
                                <input
                                    id="search"
                                    type="text"
                                    placeholder="Search bots by name..."
                                    value={search}
                                    onChange={(e) => {
                                        setSearch(e.target.value);
                                        setPage(0);
                                    }}
                                    className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                                />
                            </div>
                        </div>

                        <select
                            value={sortBy}
                            onChange={(e) => {
                                setSortBy(
                                    e.target.value as "name" | "created_at"
                                );
                                setPage(0);
                            }}
                            className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                        >
                            <option value="name">Sort by Name</option>
                            <option value="created_at">
                                Sort by Created Date
                            </option>
                        </select>

                        <button
                            onClick={() => setIsCreateModalOpen(true)}
                            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                            disabled={isLoading || isAtBotLimit}
                            title={
                                isAtBotLimit
                                    ? `Bot limit reached (${BOT_LIMIT} bots max)`
                                    : "Create a new bot"
                            }
                        >
                            <Plus size={20} />
                            Create Bot
                        </button>
                    </div>
                </div>

                {/* Content */}
                {isLoading && !data ? (
                    <div className="flex items-center justify-center py-12">
                        <Loader
                            className="animate-spin text-blue-600"
                            size={32}
                        />
                    </div>
                ) : error ? (
                    <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
                        <AlertCircle
                            className="mx-auto mb-2 text-red-600"
                            size={32}
                        />
                        <h3 className="font-semibold text-red-900 mb-2">
                            Failed to load bots
                        </h3>
                        <p className="text-red-700 mb-4">{error.message}</p>
                        <button
                            onClick={() => refetch()}
                            className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
                        >
                            Retry
                        </button>
                    </div>
                ) : !data || data.bots.length === 0 ? (
                    <div className="bg-white rounded-lg shadow p-12 text-center">
                        <h3 className="text-lg font-semibold text-gray-900 mb-2">
                            No bots found
                        </h3>
                        <p className="text-gray-600 mb-6">
                            {search
                                ? "No bots match your search"
                                : "Create your first bot to get started"}
                        </p>
                        {!search && (
                            <button
                                onClick={() => setIsCreateModalOpen(true)}
                                className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                            >
                                <Plus size={20} />
                                Create Your First Bot
                            </button>
                        )}
                    </div>
                ) : (
                    <>
                        {/* Bot Grid */}
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
                            {data.bots.map((bot) => (
                                <BotCard
                                    key={bot.id}
                                    bot={bot}
                                    onSettings={handleSettingsClick}
                                    onDuplicate={handleDuplicate}
                                    onDelete={handleDelete}
                                />
                            ))}
                        </div>

                        {/* Pagination */}
                        {maxPage > 1 && (
                            <div className="flex items-center justify-between bg-white rounded-lg shadow p-4">
                                <div className="text-sm text-gray-600">
                                    Showing {offset + 1}-
                                    {Math.min(
                                        offset + ITEMS_PER_PAGE,
                                        data.total_count
                                    )}{" "}
                                    of {data.total_count} bots
                                </div>

                                <div className="flex gap-2">
                                    <button
                                        onClick={() =>
                                            setPage((p) => Math.max(0, p - 1))
                                        }
                                        disabled={page === 0}
                                        className="px-3 py-1 border border-gray-300 rounded hover:bg-gray-50 disabled:opacity-50"
                                    >
                                        Previous
                                    </button>

                                    {/* Page Numbers */}
                                    <div className="flex gap-1">
                                        {Array.from({ length: maxPage }).map(
                                            (_, i) => (
                                                <button
                                                    key={i}
                                                    onClick={() => setPage(i)}
                                                    className={`px-3 py-1 rounded ${page === i
                                                        ? "bg-blue-600 text-white"
                                                        : "border border-gray-300 hover:bg-gray-50"
                                                        }`}
                                                >
                                                    {i + 1}
                                                </button>
                                            )
                                        )}
                                    </div>

                                    <button
                                        onClick={() =>
                                            setPage((p) =>
                                                Math.min(maxPage - 1, p + 1)
                                            )
                                        }
                                        disabled={page >= maxPage - 1}
                                        className="px-3 py-1 border border-gray-300 rounded hover:bg-gray-50 disabled:opacity-50"
                                    >
                                        Next
                                    </button>
                                </div>
                            </div>
                        )}
                    </>
                )}

                {/* Modals */}
                <CreateBotModal
                    isOpen={isCreateModalOpen}
                    onClose={() => setIsCreateModalOpen(false)}
                    onSuccess={handleCreateSuccess}
                    onError={(error) => showMessage(error, "error")}
                />

                {selectedBotId && (
                    <BotSettingsModal
                        botId={selectedBotId}
                        isOpen={isSettingsModalOpen}
                        onClose={() => {
                            setIsSettingsModalOpen(false);
                            setSelectedBotId(null);
                        }}
                        onSave={handleSettingsSave}
                        onError={(error) => showMessage(error, "error")}
                    />
                )}

                <DuplicateBotModal
                    isOpen={isDuplicateModalOpen}
                    bot={botForDuplicate}
                    onClose={() => {
                        setIsDuplicateModalOpen(false);
                        setBotForDuplicate(null);
                    }}
                    onSuccess={handleDuplicateSuccess}
                    onError={(error) => showMessage(error, "error")}
                />

                <DeleteBotModal
                    isOpen={isDeleteModalOpen}
                    bot={botForDelete}
                    onClose={() => {
                        setIsDeleteModalOpen(false);
                        setBotForDelete(null);
                    }}
                    onSuccess={handleDeleteSuccess}
                    onError={(error) => showMessage(error, "error")}
                />
            </div>
        </DashboardLayout>
    );
}
