// Folders API client functions

import { Folder, FolderCreate, FolderUpdate } from '@/types/folder';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

export async function createFolder(
  groupId: string,
  data: FolderCreate,
  token: string
): Promise<Folder> {
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
  token: string,
  includeDeleted: boolean = false
): Promise<Folder[]> {
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
  folderId: string,
  token: string
): Promise<Folder> {
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
  data: FolderUpdate,
  token: string
): Promise<Folder> {
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
  folderId: string,
  token: string
): Promise<void> {
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
