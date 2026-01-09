"use client";

import { useState, useEffect, useRef } from "react";
import { Card } from "../../../../../../../components/ui/card";
import { Button } from "../../../../../../../components/ui/button";
import { Input } from "../../../../../../../components/ui/input";
import { useToast } from "../../../../../../../hooks/useToast";
import { getAccessToken } from "../../../../../../../lib/auth";
import {
    Copy,
    Check,
    Settings2,
    ArrowLeft,
    MessageCircle,
    FileText,
    Settings,
    Clock3,
} from "lucide-react";
import Link from "next/link";
import ChatInterface from "../../../../../../../components/chat/ChatInterface";
import { Bot } from "../../../../../../../types/bot";
import { botsApi } from "../../../../../../../lib/api/bots";

interface WidgetConfig {
    bot_id: string;
    position: "bottom-right" | "bottom-left" | "top-right" | "top-left";
    primary_color: string;
    welcome_message: string | null;
    auto_open: boolean;
    allowed_domains: string[];
}

const POSITIONS = [
    { value: "bottom-right", label: "Bottom Right" },
    { value: "bottom-left", label: "Bottom Left" },
    { value: "top-right", label: "Top Right" },
    { value: "top-left", label: "Top Left" },
];

const DOMAIN_REGEX =
    /^(\*\.)?[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$/;
const LOCALHOST_REGEX = /^(localhost|127\.0\.0\.1)$/;
const MAX_DOMAINS = 50;

const normalizeDomain = (value: string): string => {
    let candidate = value.trim().toLowerCase();
    if (candidate.startsWith("http://") || candidate.startsWith("https://")) {
        try {
            const parsed = new URL(candidate);
            candidate = parsed.hostname;
        } catch {
            // leave as-is if URL parsing fails
        }
    }
    candidate = candidate.replace(/\/$/, "");
    if (candidate.includes(":")) {
        candidate = candidate.split(":")[0];
    }
    return candidate;
};

const validateDomainInput = (
    raw: string,
    existing: string[],
    editingIndex: number | null
): string | null => {
    const candidate = normalizeDomain(raw);
    if (!candidate) return "Invalid domain format";
    if (!DOMAIN_REGEX.test(candidate) && !LOCALHOST_REGEX.test(candidate)) {
        return "Invalid domain format";
    }

    const existingNormalized = existing.map((d) => normalizeDomain(d));
    const duplicateIndex = existingNormalized.findIndex((d) => d === candidate);
    const isDuplicate =
        duplicateIndex !== -1 && duplicateIndex !== editingIndex;
    if (isDuplicate) {
        return "Domain already in whitelist";
    }

    if (existing.length >= MAX_DOMAINS && editingIndex === null) {
        return `Maximum ${MAX_DOMAINS} domains allowed`;
    }

    return null;
};

export function WidgetConfigClient({
    groupId,
    botId,
    hideNav = false,
}: {
    groupId: string;
    botId: string;
    hideNav?: boolean;
}) {
    const [config, setConfig] = useState<WidgetConfig | null>(null);
    const [bot, setBot] = useState<Bot | null>(null);
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [copied, setCopied] = useState(false);
    const [paramError, setParamError] = useState<string | null>(null);
    const [domainInput, setDomainInput] = useState("");
    const [domainError, setDomainError] = useState<string | null>(null);
    const [editingIndex, setEditingIndex] = useState<number | null>(null);
    const { toast } = useToast();

    // Load current config
    useEffect(() => {
        if (
            !groupId ||
            groupId === "undefined" ||
            !botId ||
            botId === "undefined"
        ) {
            setParamError("Missing group or bot id");
            setLoading(false);
            return;
        }

        const fetchConfig = async () => {
            try {
                const token = getAccessToken();

                // Fetch widget config
                const configResponse = await fetch(
                    `/api/widget-config?groupId=${groupId}&botId=${botId}`,
                    {
                        credentials: "include",
                        headers: token
                            ? { Authorization: `Bearer ${token}` }
                            : undefined,
                    }
                );

                // Fetch bot details using API helper
                const botData = await botsApi.getBotDetails(groupId, botId);

                if (configResponse.ok) {
                    const configData = await configResponse.json();
                    setConfig({
                        ...configData,
                        allowed_domains: configData.allowed_domains || [],
                    });
                    setBot(botData);
                } else {
                    toast({
                        title: "Error",
                        description: "Failed to load widget config",
                        variant: "error",
                    });
                }
            } catch (error) {
                console.error("Failed to fetch config:", error);
                toast({
                    title: "Error",
                    description: "Failed to load widget config or bot details",
                    variant: "error",
                });
            } finally {
                setLoading(false);
            }
        };
        fetchConfig();
    }, [groupId, botId]);

    const handleSave = async () => {
        if (!config) return;
        if (
            !groupId ||
            groupId === "undefined" ||
            !botId ||
            botId === "undefined"
        ) {
            toast({
                title: "Missing parameters",
                description: "Group or bot id is missing.",
                variant: "error",
            });
            return;
        }
        setSaving(true);
        try {
            const token = getAccessToken();
            const response = await fetch(
                `/api/widget-config?groupId=${groupId}&botId=${botId}`,
                {
                    method: "PUT",
                    headers: {
                        "Content-Type": "application/json",
                        ...(token ? { Authorization: `Bearer ${token}` } : {}),
                    },
                    credentials: "include",
                    body: JSON.stringify({
                        position: config.position,
                        primary_color: config.primary_color,
                        auto_open: config.auto_open,
                        allowed_domains: config.allowed_domains,
                    }),
                }
            );
            if (response.ok) {
                const updated = await response.json();
                setConfig({
                    ...updated,
                    allowed_domains: updated.allowed_domains || [],
                });
                toast({
                    title: "Success",
                    description: "Widget config saved",
                });
            } else {
                const errorData = await response.text();
                console.error(
                    "Save response error:",
                    response.status,
                    errorData
                );
                throw new Error(
                    `Save failed: ${response.status} ${response.statusText}`
                );
            }
        } catch (error) {
            console.error("Failed to save config:", error);
            toast({
                title: "Error",
                description:
                    error instanceof Error
                        ? error.message
                        : "Failed to save config",
                variant: "error",
            });
        } finally {
            setSaving(false);
        }
    };

    const handleAddDomain = () => {
        if (!config) return;
        const error = validateDomainInput(
            domainInput,
            config.allowed_domains,
            editingIndex
        );
        if (error) {
            setDomainError(error);
            return;
        }

        const normalized = normalizeDomain(domainInput);
        const updated = [...config.allowed_domains];
        if (editingIndex !== null) {
            updated[editingIndex] = normalized;
        } else {
            updated.push(normalized);
        }

        setConfig({ ...config, allowed_domains: updated });
        setDomainInput("");
        setDomainError(null);
        setEditingIndex(null);
    };

    const handleDeleteDomain = (index: number) => {
        if (!config) return;
        const updated = config.allowed_domains.filter((_, i) => i !== index);
        setConfig({ ...config, allowed_domains: updated });
        setEditingIndex(null);
    };

    const handleEditDomain = (index: number) => {
        if (!config) return;
        setDomainInput(config.allowed_domains[index]);
        setEditingIndex(index);
        setDomainError(null);
    };

    const generateCode = () => {
        if (!config) return "";
        // Use relative path or window.location.origin in browser
        const base =
            typeof window !== "undefined"
                ? window.location.origin
                : "https://veriply.io";
        return `<script
    src="${base}/widget.js"
    data-bot-id="${config.bot_id}"
    data-position="${config.position}"
    data-primary-color="${config.primary_color}"
    data-origin="${base}"
    ${config.auto_open ? 'data-auto-open="true"' : ""}
><\/script>`;
    };

    const copyToClipboard = () => {
        navigator.clipboard.writeText(generateCode()).then(() => {
            setCopied(true);
            setTimeout(() => setCopied(false), 2000);
            toast({
                title: "Copied!",
                description: "Widget code copied to clipboard",
            });
        });
    };

    if (loading) {
        return (
            <div className="flex items-center justify-center h-screen">
                <p className="text-slate-600">Loading...</p>
            </div>
        );
    }

    if (!config) {
        return (
            <div className="flex items-center justify-center h-screen">
                <p className="text-slate-600">Failed to load widget config</p>
            </div>
        );
    }

    return (
        <div className="space-y-6">
            {!hideNav && (
                <>
                    {/* Breadcrumb */}
                    <div className="flex items-center gap-2">
                        <Link
                            href="/dashboard/bots"
                            className="flex items-center gap-2 text-sm text-slate-600 hover:text-slate-900 transition-colors"
                        >
                            <ArrowLeft size={16} />
                            Back to Bots
                        </Link>
                    </div>

                    {/* Tabs */}
                    <div className="border-b border-slate-200">
                        <nav className="flex gap-6">
                            <Link
                                href={`/dashboard/bots/${botId}?tab=chat`}
                                className="flex items-center gap-2 px-1 py-3 text-sm font-medium border-b-2 border-transparent text-slate-600 hover:text-slate-900 transition-colors"
                            >
                                <MessageCircle size={16} />
                                Chat
                            </Link>
                            <Link
                                href={`/dashboard/bots/${botId}?tab=documents`}
                                className="flex items-center gap-2 px-1 py-3 text-sm font-medium border-b-2 border-transparent text-slate-600 hover:text-slate-900 transition-colors"
                            >
                                <FileText size={16} />
                                Document Access
                            </Link>
                            <Link
                                href={`/dashboard/bots/${botId}?tab=settings`}
                                className="flex items-center gap-2 px-1 py-3 text-sm font-medium border-b-2 border-transparent text-slate-600 hover:text-slate-900 transition-colors"
                            >
                                <Settings size={16} />
                                General Settings
                            </Link>
                            <Link
                                href={`/dashboard/bots/${botId}?tab=history`}
                                className="flex items-center gap-2 px-1 py-3 text-sm font-medium border-b-2 border-transparent text-slate-600 hover:text-slate-900 transition-colors"
                            >
                                <Clock3 size={16} />
                                History
                            </Link>
                            <span className="flex items-center gap-2 px-1 py-3 text-sm font-medium border-b-2 border-emerald-600 text-emerald-600 transition-colors">
                                <Settings2 size={16} />
                                Widget Configuration
                            </span>
                        </nav>
                    </div>
                </>
            )}

            {/* Content */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Settings Panel */}
                <div className="lg:col-span-2">
                    <Card className="p-6">
                        <h2 className="text-xl font-semibold text-slate-900 mb-6">
                            Widget Settings
                        </h2>

                        {/* Position */}
                        <div className="mb-6">
                            <label className="block text-sm font-medium text-slate-900 mb-2">
                                Position
                            </label>
                            <select
                                value={config.position}
                                onChange={(e) =>
                                    setConfig({
                                        ...config,
                                        position: e.target
                                            .value as WidgetConfig["position"],
                                    })
                                }
                                className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-sky-500"
                            >
                                {POSITIONS.map((pos) => (
                                    <option key={pos.value} value={pos.value}>
                                        {pos.label}
                                    </option>
                                ))}
                            </select>
                        </div>

                        {/* Primary Color */}
                        <div className="mb-6">
                            <label className="block text-sm font-medium text-slate-900 mb-2">
                                Primary Color
                            </label>
                            <div className="flex gap-2">
                                <input
                                    type="color"
                                    value={config.primary_color}
                                    onChange={(e) =>
                                        setConfig({
                                            ...config,
                                            primary_color: e.target.value,
                                        })
                                    }
                                    className="w-12 h-10 rounded-lg cursor-pointer"
                                />
                                <Input
                                    type="text"
                                    value={config.primary_color}
                                    onChange={(e) =>
                                        setConfig({
                                            ...config,
                                            primary_color: e.target.value,
                                        })
                                    }
                                    placeholder="#3B82F6"
                                    className="flex-1"
                                />
                            </div>
                        </div>

                        {/* Auto-open */}
                        <div className="mb-6">
                            <label className="flex items-center gap-3 cursor-pointer">
                                <input
                                    type="checkbox"
                                    checked={config.auto_open}
                                    onChange={(e) =>
                                        setConfig({
                                            ...config,
                                            auto_open: e.target.checked,
                                        })
                                    }
                                    className="w-4 h-4 rounded"
                                />
                                <span className="text-sm font-medium text-slate-900">
                                    Auto-open widget on page load
                                </span>
                            </label>
                        </div>

                        {/* Allowed Domains */}
                        <div className="mb-6">
                            <label className="block text-sm font-medium text-slate-900 mb-2">
                                Allowed Domains
                            </label>
                            {config.allowed_domains.length === 0 && (
                                <div className="mb-3 flex gap-2 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-800">
                                    <span aria-hidden>⚠️</span>
                                    <div className="text-left leading-snug">
                                        No domain restrictions. Widget is
                                        publicly accessible on ANY website.
                                    </div>
                                </div>
                            )}
                            <div className="flex flex-col gap-2">
                                <div className="flex flex-col sm:flex-row gap-2">
                                    <Input
                                        value={domainInput}
                                        onChange={(e) => {
                                            setDomainInput(e.target.value);
                                            setDomainError(null);
                                        }}
                                        onKeyDown={(e) => {
                                            if (e.key === "Enter") {
                                                e.preventDefault();
                                                handleAddDomain();
                                            }
                                        }}
                                        placeholder="example.com or *.example.com"
                                        className="flex-1"
                                        aria-label="Add allowed domain"
                                    />
                                    <Button
                                        onClick={handleAddDomain}
                                        className="sm:w-auto w-full"
                                        variant="secondary"
                                        size="lg"
                                    >
                                        {editingIndex !== null
                                            ? "Update"
                                            : "Add"}
                                    </Button>
                                </div>
                                <p className="text-xs text-slate-500">
                                    Supports wildcards (e.g., *.example.com).
                                    localhost is allowed for testing.
                                </p>
                                {domainError && (
                                    <p
                                        className="text-xs text-red-600"
                                        role="alert"
                                    >
                                        {domainError}
                                    </p>
                                )}
                            </div>

                            <div className="mt-3 flex flex-wrap gap-2">
                                {config.allowed_domains.length === 0 && (
                                    <p className="text-xs text-slate-600">
                                        No domains added yet.
                                    </p>
                                )}
                                {config.allowed_domains.map((domain, index) => (
                                    <div
                                        key={`${domain}-${index}`}
                                        className="flex items-center gap-2 rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-sm"
                                    >
                                        <span className="text-slate-800">
                                            {domain}
                                        </span>
                                        <div className="flex items-center gap-1">
                                            <Button
                                                size="sm"
                                                variant="ghost"
                                                className="h-11 min-w-[44px] px-3 text-xs"
                                                onClick={() =>
                                                    handleEditDomain(index)
                                                }
                                                aria-label={`Edit ${domain}`}
                                            >
                                                Edit
                                            </Button>
                                            <Button
                                                size="sm"
                                                variant="ghost"
                                                className="h-11 min-w-[44px] px-3 text-xs text-red-600 hover:bg-red-50"
                                                onClick={() =>
                                                    handleDeleteDomain(index)
                                                }
                                                aria-label={`Delete ${domain}`}
                                            >
                                                Delete
                                            </Button>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>

                        <Button
                            onClick={handleSave}
                            disabled={saving}
                            className="w-full"
                        >
                            {saving ? "Saving..." : "Save Settings"}
                        </Button>
                    </Card>
                </div>

                {/* Preview & Code Panel */}
                <div className="lg:col-span-1 h-full flex flex-col">
                    {/* Code Snippet */}
                    <Card className="p-6 mb-6 flex-1 flex flex-col">
                        <h3 className="text-lg font-semibold text-slate-900 mb-3">
                            Embed Code
                        </h3>
                        <div className="mb-3 p-3 bg-slate-50 rounded-lg flex-1 overflow-y-auto">
                            <code className="text-xs text-slate-700 whitespace-pre-wrap">
                                {generateCode()}
                            </code>
                        </div>
                        <Button
                            onClick={copyToClipboard}
                            variant="outline"
                            size="sm"
                            className="w-full mt-auto"
                        >
                            {copied ? (
                                <>
                                    <Check className="h-4 w-4 mr-2" />
                                    Copied!
                                </>
                            ) : (
                                <>
                                    <Copy className="h-4 w-4 mr-2" />
                                    Copy Code
                                </>
                            )}
                        </Button>
                    </Card>
                </div>
            </div>
            <WidgetFloatingDemo
                position={config.position}
                primaryColor={config.primary_color}
                autoOpen={config.auto_open}
                bot={bot}
                botId={botId}
            />
        </div>
    );
}

function WidgetFloatingDemo({
    position,
    primaryColor,
    autoOpen,
    bot,
    botId,
}: {
    position: WidgetConfig["position"];
    primaryColor: string;
    autoOpen: boolean;
    bot: Bot | null;
    botId: string;
}) {
    const [open, setOpen] = useState(autoOpen);
    const [colorChangeKey, setColorChangeKey] = useState(0);
    const prevColorRef = useRef<string>(primaryColor);

    // Force ChatInterface remount when color actually changes
    useEffect(() => {
        if (prevColorRef.current !== primaryColor) {
            prevColorRef.current = primaryColor;
            setColorChangeKey((prev) => prev + 1);
            if (typeof window !== "undefined") {
                const key = `chat_session_${botId}`;
                sessionStorage.removeItem(key);
            }
        }
    }, [primaryColor, botId]);

    const margin = "12px";
    const buttonSize = 56;
    const gap = 8;
    const chatOffset = `${buttonSize + gap}px`;

    const posStyle = {
        "bottom-right": { right: margin, bottom: margin },
        "bottom-left": { left: margin, bottom: margin },
        "top-right": { right: margin, top: margin },
        "top-left": { left: margin, top: margin },
    } as const;

    const chatPosStyle = {
        "bottom-right": {
            right: margin,
            bottom: `calc(${margin} + ${chatOffset})`,
        },
        "bottom-left": {
            left: margin,
            bottom: `calc(${margin} + ${chatOffset})`,
        },
        "top-right": { right: margin, top: `calc(${margin} + ${chatOffset})` },
        "top-left": { left: margin, top: `calc(${margin} + ${chatOffset})` },
    } as const;

    return (
        <>
            <button
                type="button"
                aria-label="Open chat"
                onClick={() => setOpen((v) => !v)}
                style={{
                    position: "fixed",
                    zIndex: 2147483648,
                    width: `${buttonSize}px`,
                    height: `${buttonSize}px`,
                    borderRadius: "50%",
                    border: "none",
                    cursor: "pointer",
                    boxShadow: "0 6px 16px rgba(0,0,0,0.25)",
                    background: primaryColor,
                    color: "#fff",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    ...posStyle[position],
                }}
            >
                <svg
                    width="26"
                    height="26"
                    viewBox="0 0 24 24"
                    fill="none"
                    xmlns="http://www.w3.org/2000/svg"
                >
                    <path
                        d="M4 4H20V16H5.17L4 17.17V4Z"
                        stroke="white"
                        strokeWidth="2"
                    />
                    <path d="M8 9H16" stroke="white" strokeWidth="2" />
                    <path d="M8 13H12" stroke="white" strokeWidth="2" />
                </svg>
            </button>

            {open && bot && (
                <div
                    className="fixed flex flex-col"
                    style={{
                        width: "400px",
                        height: "600px",
                        borderRadius: "12px",
                        overflow: "hidden",
                        boxShadow: "0 8px 24px rgba(0,0,0,0.2)",
                        background: "#fff",
                        zIndex: 2147483647,
                        ...chatPosStyle[position],
                    }}
                >
                    {/* Custom Header */}
                    <div
                        className="px-4 py-3 text-white text-sm font-semibold flex items-center justify-between flex-shrink-0"
                        style={{ background: primaryColor }}
                    >
                        <span>Chat with {bot.name}</span>
                        <button
                            onClick={() => setOpen(false)}
                            className="text-white hover:opacity-80 transition-opacity"
                            aria-label="Close chat"
                        >
                            ✕
                        </button>
                    </div>
                    {/* Chat Interface */}
                    <div className="flex-1 overflow-hidden h-full">
                        <ChatInterface
                            key={`${botId}-${colorChangeKey}`}
                            botId={botId}
                            botName={bot.name}
                            botAvatar={bot.avatar_url}
                            description={bot.description}
                            isPublic={bot.is_public}
                            confidenceThreshold={bot.confidence_threshold}
                            embedded={true}
                            embedOrigin="widget-preview"
                        />
                    </div>
                </div>
            )}
        </>
    );
}
