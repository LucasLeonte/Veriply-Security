const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

export type EmailRule = {
  id: string;
  tenant_id: string;
  user_id: string;
  integration_id: string;
  bot_id: string;
  folder_labels?: string[];
  include_keywords?: string[];
  exclude_keywords?: string[];
  priority: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
};

export type CreateEmailRuleRequest = {
  integration_id: string;
  bot_id: string;
  folder_labels?: string[];
  include_keywords?: string[];
  exclude_keywords?: string[];
  priority?: number;
  is_active?: boolean;
};

export type UpdateEmailRuleRequest = Partial<CreateEmailRuleRequest>;

export async function listEmailRules(token: string, integrationId?: string): Promise<EmailRule[]> {
  const url = new URL(`${API_BASE_URL}/api/v1/email-rules`);
  if (integrationId) url.searchParams.set("integration_id", integrationId);
  const res = await fetch(url.toString(), {
    credentials: "include",
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error("Failed to list rules");
  return await res.json();
}

export async function createEmailRule(token: string, payload: CreateEmailRuleRequest): Promise<EmailRule> {
  const res = await fetch(`${API_BASE_URL}/api/v1/email-rules`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    credentials: "include",
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error("Failed to create rule");
  return await res.json();
}

export async function updateEmailRule(token: string, id: string, payload: UpdateEmailRuleRequest): Promise<EmailRule> {
  const res = await fetch(`${API_BASE_URL}/api/v1/email-rules/${id}`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    credentials: "include",
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error("Failed to update rule");
  return await res.json();
}

export async function deleteEmailRule(token: string, id: string): Promise<void> {
  const res = await fetch(`${API_BASE_URL}/api/v1/email-rules/${id}`, {
    method: "DELETE",
    headers: {
      Authorization: `Bearer ${token}`,
    },
    credentials: "include",
  });
  if (!res.ok) throw new Error("Failed to delete rule");
}

export async function reorderEmailRules(token: string, orderedIds: string[]): Promise<void> {
  const res = await fetch(`${API_BASE_URL}/api/v1/email-rules/reorder`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    credentials: "include",
    body: JSON.stringify({ ordered_ids: orderedIds }),
  });
  if (!res.ok) throw new Error("Failed to reorder rules");
}

export type EmailSampleRequest = {
  subject: string;
  body: string;
  sender?: string;
  folder?: string;
  labels?: string[];
};

export async function testEmailRule(token: string, id: string, sample: EmailSampleRequest): Promise<{ matched: boolean; rule_id?: string; explanation: string; }> {
  const res = await fetch(`${API_BASE_URL}/api/v1/email-rules/${id}/test`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    credentials: "include",
    body: JSON.stringify(sample),
  });
  if (!res.ok) throw new Error("Failed to test rule");
  return await res.json();
}
