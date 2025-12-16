// Bot access API client functions

import {
  AccessSummary,
  SetAccessRequest,
  BulkSetAccessRequest,
  BulkSetAccessResponse,
} from '@/types/botAccess';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

export async function getBotAccess(botId: string, token: string): Promise<AccessSummary> {
  const response = await fetch(`${API_BASE_URL}/api/v1/bots/${botId}/access`, {
    method: 'GET',
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to get bot access');
  }

  return response.json();
}

export async function setDocumentAccess(
  botId: string,
  documentId: string,
  isAllowed: boolean,
  token: string
): Promise<void> {
  const data: SetAccessRequest = { is_allowed: isAllowed };

  const response = await fetch(
    `${API_BASE_URL}/api/v1/bots/${botId}/access/documents/${documentId}`,
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(data),
    }
  );

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to set document access');
  }
}

export async function setFolderAccess(
  botId: string,
  folderId: string,
  isAllowed: boolean,
  token: string
): Promise<void> {
  const data: SetAccessRequest = { is_allowed: isAllowed };

  const response = await fetch(
    `${API_BASE_URL}/api/v1/bots/${botId}/access/folders/${folderId}`,
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(data),
    }
  );

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to set folder access');
  }
}

export async function bulkSetAccess(
  botId: string,
  data: BulkSetAccessRequest,
  token: string
): Promise<BulkSetAccessResponse> {
  const response = await fetch(`${API_BASE_URL}/api/v1/bots/${botId}/access/bulk`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to bulk set access');
  }

  return response.json();
}
