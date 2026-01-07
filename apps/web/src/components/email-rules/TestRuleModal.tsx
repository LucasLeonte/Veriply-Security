"use client";

import { useEffect, useState } from "react";

type Props = {
  open: boolean;
  onClose: () => void;
  ruleId?: string;
  onTest: (
    id: string,
    sample: { subject: string; body: string; sender?: string; folder?: string; labels?: string[] }
  ) => Promise<{ matched: boolean; explanation: string } | { matched: boolean; rule_id?: string; explanation: string }>;
};

export default function TestRuleModal({ open, onClose, ruleId, onTest }: Props) {
  const [subject, setSubject] = useState("");
  const [body, setBody] = useState("");
  const [sender, setSender] = useState("");
  const [folder, setFolder] = useState("");
  const [labels, setLabels] = useState("");
  const [result, setResult] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!open) {
      setSubject("");
      setBody("");
      setSender("");
      setFolder("");
      setLabels("");
      setResult(null);
    }
  }, [open]);

  const handleTest = async () => {
    if (!ruleId) return;
    setLoading(true);
    try {
      const payload = {
        subject,
        body,
        sender: sender || undefined,
        folder: folder || undefined,
        labels: labels
          ? labels.split(",").map((s) => s.trim()).filter(Boolean)
          : undefined,
      };
      const res = await onTest(ruleId, payload);
      setResult(res.matched ? `Matched ✅ — ${res.explanation}` : `No match ❌ — ${res.explanation}`);
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : "Test failed";
      setResult(msg);
    } finally {
      setLoading(false);
    }
  };

  if (!open) return null;

  return (
    <div className="fixed inset-0 bg-black/40 z-50 flex items-center justify-center">
      <div className="bg-white rounded-lg shadow-lg w-full max-w-2xl p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold">Test Rule</h3>
          <button onClick={onClose} className="text-slate-600 hover:text-slate-900">✕</button>
        </div>

        <div className="grid grid-cols-1 gap-3">
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Subject</label>
            <input
              className="w-full border rounded px-3 py-2"
              value={subject}
              onChange={(e) => setSubject(e.target.value)}
              placeholder="Email subject"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Body</label>
            <textarea
              className="w-full border rounded px-3 py-2 min-h-[120px]"
              value={body}
              onChange={(e) => setBody(e.target.value)}
              placeholder="Paste or type the email body"
            />
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Sender</label>
              <input
                className="w-full border rounded px-3 py-2"
                value={sender}
                onChange={(e) => setSender(e.target.value)}
                placeholder="e.g. billing@vendor.com"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Folder</label>
              <input
                className="w-full border rounded px-3 py-2"
                value={folder}
                onChange={(e) => setFolder(e.target.value)}
                placeholder="e.g. INBOX"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Labels</label>
              <input
                className="w-full border rounded px-3 py-2"
                value={labels}
                onChange={(e) => setLabels(e.target.value)}
                placeholder="e.g. Support, Billing"
              />
            </div>
          </div>
        </div>

        <div className="flex items-center justify-between mt-4">
          <div className="text-sm text-slate-600">
            {result || "Enter sample content and click Test"}
          </div>
          <div className="flex items-center gap-2">
            <button onClick={onClose} className="px-3 py-2 rounded bg-slate-100 hover:bg-slate-200">Close</button>
            <button
              onClick={handleTest}
              disabled={loading || !subject || !body}
              className="px-3 py-2 rounded bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50"
            >
              {loading ? "Testing..." : "Test"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
