// Folders API client functions

import { Folder, FolderCreate, FolderUpdate } from '@/types/folder';
import { getAccessToken } from '@/lib/auth';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

async function getAuthToken(): Promise<string | null> {
  if (typeof window === "undefined") {
    return null;
  }
  return getAccessToken();
}

export async function createFolder(
  groupId: string,
  data: FolderCreate
): Promise<Folder> {
  const token = await getAuthToken();
  if (!token) {
    throw new Error("Not authenticated");
  }

  const response = await fetch(`${API_BASE_URL}/api/v1/groups/${groupId}/folders`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to create folder');
  }

  return response.json();
}

export async function listFolders(
  groupId: string,
  includeDeleted: boolean = false
): Promise<Folder[]> {
  const token = await getAuthToken();
  if (!token) {
    throw new Error("Not authenticated");
  }

  const url = new URL(`${API_BASE_URL}/api/v1/groups/${groupId}/folders`);
  if (includeDeleted) {
    url.searchParams.set('include_deleted', 'true');
  }

  const response = await fetch(url.toString(), {
    method: 'GET',
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to list folders');
  }

  return response.json();
}

export async function getFolder(
  groupId: string,
  folderId: string
): Promise<Folder> {
  const token = await getAuthToken();
  if (!token) {
    throw new Error("Not authenticated");
  }

  const response = await fetch(
    `${API_BASE_URL}/api/v1/groups/${groupId}/folders/${folderId}`,
    {
      method: 'GET',
      headers: {
        Authorization: `Bearer ${token}`,
      },
    }
  );

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to get folder');
  }

  return response.json();
}

export async function updateFolder(
  groupId: string,
  folderId: string,
  data: FolderUpdate
): Promise<Folder> {
  const token = await getAuthToken();
  if (!token) {
    throw new Error("Not authenticated");
  }

  const response = await fetch(
    `${API_BASE_URL}/api/v1/groups/${groupId}/folders/${folderId}`,
    {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(data),
    }
  );

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to update folder');
  }

  return response.json();
}

export async function deleteFolder(
  groupId: string,
  folderId: string
): Promise<void> {
  const token = await getAuthToken();
  if (!token) {
    throw new Error("Not authenticated");
  }

  const response = await fetch(
    `${API_BASE_URL}/api/v1/groups/${groupId}/folders/${folderId}`,
    {
      method: 'DELETE',
      headers: {
        Authorization: `Bearer ${token}`,
      },
    }
  );

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to delete folder');
  }
}

// Export API object
export const foldersApi = {
  createFolder,
  listFolders,
  getFolder,
  updateFolder,
  deleteFolder,
};
