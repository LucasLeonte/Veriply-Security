"use client";

import { useCallback, useEffect, useState } from "react";
import { DashboardLayout } from "@/components";
import { getAccessToken } from "@/lib/auth";
import { EmailRule, listEmailRules, createEmailRule, updateEmailRule, deleteEmailRule, reorderEmailRules, testEmailRule, getMonitoringStatus, setMonitoringPause, MonitoringStatus } from "@/lib/api/emailRules";
import { EmailIntegration, listIntegrations } from "@/lib/api/integrations";
import { botsApi } from "@/lib/api/bots";
import { Bot } from "@/types/bot";
import { useGroup } from "@/contexts/GroupContext";
import RuleForm from "../../../components/email-rules/RuleForm";
import RulesList from "../../../components/email-rules/RulesList";
import TestRuleModal from "../../../components/email-rules/TestRuleModal";

export default function EmailRulesPage() {
  const [token, setToken] = useState<string | null>(null);
  const [integrations, setIntegrations] = useState<EmailIntegration[]>([]);
  const [bots, setBots] = useState<Bot[]>([]);
  const [rules, setRules] = useState<EmailRule[]>([]);
  const [selectedIntegrationId, setSelectedIntegrationId] = useState<string | null>(null);
  const [showTestModal, setShowTestModal] = useState<{ open: boolean; ruleId?: string }>({ open: false });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [monitoring, setMonitoring] = useState<MonitoringStatus | null>(null);
  const [monitoringError, setMonitoringError] = useState<string | null>(null);

  useEffect(() => {
    setToken(getAccessToken());
  }, []);

  const { currentGroup } = useGroup();

  useEffect(() => {
    if (!token) return;
    (async () => {
      try {
        const ints = await listIntegrations(token);
        setIntegrations(ints.integrations);
        if (ints.integrations.length > 0) {
          setSelectedIntegrationId(ints.integrations[0].id);
        }
      } catch (e: unknown) {
        const msg = e instanceof Error ? e.message : "Failed to load integrations";
        setError(msg);
      }
    })();
  }, [token]);

  useEffect(() => {
    if (!currentGroup) return;
    (async () => {
      try {
        const resp = await botsApi.listBots(currentGroup.id, 50, 0);
        setBots(resp.bots);
      } catch (e: unknown) {
        const msg = e instanceof Error ? e.message : "Failed to load bots";
        setError(msg);
      }
    })();
  }, [currentGroup]);

  const refreshRules = useCallback(async () => {
    if (!token) return;
    setLoading(true);
    try {
      const data = await listEmailRules(token, selectedIntegrationId || undefined);
      setRules(data);
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : "Failed to load rules";
      setError(msg);
    } finally {
      setLoading(false);
    }
  }, [token, selectedIntegrationId]);

  const refreshMonitoring = useCallback(async () => {
    if (!token || !selectedIntegrationId) return;
    try {
      const status = await getMonitoringStatus(token, selectedIntegrationId);
      setMonitoring(status);
      setMonitoringError(null);
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : "Failed to load monitoring status";
      setMonitoringError(msg);
    }
  }, [token, selectedIntegrationId]);

  useEffect(() => {
    if (token) {
      refreshRules();
      refreshMonitoring();
    }
  }, [token, selectedIntegrationId, refreshRules, refreshMonitoring]);

  // Periodic auto-refresh for monitoring
  useEffect(() => {
    if (!token || !selectedIntegrationId) return;
    const id = setInterval(() => {
      refreshMonitoring();
    }, 15000);
    return () => clearInterval(id);
  }, [token, selectedIntegrationId, refreshMonitoring]);

  const onCreateRule = async (payload: Parameters<typeof createEmailRule>[1]) => {
    if (!token) return;
    await createEmailRule(token, payload);
    await refreshRules();
  };

  const onUpdateRule = async (id: string, payload: Parameters<typeof updateEmailRule>[2]) => {
    if (!token) return;
    await updateEmailRule(token, id, payload);
    await refreshRules();
  };

  const onDeleteRule = async (id: string) => {
    if (!token) return;
    await deleteEmailRule(token, id);
    await refreshRules();
  };

  const onReorder = async (orderedIds: string[]) => {
    if (!token) return;
    await reorderEmailRules(token, orderedIds);
    await refreshRules();
  };

  const onTestRule = async (id: string, sample: { subject: string; body: string; sender?: string; folder?: string; labels?: string[] }) => {
    if (!token) return { matched: false, explanation: "No token" };
    return await testEmailRule(token, id, sample);
  };

  const onTogglePause = async () => {
    if (!token || !selectedIntegrationId) return;
    const next = !(monitoring?.is_paused ?? false);
    try {
      const updated = await setMonitoringPause(token, selectedIntegrationId, next);
      setMonitoring(updated);
      setMonitoringError(null);
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : "Failed to update pause state";
      setMonitoringError(msg);
    }
  };

  const fmt = (s?: string | null) => {
    if (!s) return "—";
    try { return new Date(s).toLocaleString(); } catch { return s; }
  };

  return (
    <DashboardLayout>
      <div className="container max-w-5xl mx-auto py-8 px-4 space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold">Email Monitoring Rules</h1>
            <p className="text-slate-600">Configure folders/labels, keywords, and draft generation bots.</p>
          </div>
        </div>

        <RuleForm
          integrations={integrations}
          bots={bots}
          defaultIntegrationId={selectedIntegrationId || undefined}
          onCreate={onCreateRule}
          onIntegrationChange={setSelectedIntegrationId}
        />

        {/* Monitoring status and controls */}
        {selectedIntegrationId && (
          <div className="rounded border border-slate-200 p-4 bg-slate-50">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-lg font-semibold">Monitoring Status</h2>
                <p className="text-slate-600">Provider polling for selected integration.</p>
              </div>
              <button
                onClick={onTogglePause}
                className={`px-3 py-1.5 rounded text-sm font-medium border ${monitoring?.is_paused ? 'bg-green-600 text-white border-green-700' : 'bg-yellow-500 text-white border-yellow-600'}`}
              >
                {monitoring?.is_paused ? 'Resume' : 'Pause'}
              </button>
            </div>

            {monitoringError && (
              <div className="mt-3 p-2 rounded bg-red-50 border border-red-200 text-red-700">{monitoringError}</div>
            )}

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 mt-4 text-sm">
              <div className="rounded bg-white border p-3">
                <div className="text-slate-500">Last Poll</div>
                <div className="font-medium">{fmt(monitoring?.last_poll_at)}</div>
              </div>
              <div className="rounded bg-white border p-3">
                <div className="text-slate-500">Last Success</div>
                <div className="font-medium">{fmt(monitoring?.last_success_at)}</div>
              </div>
              <div className="rounded bg-white border p-3">
                <div className="text-slate-500">Next Poll</div>
                <div className="font-medium">{fmt(monitoring?.next_poll_at)}</div>
              </div>
              <div className="rounded bg-white border p-3">
                <div className="text-slate-500">Errors (recent)</div>
                <div className="font-medium">{monitoring?.error_count ?? 0}</div>
              </div>
              <div className="sm:col-span-2 lg:col-span-3 rounded bg-white border p-3">
                <div className="text-slate-500">Last Error</div>
                <div className="font-medium">{monitoring?.last_error_at ? `${fmt(monitoring?.last_error_at)} — ${monitoring?.last_error_message ?? ''}` : '—'}</div>
              </div>
            </div>
          </div>
        )}

        <RulesList
          rules={rules}
          bots={bots}
          onUpdate={onUpdateRule}
          onDelete={onDeleteRule}
          onReorder={onReorder}
          onTest={(id: string) => setShowTestModal({ open: true, ruleId: id })}
        />

        {error && (
          <div className="p-3 rounded bg-red-50 border border-red-200 text-red-700">{error}</div>
        )}

        {loading && (
          <div className="text-slate-600">Loading rules…</div>
        )}

        <TestRuleModal
          open={showTestModal.open}
          onClose={() => setShowTestModal({ open: false })}
          ruleId={showTestModal.ruleId}
          onTest={onTestRule}
        />
      </div>
    </DashboardLayout>
  );
}
