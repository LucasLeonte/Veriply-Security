"use client";

import { useEffect, useState } from "react";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
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
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="md:col-span-2 space-y-5">
                <div>
                    <label
                        htmlFor="name"
                        className="block text-sm font-medium text-slate-700 mb-1"
                    >
                        Name
                    </label>
                    <input
                        id="name"
                        value={form.name || ""}
                        onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                            setForm({ ...form, name: e.target.value })
                        }
                        className="flex h-10 w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm ring-offset-white placeholder:text-slate-400 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sky-500"
                    />
                </div>
                <div>
                    <label
                        htmlFor="description"
                        className="block text-sm font-medium text-slate-700 mb-1"
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
                    />
                </div>
                <div className="flex items-center justify-between p-3 border rounded-md">
                    <p className="text-sm text-slate-700">
                        Allow anyone with the link to chat with this bot
                    </p>
                    <input
                        id="is_public"
                        type="checkbox"
                        checked={!!form.is_public}
                        onChange={(e) =>
                            setForm({ ...form, is_public: e.target.checked })
                        }
                        className="h-5 w-5 accent-sky-600"
                    />
                </div>
                {error && (
                    <div className="p-3 border border-red-200 bg-red-50 text-sm text-red-800 rounded">
                        {error}
                    </div>
                )}
                {success && (
                    <div className="p-3 border border-emerald-200 bg-emerald-50 text-sm text-emerald-800 rounded">
                        {success}
                    </div>
                )}
                <div className="flex gap-2">
                    <Button onClick={onSave} disabled={saving}>
                        {saving ? (
                            <>
                                <Loader2 className="h-4 w-4 animate-spin mr-2" />
                                Saving...
                            </>
                        ) : (
                            "Save changes"
                        )}
                    </Button>
                </div>
            </div>
            <div className="space-y-4">
                <div className="block text-sm font-medium text-slate-700">
                    Profile picture
                </div>
                <div className="flex items-center gap-4">
                    <div className="h-20 w-20 rounded-full overflow-hidden bg-slate-100 border">
                        {bot.avatar_url ? (
                            // eslint-disable-next-line @next/next/no-img-element
                            <img
                                src={bot.avatar_url}
                                alt={bot.name}
                                className="h-full w-full object-cover"
                            />
                        ) : (
                            <div className="h-full w-full flex items-center justify-center text-slate-400">
                                No image
                            </div>
                        )}
                    </div>
                    <div>
                        <label className="inline-flex items-center gap-2 px-3 py-2 border rounded-md cursor-pointer hover:bg-slate-50">
                            <Upload className="h-4 w-4" />
                            <span>{uploading ? "Uploading..." : "Upload"}</span>
                            <input
                                type="file"
                                accept="image/*"
                                className="hidden"
                                onChange={(e) => {
                                    const file = e.target.files?.[0];
                                    if (file) onAvatarChange(file);
                                }}
                            />
                        </label>
                    </div>
                </div>
            </div>
        </div>
    );
}
