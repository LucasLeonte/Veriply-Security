// Folder types for group-scoped KB organization

export interface Folder {
  id: string;
  tenant_id: string;
  group_id: string;
  name: string;
  created_by: string;
  created_at: string;
  updated_at: string;
  stats?: FolderStats;
}

export interface FolderStats {
  doc_count: number;
}

export interface FolderCreate {
  name: string;
}

export interface FolderUpdate {
  name: string;
}
