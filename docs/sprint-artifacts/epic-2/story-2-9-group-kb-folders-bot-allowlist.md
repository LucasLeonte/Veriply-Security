# Story 2.9: Group KB Folders and Bot Document Allowlist

**Epic:** 2. Bot & Knowledge Management  
**Status:** ready-for-dev  
**Assigned to:** Dario  
**Blocked by:** null

## Story

As a User,  
I want to organize group documents into folders and control which documents/folders each bot can access,  
so that I can structure my knowledge base and precisely scope bot knowledge domains within a shared group KB.

## Acceptance Criteria

### AC1: Group-Scoped Folders (Backend)

- [ ] `folders` table created with columns:
  - `id` (UUID, PK)
  - `tenant_id` (UUID, FK to tenants, NOT NULL)
  - `group_id` (UUID, FK to groups, NOT NULL)
  - `name` (VARCHAR, NOT NULL)
  - `created_by` (UUID, FK to users)
  - `created_at`, `updated_at` (TIMESTAMP)
  - `deleted_at` (TIMESTAMP, nullable, for soft-delete)
- [ ] Unique constraint: `(tenant_id, group_id, name)` enforces unique folder names per group
- [ ] RLS: All folder queries include `tenant_id` and `group_id` filters
- [ ] Index: `(tenant_id, group_id)`, `(group_id)`

### AC2: Document-Folder Association (Backend)

- [ ] `documents` table updated with:
  - `folder_id` (UUID, FK to folders, nullable)
  - Default: `folder_id = NULL` (root level, no folder)
- [ ] Index: `(folder_id)` for folder-based queries
- [ ] Foreign key constraint: `folder_id` references `folders.id` ON DELETE SET NULL
- [ ] When folder deleted (soft-delete), documents remain in group but `folder_id` set to NULL

### AC3: Bot-Document Allowlist (Backend)

- [ ] `bot_document_access` table created with columns:
  - `id` (UUID, PK)
  - `tenant_id` (UUID, FK to tenants, NOT NULL)
  - `group_id` (UUID, FK to groups, NOT NULL)
  - `bot_id` (UUID, FK to bots, NOT NULL)
  - `document_id` (UUID, FK to documents, nullable)
  - `folder_id` (UUID, FK to folders, nullable)
  - `is_allowed` (BOOLEAN, NOT NULL)
  - `created_at`, `updated_at` (TIMESTAMP)
- [ ] Constraint: Either `document_id` OR `folder_id` must be set (not both, not neither)
- [ ] Unique constraint: `(bot_id, document_id)` OR `(bot_id, folder_id)`
- [ ] RLS: All queries include `tenant_id` and `group_id` filters
- [ ] Index: `(bot_id, document_id)`, `(bot_id, folder_id)`, `(tenant_id, group_id)`

### AC4: Access Resolution Logic (Backend)

- [ ] When checking if bot can access a document:
  1. Check for explicit document-level access (`bot_document_access` WHERE `document_id`)
  2. If no explicit doc access, check folder-level access (`bot_document_access` WHERE `folder_id`)
  3. If neither exists, default: bot CANNOT access document (deny-by-default)
- [ ] Document-level access OVERRIDES folder-level access
- [ ] Example: Folder allowed, doc explicitly denied → doc is denied
- [ ] Example: Folder denied, doc explicitly allowed → doc is allowed

### AC5: Folder CRUD Service (Backend)

- [ ] `FolderService.create_folder(db, tenant_id, group_id, name, created_by)` → Folder
- [ ] `FolderService.get_folder(db, folder_id, tenant_id, group_id)` → Folder
- [ ] `FolderService.list_group_folders(db, tenant_id, group_id, include_deleted=False)` → List[Folder]
- [ ] `FolderService.update_folder(db, folder_id, tenant_id, group_id, name)` → Folder
- [ ] `FolderService.soft_delete_folder(db, folder_id, tenant_id, group_id)` → Folder
- [ ] `FolderService.get_folder_stats(db, folder_id, tenant_id, group_id)` → {doc_count, chunk_count}
- [ ] All operations enforce RLS: `tenant_id` + `group_id`
- [ ] Audit logging for create/delete/rename

### AC6: Bot Document Access Service (Backend)

- [ ] `BotAccessService.set_document_access(db, bot_id, document_id, is_allowed, tenant_id, group_id)` → BotDocumentAccess
- [ ] `BotAccessService.set_folder_access(db, bot_id, folder_id, is_allowed, tenant_id, group_id)` → BotDocumentAccess
- [ ] `BotAccessService.get_bot_accessible_documents(db, bot_id, tenant_id, group_id)` → List[Document]
- [ ] `BotAccessService.check_document_access(db, bot_id, document_id, tenant_id, group_id)` → bool
- [ ] `BotAccessService.bulk_set_access(db, bot_id, document_ids, is_allowed, tenant_id, group_id)` → int (count updated)
- [ ] `BotAccessService.get_access_summary(db, bot_id, tenant_id, group_id)` → {folders: [{id, name, allowed}], documents: [{id, name, folder_id, allowed}]}
- [ ] All operations enforce RLS
- [ ] Audit logging for access changes

### AC7: API Routes - Folders (Backend)

- [ ] `POST /api/v1/groups/{group_id}/folders` - Create folder
  - Body: `{name: string}`
  - Returns: Folder object
  - Status: 201 on success, 400 if duplicate name, 403 if not group member
- [ ] `GET /api/v1/groups/{group_id}/folders` - List all folders in group
  - Query params: `include_deleted` (bool, default false)
  - Returns: Array of folders with stats (doc_count)
  - Status: 200
- [ ] `GET /api/v1/groups/{group_id}/folders/{folder_id}` - Get folder details
  - Returns: Folder object with stats
  - Status: 200 or 404
- [ ] `PATCH /api/v1/groups/{group_id}/folders/{folder_id}` - Update folder name
  - Body: `{name: string}`
  - Returns: Updated folder
  - Status: 200 or 400 if duplicate
- [ ] `DELETE /api/v1/groups/{group_id}/folders/{folder_id}` - Soft-delete folder
  - Returns: Success message
  - Status: 204
  - Side effect: All documents in folder have `folder_id` set to NULL

### AC8: API Routes - Bot Document Access (Backend)

- [ ] `GET /api/v1/bots/{bot_id}/access` - Get access summary for bot
  - Returns: `{folders: [{id, name, allowed}], documents: [{id, name, folder_id, allowed}]}`
  - Status: 200
- [ ] `POST /api/v1/bots/{bot_id}/access/documents/{document_id}` - Set document access
  - Body: `{is_allowed: boolean}`
  - Returns: Success message
  - Status: 200
- [ ] `POST /api/v1/bots/{bot_id}/access/folders/{folder_id}` - Set folder access
  - Body: `{is_allowed: boolean}`
  - Returns: Success message
  - Status: 200
- [ ] `POST /api/v1/bots/{bot_id}/access/bulk` - Bulk set access
  - Body: `{document_ids: UUID[], folder_ids: UUID[], is_allowed: boolean}`
  - Returns: `{documents_updated: int, folders_updated: int}`
  - Status: 200
- [ ] All routes enforce: user is group member, bot belongs to group

### AC9: Frontend - KB Folder Management UI

- [ ] In group KB view, show folder list with expand/collapse
- [ ] "Add Folder" button opens modal with name input
- [ ] Each folder shows:
  - Folder name
  - Document count
  - "Rename" button (opens inline edit or modal)
  - "Delete" button (confirmation: "Delete folder? Documents will move to root.")
- [ ] Documents can be moved into folders:
  - Drag-and-drop (optional, can defer)
  - OR: Document context menu → "Move to Folder" → Select folder
- [ ] Root-level documents shown separately (no folder)
- [ ] Folder view hierarchical but flat (one level)

### AC10: Frontend - Bot Document Toggle UI

- [ ] Clicking a bot opens detail view with "Documents & Access" tab
- [ ] Tab shows:
  - **Folders section**: List of all group folders with toggle switch
    - Toggle ON = all docs in folder allowed
    - Toggle OFF = all docs in folder denied
    - Partially ON state if some docs in folder have overrides
  - **Documents section**: List of all group documents (grouped by folder + root)
    - Each document has toggle switch
    - Document toggle overrides folder toggle
    - Visual indicator if doc has explicit override
- [ ] Toggling folder:
  - Sends `POST /bots/{bot_id}/access/folders/{folder_id}` with `is_allowed`
  - All documents in folder inherit state UNLESS they have explicit override
- [ ] Toggling document:
  - Sends `POST /bots/{bot_id}/access/documents/{doc_id}` with `is_allowed`
  - Document gets explicit access record
  - If folder was toggled ON/OFF, folder toggle shows "partial" state
- [ ] "Allow All" button: sets all folders and docs to allowed
- [ ] "Deny All" button: sets all folders and docs to denied

### AC11: Frontend - Toggle State Logic

- [ ] Folder toggle state resolved as:
  - ON: folder access record exists with `is_allowed = true` AND no doc overrides
  - OFF: folder access record exists with `is_allowed = false` OR no record
  - PARTIAL: folder has access record but one or more docs have explicit overrides
- [ ] Document toggle state resolved as:
  - ON: explicit doc access with `is_allowed = true` OR (folder allowed AND no doc override)
  - OFF: explicit doc access with `is_allowed = false` OR (folder denied OR no record) AND no doc override
- [ ] When user toggles document inside a toggled folder:
  - Document gets explicit access record
  - Folder toggle state becomes PARTIAL (not fully ON/OFF anymore)

### AC12: Backward Compatibility & Migration

- [ ] Existing documents have `folder_id = NULL` (root level)
- [ ] No breaking changes to existing document upload/processing
- [ ] Legacy bot-document associations (if any) migrated to `bot_document_access` table
- [ ] Update document processing to respect bot access filters when generating responses

## Tasks / Subtasks

### 1) Database Schema & Migration

- [ ] Create `folders` table with columns, indexes, constraints
- [ ] Alter `documents` table: add `folder_id` column with FK
- [ ] Create `bot_document_access` table with columns, indexes, constraints
- [ ] Write Alembic migration script
- [ ] Test migration up/down
- [ ] Apply migration to dev database

### 2) Backend - Folder Service

- [ ] Implement `FolderService.create_folder`
- [ ] Implement `FolderService.get_folder`
- [ ] Implement `FolderService.list_group_folders`
- [ ] Implement `FolderService.update_folder`
- [ ] Implement `FolderService.soft_delete_folder`
- [ ] Implement `FolderService.get_folder_stats`
- [ ] Add RLS enforcement to all queries
- [ ] Add audit logging

### 3) Backend - Bot Access Service

- [ ] Implement `BotAccessService.set_document_access`
- [ ] Implement `BotAccessService.set_folder_access`
- [ ] Implement `BotAccessService.get_bot_accessible_documents`
- [ ] Implement `BotAccessService.check_document_access` (with override logic)
- [ ] Implement `BotAccessService.bulk_set_access`
- [ ] Implement `BotAccessService.get_access_summary`
- [ ] Add RLS enforcement
- [ ] Add audit logging

### 4) Backend - API Routes for Folders

- [ ] Implement `POST /api/v1/groups/{group_id}/folders`
- [ ] Implement `GET /api/v1/groups/{group_id}/folders`
- [ ] Implement `GET /api/v1/groups/{group_id}/folders/{folder_id}`
- [ ] Implement `PATCH /api/v1/groups/{group_id}/folders/{folder_id}`
- [ ] Implement `DELETE /api/v1/groups/{group_id}/folders/{folder_id}`
- [ ] Add RBAC checks (group membership)
- [ ] Add request validation (Pydantic schemas)

### 5) Backend - API Routes for Bot Access

- [ ] Implement `GET /api/v1/bots/{bot_id}/access`
- [ ] Implement `POST /api/v1/bots/{bot_id}/access/documents/{document_id}`
- [ ] Implement `POST /api/v1/bots/{bot_id}/access/folders/{folder_id}`
- [ ] Implement `POST /api/v1/bots/{bot_id}/access/bulk`
- [ ] Add RBAC checks (group membership, bot ownership)
- [ ] Add request validation

### 6) Backend - Update Document Processing

- [ ] Modify RAG search to filter by bot accessible documents
- [ ] Update `get_bot_accessible_documents` to include folder-based filtering
- [ ] Ensure chunk queries respect bot access (join with `bot_document_access`)

### 7) Frontend - Folder Models & API Client

- [ ] Define TypeScript types: `Folder`, `FolderStats`, `BotAccessSummary`
- [ ] Implement API client methods:
  - `createFolder`, `listFolders`, `updateFolder`, `deleteFolder`
  - `getBotAccess`, `setDocumentAccess`, `setFolderAccess`, `bulkSetAccess`

### 8) Frontend - KB Folder Management Component

- [ ] Create `FolderList` component showing folders with stats
- [ ] Create `AddFolderModal` component with name input
- [ ] Create `RenameFolderModal` component
- [ ] Create `DeleteFolderConfirmation` modal
- [ ] Implement folder expand/collapse UI
- [ ] Add "Move to Folder" option to document context menu
- [ ] Integrate with existing KB document list view

### 9) Frontend - Bot Document Toggle Component

- [ ] Create `BotDocumentAccessPanel` component
- [ ] Implement folder toggle list with ON/OFF/PARTIAL states
- [ ] Implement document toggle list grouped by folder
- [ ] Add "Allow All" and "Deny All" buttons
- [ ] Handle toggle state changes (folder/doc)
- [ ] Show visual indicators for overrides
- [ ] Integrate with bot detail view

### 10) Backend - Unit Tests

- [ ] Test `FolderService` CRUD operations
- [ ] Test `FolderService` RLS enforcement
- [ ] Test `BotAccessService` access resolution logic (overrides)
- [ ] Test `BotAccessService` bulk operations
- [ ] Test unique folder name constraint
- [ ] Test folder deletion → documents `folder_id` set to NULL

### 11) Backend - Integration Tests

- [ ] Test folder API routes end-to-end
- [ ] Test bot access API routes end-to-end
- [ ] Test access resolution: doc override > folder access
- [ ] Test RAG search respects bot access filters
- [ ] Test audit logging for folder/access changes

### 12) Frontend - Component Tests

- [ ] Test `FolderList` rendering and interactions
- [ ] Test `AddFolderModal` create flow
- [ ] Test `BotDocumentAccessPanel` toggle logic
- [ ] Test folder/document toggle state resolution
- [ ] Test "Allow All" / "Deny All" bulk actions

## Dev Notes

### Key Design Decisions

1. **Flat folder hierarchy**: One level only. Documents can be in a folder or root. No nested folders.
2. **Document override precedence**: Explicit document access ALWAYS overrides folder access.
3. **Toggle behavior**: When toggling a document inside a toggled folder, folder becomes "partial" (not fully toggled anymore).
4. **Deny-by-default**: If no access record exists for bot+document, bot CANNOT access document.
5. **Soft-delete folders**: Deleting folder sets documents' `folder_id = NULL`, preserving documents.

### Access Resolution Algorithm

```python
def can_bot_access_document(bot_id, document_id):
    # 1. Check explicit document access
    doc_access = query(bot_document_access, bot_id=bot_id, document_id=document_id)
    if doc_access:
        return doc_access.is_allowed
    
    # 2. Check folder access
    document = query(documents, id=document_id)
    if document.folder_id:
        folder_access = query(bot_document_access, bot_id=bot_id, folder_id=document.folder_id)
        if folder_access:
            return folder_access.is_allowed
    
    # 3. Default: deny
    return False
```

### Frontend Toggle State Algorithm

```javascript
function getFolderToggleState(folder, documents, accessRecords) {
  const folderRecord = accessRecords.find(r => r.folder_id === folder.id);
  const docsInFolder = documents.filter(d => d.folder_id === folder.id);
  const docOverrides = docsInFolder.filter(d => 
    accessRecords.some(r => r.document_id === d.id)
  );
  
  if (docOverrides.length > 0) return 'PARTIAL';
  if (folderRecord?.is_allowed) return 'ON';
  return 'OFF';
}
```

### Project Structure

- Backend:
  - Models: `apps/api/app/models/folder.py`, `apps/api/app/models/bot_document_access.py`
  - Services: `apps/api/app/services/folder_service.py`, `apps/api/app/services/bot_access_service.py`
  - Routes: `apps/api/app/routes/folders.py`, `apps/api/app/routes/bots.py` (extend)
  - Migration: `apps/api/alembic/versions/xxx_add_folders_and_bot_access.py`
  - Tests: `apps/api/tests/services/test_folder_service.py`, `apps/api/tests/services/test_bot_access_service.py`
- Frontend:
  - Types: `apps/web/src/types/folder.ts`, `apps/web/src/types/botAccess.ts`
  - API: `apps/web/src/lib/api/folders.ts`, `apps/web/src/lib/api/botAccess.ts`
  - Components: `apps/web/src/components/knowledge-base/FolderList.tsx`, `apps/web/src/components/bots/BotDocumentAccessPanel.tsx`
  - Tests: `apps/web/__tests__/components/knowledge-base/`, `apps/web/__tests__/components/bots/`

### References

- [Phase 3: Services Complete](../PHASE-3-SERVICES-COMPLETE.md)
- [Story 2.3: Document Upload API](./story-2-3-document-upload-api.md)
- [Story 2.5: Knowledge Base Management UI](./story-2-5-knowledge-base-management-ui.md)
- [Architecture: Group-scoped Knowledge Base](../../architecture.md)

## Dev Agent Record

### Context Reference

<!-- Path(s) to story context XML will be added here by context workflow -->

### Agent Model Used

Claude Sonnet 4.5

### Debug Log

### Completion Notes

### File List

### Change Log

## Status

Status: ready-for-dev  
Created: 2025-12-16  
Updated: 2025-12-16
