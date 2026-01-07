"use client";

import { useEffect, useState } from "react";
import { EmailIntegration } from "@/lib/api/integrations";
import { Bot } from "@/types/bot";
import { CreateEmailRuleRequest } from "@/lib/api/emailRules";

type Props = {
  integrations: EmailIntegration[];
  bots: Bot[];
  defaultIntegrationId?: string;
  onCreate: (payload: CreateEmailRuleRequest) => Promise<void> | void;
  onIntegrationChange?: (integrationId: string | null) => void;
};

export default function RuleForm({ integrations, bots, defaultIntegrationId, onCreate, onIntegrationChange }: Props) {
  const [integrationId, setIntegrationId] = useState<string | "">(defaultIntegrationId || "");
  const [botId, setBotId] = useState<string | "">(bots[0]?.id || "");
  const [folderLabels, setFolderLabels] = useState("");
  const [includeKeywords, setIncludeKeywords] = useState("");
  const [excludeKeywords, setExcludeKeywords] = useState("");
  const [isActive, setIsActive] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (defaultIntegrationId) setIntegrationId(defaultIntegrationId);
  }, [defaultIntegrationId]);

  useEffect(() => {
    if (onIntegrationChange) {
      onIntegrationChange(integrationId || null);
    }
  }, [integrationId, onIntegrationChange]);

  const availableBots = bots || [];

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      const payload: CreateEmailRuleRequest = {
        integration_id: integrationId,
        bot_id: botId,
        folder_labels: folderLabels
          .split(",")
          .map((s) => s.trim())
          .filter(Boolean),
        include_keywords: includeKeywords
          .split(",")
          .map((s) => s.trim())
          .filter(Boolean),
        exclude_keywords: excludeKeywords
          .split(",")
          .map((s) => s.trim())
          .filter(Boolean),
        is_active: isActive,
      };
      await onCreate(payload);
      // reset keyword fields only (keep integration/bot selection)
      setFolderLabels("");
      setIncludeKeywords("");
      setExcludeKeywords("");
      setIsActive(true);
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : "Failed to create rule";
      setError(msg);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="bg-white rounded-lg border border-slate-200 p-6">
      <h2 className="text-xl font-semibold text-slate-900 mb-4">Create Rule</h2>
      {error && (
        <div className="mb-4 p-3 rounded bg-red-50 text-red-700 border border-red-200">{error}</div>
      )}
      <form onSubmit={handleSubmit} className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">Integration</label>
          <select
            className="w-full border rounded px-3 py-2"
            value={integrationId}
            onChange={(e) => setIntegrationId(e.target.value)}
            required
          >
            <option value="" disabled>
              Select integration
            </option>
            {integrations.map((i) => (
              <option key={i.id} value={i.id}>
                {i.provider.toUpperCase()} - {i.status}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">Bot</label>
          <select
            className="w-full border rounded px-3 py-2"
            value={botId}
            onChange={(e) => setBotId(e.target.value)}
            required
          >
            <option value="" disabled>
              Select bot
            </option>
            {availableBots.map((b) => (
              <option key={b.id} value={b.id}>
                {b.name}
              </option>
            ))}
          </select>
        </div>

        <div className="md:col-span-2">
          <label className="block text-sm font-medium text-slate-700 mb-1">Folders/Labels</label>
          <input
            type="text"
            className="w-full border rounded px-3 py-2"
            placeholder="e.g. INBOX, Support, billing"
            value={folderLabels}
            onChange={(e) => setFolderLabels(e.target.value)}
          />
          <p className="text-xs text-slate-500 mt-1">Comma-separated; leave empty to match all folders.</p>
        </div>

        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">Include Keywords</label>
          <input
            type="text"
            className="w-full border rounded px-3 py-2"
            placeholder="e.g. invoice, refund"
            value={includeKeywords}
            onChange={(e) => setIncludeKeywords(e.target.value)}
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">Exclude Keywords</label>
          <input
            type="text"
            className="w-full border rounded px-3 py-2"
            placeholder="e.g. newsletter, promo"
            value={excludeKeywords}
            onChange={(e) => setExcludeKeywords(e.target.value)}
          />
        </div>

        <div className="flex items-center gap-2 md:col-span-2">
          <input
            id="isActive"
            type="checkbox"
            className="h-4 w-4"
            checked={isActive}
            onChange={(e) => setIsActive(e.target.checked)}
          />
          <label htmlFor="isActive" className="text-sm text-slate-700">
            Active
          </label>
        </div>

        <div className="md:col-span-2">
          <button
            type="submit"
            disabled={submitting || !integrationId || !botId}
            className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
          >
            {submitting ? "Creating..." : "Add Rule"}
          </button>
        </div>
      </form>
    </div>
  );
}
