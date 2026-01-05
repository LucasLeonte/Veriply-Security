"use client";

import { useState, useEffect } from "react";
import { Card } from "../../../../../../../components/ui/card";
import { Button } from "../../../../../../../components/ui/button";
import { Input } from "../../../../../../../components/ui/input";
import { Textarea } from "../../../../../../../components/ui/textarea";
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
}

const POSITIONS = [
    { value: "bottom-right", label: "Bottom Right" },
    { value: "bottom-left", label: "Bottom Left" },
    { value: "top-right", label: "Top Right" },
    { value: "top-left", label: "Top Left" },
];

export function WidgetConfigClient({
    groupId,
    botId,
}: {
    groupId: string;
    botId: string;
}) {
    const [config, setConfig] = useState<WidgetConfig | null>(null);
    const [bot, setBot] = useState<Bot | null>(null);
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [copied, setCopied] = useState(false);
    const [paramError, setParamError] = useState<string | null>(null);
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
                    setConfig(configData);
                    setBot(botData);
                } else {
                    toast({
                        title: "Error",
                        description: "Failed to load widget config",
                        variant: "destructive",
                    });
                }
            } catch (error) {
                console.error("Failed to fetch config:", error);
                toast({
                    title: "Error",
                    description: "Failed to load widget config or bot details",
                    variant: "destructive",
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
                variant: "destructive",
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
                        welcome_message: config.welcome_message,
                        auto_open: config.auto_open,
                    }),
                }
            );
            if (response.ok) {
                const updated = await response.json();
                setConfig(updated);
                toast({
                    title: "Success",
                    description: "Widget config saved",
                });
            } else {
                throw new Error("Save failed");
            }
        } catch (error) {
            console.error("Failed to save config:", error);
            toast({
                title: "Error",
                description: "Failed to save config",
                variant: "destructive",
            });
        } finally {
            setSaving(false);
        }
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
    ${
        config.welcome_message
            ? `data-welcome-message="${config.welcome_message}"`
            : ""
    }
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
                        href={`/dashboard/bots/${botId}`}
                        className="flex items-center gap-2 px-1 py-3 text-sm font-medium border-b-2 border-transparent text-slate-600 hover:text-slate-900 transition-colors"
                    >
                        <MessageCircle size={16} />
                        Chat
                    </Link>
                    <Link
                        href={`/dashboard/bots/${botId}`}
                        className="flex items-center gap-2 px-1 py-3 text-sm font-medium border-b-2 border-transparent text-slate-600 hover:text-slate-900 transition-colors"
                    >
                        <FileText size={16} />
                        Document Access
                    </Link>
                    <Link
                        href={`/dashboard/bots/${botId}`}
                        className="flex items-center gap-2 px-1 py-3 text-sm font-medium border-b-2 border-transparent text-slate-600 hover:text-slate-900 transition-colors"
                    >
                        <Settings size={16} />
                        General Settings
                    </Link>
                    <span className="flex items-center gap-2 px-1 py-3 text-sm font-medium border-b-2 border-emerald-600 text-emerald-600 transition-colors">
                        <Settings2 size={16} />
                        Widget Configuration
                    </span>
                </nav>
            </div>

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

                        {/* Welcome Message */}
                        <div className="mb-6">
                            <label className="block text-sm font-medium text-slate-900 mb-2">
                                Welcome Message{" "}
                                <span className="text-slate-500">
                                    ({config.welcome_message?.length || 0}/200)
                                </span>
                            </label>
                            <Textarea
                                value={config.welcome_message || ""}
                                onChange={(e) =>
                                    setConfig({
                                        ...config,
                                        welcome_message: e.target.value.slice(
                                            0,
                                            200
                                        ),
                                    })
                                }
                                placeholder="Hi! How can I help you?"
                                className="min-h-[100px]"
                                maxLength={200}
                            />
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
                welcomeMessage={config.welcome_message}
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
    welcomeMessage,
    autoOpen,
    bot,
    botId,
}: {
    position: WidgetConfig["position"];
    primaryColor: string;
    welcomeMessage: string | null;
    autoOpen: boolean;
    bot: Bot | null;
    botId: string;
}) {
    const [open, setOpen] = useState(autoOpen);

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
                    className="fixed"
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
                    <div className="flex flex-col h-full">
                        <div
                            className="px-4 py-3 text-white text-sm font-semibold flex items-center justify-between"
                            style={{ background: primaryColor }}
                        >
                            <span>Chat with {bot.name}</span>
                            <button
                                onClick={() => setOpen(false)}
                                className="text-white hover:opacity-80"
                                aria-label="Close chat"
                            >
                                ✕
                            </button>
                        </div>
                        <div className="flex-1 overflow-hidden">
                            <ChatInterface
                                botId={botId}
                                botName={bot.name}
                                botAvatar={bot.avatar_url}
                                welcomeMessage={
                                    welcomeMessage ||
                                    bot.welcome_message ||
                                    bot.description ||
                                    `Hi! I'm ${bot.name}`
                                }
                                isPublic={bot.is_public}
                                confidenceThreshold={bot.confidence_threshold}
                                embedded={true}
                            />
                        </div>
                    </div>
                </div>
            )}
        </>
    );
}
