"use client";

import { useEffect, useState } from "react";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import { botsApi } from "@/lib/api/bots";
import { Bot, UpdateBotInput } from "@/types/bot";
import { Loader2, Upload } from "lucide-react";

interface Props {
    groupId: string;
    botId: string;
}

export default function BotGeneralSettings({ groupId, botId }: Props) {
    const [bot, setBot] = useState<Bot | null>(null);
    const [saving, setSaving] = useState(false);
    const [uploading, setUploading] = useState(false);
    const [form, setForm] = useState<UpdateBotInput>({});
    const [error, setError] = useState<string | null>(null);
    const [success, setSuccess] = useState<string | null>(null);

    useEffect(() => {
        (async () => {
            try {
                const data = await botsApi.getBotDetails(groupId, botId);
                setBot(data);
                setForm({
                    name: data.name,
                    description: data.description,
                    is_public: data.is_public,
                    is_active: data.is_active ?? true, // Default to true if undefined
                    confidence_threshold: data.confidence_threshold,
                });
            } catch (e: unknown) {
                const msg = e instanceof Error ? e.message : String(e);
                setError(msg || "Failed to load bot");
            }
        })();
    }, [groupId, botId]);

    const onSave = async () => {
        setError(null);
        setSuccess(null);
        setSaving(true);
        try {
            const updated = await botsApi.updateBot(groupId, botId, form);
            setBot(updated);
            setSuccess("Settings saved");
        } catch (e: unknown) {
            const msg = e instanceof Error ? e.message : String(e);
            setError(msg || "Failed to save settings");
        } finally {
            setSaving(false);
        }
    };

    const onAvatarChange = async (file: File) => {
        setUploading(true);
        setError(null);
        setSuccess(null);
        try {
            const res = await botsApi.uploadBotAvatar(groupId, botId, file);
            setForm((f) => ({ ...f, avatar_url: res.avatar_url }));
            setBot((prev) =>
                prev ? { ...prev, avatar_url: res.avatar_url } : prev
            );
            setSuccess("Avatar updated");
        } catch (e: unknown) {
            const msg = e instanceof Error ? e.message : String(e);
            setError(msg || "Failed to upload avatar");
        } finally {
            setUploading(false);
        }
    };

    if (!bot) {
        return (
            <div className="flex items-center gap-2 text-slate-600">
                <Loader2 className="h-4 w-4 animate-spin" /> Loading...
            </div>
        );
    }

    return (
        <div className="max-w-4xl space-y-6">
            {/* Profile Section */}
            <div className="bg-white rounded-lg border border-slate-200 p-6">
                <div className="flex items-start gap-6">
                    {/* Avatar */}
                    <div className="flex-shrink-0">
                        <div className="relative">
                            <div className="h-24 w-24 rounded-full overflow-hidden bg-gradient-to-br from-sky-100 to-emerald-100 border-2 border-white shadow-lg">
                                {bot.avatar_url ? (
                                    // eslint-disable-next-line @next/next/no-img-element
                                    <img
                                        src={bot.avatar_url}
                                        alt={bot.name}
                                        className="h-full w-full object-cover"
                                    />
                                ) : (
                                    <div className="h-full w-full flex items-center justify-center text-slate-400 text-2xl font-semibold">
                                        {bot.name?.charAt(0)?.toUpperCase() || "B"}
                                    </div>
                                )}
                            </div>
                            <label className="absolute -bottom-1 -right-1 h-8 w-8 rounded-full bg-sky-600 hover:bg-sky-700 transition-colors cursor-pointer flex items-center justify-center shadow-lg">
                                <Upload className="h-4 w-4 text-white" />
                                <input
                                    type="file"
                                    accept="image/*"
                                    className="hidden"
                                    onChange={(e) => {
                                        const file = e.target.files?.[0];
                                        if (file) onAvatarChange(file);
                                    }}
                                    disabled={uploading}
                                />
                            </label>
                        </div>
                        {uploading && (
                            <p className="text-xs text-slate-500 mt-2 text-center">
                                Uploading...
                            </p>
                        )}
                    </div>

                    {/* Name and Description */}
                    <div className="flex-1 space-y-4">
                        <div>
                            <label
                                htmlFor="name"
                                className="block text-sm font-medium text-slate-700 mb-1.5"
                            >
                                Bot Name
                            </label>
                            <input
                                id="name"
                                value={form.name || ""}
                                onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                                    setForm({ ...form, name: e.target.value })
                                }
                                className="w-full h-11 rounded-lg border border-slate-300 bg-white px-4 text-sm font-medium text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-sky-500 focus:border-transparent transition-all"
                                placeholder="Enter bot name..."
                            />
                        </div>
                        <div>
                            <label
                                htmlFor="description"
                                className="block text-sm font-medium text-slate-700 mb-1.5"
                            >
                                Description
                            </label>
                            <Textarea
                                id="description"
                                value={form.description || ""}
                                onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) =>
                                    setForm({ ...form, description: e.target.value })
                                }
                                rows={3}
                                className="resize-none"
                                placeholder="Describe what this bot does..."
                            />
                        </div>
                    </div>
                </div>
            </div>

            {/* Configuration Section */}
            <div className="bg-white rounded-lg border border-slate-200 p-6 space-y-6">
                <div>
                    <h3 className="text-base font-semibold text-slate-900 mb-4">
                        Configuration
                    </h3>

                    {/* Bot ID */}
                    <div className="pb-6 border-b border-slate-100">
                        <label className="block text-sm font-medium text-slate-900 mb-2">
                            Bot ID
                        </label>
                        <div className="flex items-center gap-2 p-3 bg-slate-50 border border-slate-200 rounded-lg">
                            <code className="flex-1 text-xs text-slate-600 font-mono break-all">
                                {bot.id}
                            </code>
                            <button
                                type="button"
                                onClick={() => {
                                    navigator.clipboard.writeText(bot.id);
                                }}
                                className="flex-shrink-0 p-2 hover:bg-slate-200 rounded-md transition-colors"
                                title="Copy bot ID"
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
                                    className="text-slate-600"
                                >
                                    <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                                    <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
                                </svg>
                            </button>
                        </div>
                    </div>

                    {/* Confidence Threshold */}
                    <div className="pb-6 border-b border-slate-100 pt-6">
                        <div className="flex items-start justify-between mb-3">
                            <div className="flex-1">
                                <label
                                    htmlFor="confidence_threshold"
                                    className="block text-sm font-medium text-slate-900"
                                >
                                    Confidence Threshold
                                </label>
                                <p className="text-xs text-slate-500 mt-0.5">
                                    Answers below this threshold require human review
                                </p>
                            </div>
                            <span className="inline-flex items-center justify-center min-w-[3rem] h-8 px-3 rounded-md bg-sky-50 text-sm font-semibold text-sky-700">
                                {form.confidence_threshold ?? 80}%
                            </span>
                        </div>
                        <div className="relative">
                            <input
                                id="confidence_threshold"
                                type="range"
                                min="0"
                                max="100"
                                value={form.confidence_threshold ?? 80}
                                onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                                    setForm({
                                        ...form,
                                        confidence_threshold: parseInt(e.target.value),
                                    })
                                }
                                className="slider-custom w-full h-2 bg-gradient-to-r from-red-200 via-amber-200 to-emerald-200 rounded-full appearance-none cursor-pointer transition-all"
                                style={{
                                    background: `linear-gradient(to right, 
                                        #fecaca 0%, 
                                        #fde68a ${(form.confidence_threshold ?? 80) / 2}%, 
                                        #86efac ${form.confidence_threshold ?? 80}%, 
                                        #e2e8f0 ${form.confidence_threshold ?? 80}%)`,
                                }}
                            />
                            <style jsx>{`
                                .slider-custom::-webkit-slider-thumb {
                                    appearance: none;
                                    width: 20px;
                                    height: 20px;
                                    border-radius: 50%;
                                    background: linear-gradient(135deg, #0ea5e9 0%, #0284c7 100%);
                                    cursor: pointer;
                                    border: 3px solid white;
                                    box-shadow: 0 2px 8px rgba(14, 165, 233, 0.4);
                                    transition: all 0.2s ease;
                                }
                                .slider-custom::-webkit-slider-thumb:hover {
                                    transform: scale(1.15);
                                    box-shadow: 0 4px 12px rgba(14, 165, 233, 0.6);
                                }
                                .slider-custom::-webkit-slider-thumb:active {
                                    transform: scale(1.05);
                                }
                                .slider-custom::-moz-range-thumb {
                                    width: 20px;
                                    height: 20px;
                                    border-radius: 50%;
                                    background: linear-gradient(135deg, #0ea5e9 0%, #0284c7 100%);
                                    cursor: pointer;
                                    border: 3px solid white;
                                    box-shadow: 0 2px 8px rgba(14, 165, 233, 0.4);
                                    transition: all 0.2s ease;
                                }
                                .slider-custom::-moz-range-thumb:hover {
                                    transform: scale(1.15);
                                    box-shadow: 0 4px 12px rgba(14, 165, 233, 0.6);
                                }
                                .slider-custom::-moz-range-thumb:active {
                                    transform: scale(1.05);
                                }
                            `}</style>
                        </div>
                        <div className="flex justify-between mt-2">
                            <span className="text-xs text-slate-400">0%</span>
                            <span className="text-xs text-slate-400">50%</span>
                            <span className="text-xs text-slate-400">100%</span>
                        </div>
                    </div>

                    {/* Toggles */}
                    <div className="space-y-4 pt-6">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-sm font-medium text-slate-900">
                                    Bot Active
                                </p>
                                <p className="text-xs text-slate-500 mt-0.5">
                                    Enable or disable this bot
                                </p>
                            </div>
                            <Switch
                                checked={!!form.is_active}
                                onCheckedChange={(checked) =>
                                    setForm({ ...form, is_active: checked })
                                }
                            />
                        </div>
                        <div className="flex items-center justify-between pt-4 border-t border-slate-100">
                            <div>
                                <p className="text-sm font-medium text-slate-900">
                                    Allow Link Sharing
                                </p>
                                <p className="text-xs text-slate-500 mt-0.5">
                                    Let others access this bot via public link
                                </p>
                            </div>
                            <Switch
                                checked={!!form.is_public}
                                onCheckedChange={(checked) =>
                                    setForm({ ...form, is_public: checked })
                                }
                            />
                        </div>
                    </div>
                </div>
            </div>

            {/* Alerts */}
            {error && (
                <div className="p-4 rounded-lg border border-red-200 bg-red-50 text-sm text-red-800 flex items-start gap-3">
                    <div className="flex-shrink-0 w-5 h-5 rounded-full bg-red-100 flex items-center justify-center mt-0.5">
                        <span className="text-red-600 text-xs font-bold">!</span>
                    </div>
                    <p className="flex-1">{error}</p>
                </div>
            )}
            {success && (
                <div className="p-4 rounded-lg border border-emerald-200 bg-emerald-50 text-sm text-emerald-800 flex items-start gap-3">
                    <div className="flex-shrink-0 w-5 h-5 rounded-full bg-emerald-100 flex items-center justify-center mt-0.5">
                        <span className="text-emerald-600 text-xs font-bold">✓</span>
                    </div>
                    <p className="flex-1">{success}</p>
                </div>
            )}

            {/* Actions */}
            <div className="flex items-center justify-end gap-3">
                <Button
                    onClick={onSave}
                    disabled={saving}
                    className="bg-sky-600 hover:bg-sky-700 text-white px-6 h-11"
                >
                    {saving ? (
                        <>
                            <Loader2 className="h-4 w-4 animate-spin mr-2" />
                            Saving...
                        </>
                    ) : (
                        "Save Changes"
                    )}
                </Button>
            </div>
        </div>
    );
}
