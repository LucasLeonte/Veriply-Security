// Bot document access types for bot-level access control

export interface FolderAccessItem {
  id: string;
  name: string;
  allowed: boolean;
  has_explicit_access: boolean;
  has_doc_overrides: boolean;
}

export interface DocumentAccessItem {
  id: string;
  name: string;
  folder_id: string | null;
  allowed: boolean;
  has_explicit_access: boolean;
  explicit_allowed: boolean | null;
}

export interface AccessSummary {
  folders: FolderAccessItem[];
  documents: DocumentAccessItem[];
}

export interface SetAccessRequest {
  is_allowed: boolean;
}

export interface BulkSetAccessRequest {
  document_ids?: string[];
  folder_ids?: string[];
  is_allowed: boolean;
}

export interface BulkSetAccessResponse {
  message: string;
  documents_updated: number;
  folders_updated: number;
}
