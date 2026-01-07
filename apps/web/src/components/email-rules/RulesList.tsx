"use client";

import { useMemo, useState } from "react";
import { EmailRule, UpdateEmailRuleRequest } from "@/lib/api/emailRules";
import { Bot } from "@/types/bot";

type Props = {
  rules: EmailRule[];
  bots: Bot[];
  onUpdate: (id: string, payload: UpdateEmailRuleRequest) => Promise<void> | void;
  onDelete: (id: string) => Promise<void> | void;
  onReorder: (orderedIds: string[]) => Promise<void> | void;
  onTest: (id: string) => void;
};

export default function RulesList({ rules, bots, onUpdate, onDelete, onReorder, onTest }: Props) {
  const [working, setWorking] = useState<string | null>(null);

  const sorted = useMemo(() => {
    return [...rules].sort((a, b) => a.priority - b.priority);
  }, [rules]);

  const botName = (botId: string) => bots.find((b) => b.id === botId)?.name || botId;

  const move = async (id: string, dir: -1 | 1) => {
    const idx = sorted.findIndex((r) => r.id === id);
    if (idx < 0) return;
    const newOrder = [...sorted];
    const targetIdx = idx + dir;
    if (targetIdx < 0 || targetIdx >= newOrder.length) return;
    const [item] = newOrder.splice(idx, 1);
    newOrder.splice(targetIdx, 0, item);
    await onReorder(newOrder.map((r) => r.id));
  };

  const toggleActive = async (r: EmailRule) => {
    setWorking(r.id);
    try {
      await onUpdate(r.id, { is_active: !r.is_active });
    } finally {
      setWorking(null);
    }
  };

  return (
    <div className="bg-white rounded-lg border border-slate-200 p-6">
      <h2 className="text-xl font-semibold text-slate-900 mb-4">Rules</h2>
      {sorted.length === 0 ? (
        <p className="text-slate-600">No rules yet. Create your first rule above.</p>
      ) : (
        <div className="overflow-x-auto">
          <table className="min-w-full text-sm">
            <thead>
              <tr className="text-left text-slate-700 border-b">
                <th className="py-2 pr-4">#</th>
                <th className="py-2 pr-4">Active</th>
                <th className="py-2 pr-4">Integration</th>
                <th className="py-2 pr-4">Bot</th>
                <th className="py-2 pr-4">Folders/Labels</th>
                <th className="py-2 pr-4">Include</th>
                <th className="py-2 pr-4">Exclude</th>
                <th className="py-2 pr-4">Actions</th>
              </tr>
            </thead>
            <tbody>
              {sorted.map((r, i) => (
                <tr key={r.id} className="border-b last:border-b-0">
                  <td className="py-2 pr-4 align-top">{i + 1}</td>
                  <td className="py-2 pr-4 align-top">
                    <button
                      onClick={() => toggleActive(r)}
                      disabled={working === r.id}
                      className={`px-2 py-1 rounded text-xs ${r.is_active ? "bg-green-100 text-green-800" : "bg-slate-100 text-slate-700"}`}
                    >
                      {r.is_active ? "Active" : "Paused"}
                    </button>
                  </td>
                  <td className="py-2 pr-4 align-top">{r.integration_id.slice(0, 8)}…</td>
                  <td className="py-2 pr-4 align-top">{botName(r.bot_id)}</td>
                  <td className="py-2 pr-4 align-top">{(r.folder_labels || []).join(", ") || <span className="text-slate-400">All</span>}</td>
                  <td className="py-2 pr-4 align-top">{(r.include_keywords || []).join(", ") || "—"}</td>
                  <td className="py-2 pr-4 align-top">{(r.exclude_keywords || []).join(", ") || "—"}</td>
                  <td className="py-2 pr-4 align-top">
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => move(r.id, -1)}
                        className="px-2 py-1 rounded bg-slate-100 hover:bg-slate-200"
                        title="Move up"
                      >↑</button>
                      <button
                        onClick={() => move(r.id, 1)}
                        className="px-2 py-1 rounded bg-slate-100 hover:bg-slate-200"
                        title="Move down"
                      >↓</button>
                      <button
                        onClick={() => onTest(r.id)}
                        className="px-2 py-1 rounded bg-blue-600 text-white hover:bg-blue-700"
                      >Test</button>
                      <button
                        onClick={() => onDelete(r.id)}
                        className="px-2 py-1 rounded bg-red-600 text-white hover:bg-red-700"
                      >Delete</button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
