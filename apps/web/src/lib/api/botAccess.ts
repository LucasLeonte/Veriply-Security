// Bot access API client functions

import {
  AccessSummary,
  SetAccessRequest,
  BulkSetAccessRequest,
  BulkSetAccessResponse,
} from '@/types/botAccess';
import { getAccessToken } from '@/lib/auth';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

async function getAuthToken(): Promise<string | null> {
  if (typeof window === "undefined") {
    return null;
  }
  return getAccessToken();
}

export async function getBotAccess(botId: string): Promise<AccessSummary> {
  const token = await getAuthToken();
  if (!token) {
    throw new Error("Not authenticated");
  }

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
  data: SetAccessRequest
): Promise<void> {
  const token = await getAuthToken();
  if (!token) {
    throw new Error("Not authenticated");
  }

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
  data: SetAccessRequest
): Promise<void> {
  const token = await getAuthToken();
  if (!token) {
    throw new Error("Not authenticated");
  }

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
  data: BulkSetAccessRequest
): Promise<BulkSetAccessResponse> {
  const token = await getAuthToken();
  if (!token) {
    throw new Error("Not authenticated");
  }

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

// Export API object
export const botAccessApi = {
  getBotAccess,
  setDocumentAccess,
  setFolderAccess,
  bulkSetAccess,
};
