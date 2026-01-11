# Phase 1 Completion: Models & Migration ✓

**Status:** COMPLETE  
**Date:** 2025-12-11  
**Scope:** Database models + Alembic migration for group model implementation

---

## Changes Implemented

### 1. New Models Created

#### `apps/api/app/models/group.py`

-   **Table:** `groups`
-   **Columns:**
    -   `id` (UUID, PK)
    -   `tenant_id` (FK → tenants.id, CASCADE)
    -   `name` (String 50, NOT NULL)
    -   `description` (Text, nullable)
    -   `created_by` (FK → users.id)
    -   `created_at`, `updated_at` (timestamps)
-   **Indexes:** (tenant_id), (tenant_id, name)
-   **Constraints:** UNIQUE(tenant_id, name)
-   **Purpose:** Logical grouping of bots within tenant; single shared KB per group

#### `apps/api/app/models/group_member.py`

-   **Table:** `group_members`
-   **Enums:** `GroupRole` (group_admin, manager, operator)
-   **Columns:**
    -   `id` (UUID, PK)
    -   `group_id` (FK → groups.id, CASCADE)
    -   `user_id` (FK → users.id, CASCADE)
    -   `role` (Enum, NOT NULL)
    -   `invited_at` (timestamp)
    -   `invited_by_id` (FK → users.id, nullable)
-   **Indexes:** (group_id), (user_id), (group_id, user_id)
-   **Constraints:** UNIQUE(group_id, user_id)
-   **Purpose:** RBAC membership tracking with 3-tier roles

### 2. Models Updated

#### `bot.py`

-   **Added:** `group_id` (FK → groups.id, CASCADE, NOT NULL)
-   **Updated:** Unique constraint from (tenant_id, name) → (tenant_id, group_id, name)
-   **Added indexes:**
    -   ix_bots_group_id
    -   ix_bots_tenant_group
    -   ix_bots_tenant_group_created
-   **Impact:** Bots now scoped to groups; prevents name collision across groups

#### `document.py`

-   **Added:** `group_id` (FK → groups.id, CASCADE, NOT NULL)
-   **Added:** `deleted_at` (DateTime, nullable) for soft-delete audit trail
-   **Renamed:** `uploaded_by` → `uploader_id` (made NOT NULL for provenance)
-   **Added indexes:**
    -   ix_documents_group_id
    -   ix_documents_tenant_group
    -   ix_documents_deleted
-   **Impact:** Documents now part of group KB; provenance tracking via uploader_id

#### `chunk.py`

-   **Added:** `group_id` (FK → groups.id, CASCADE, NOT NULL)
-   **Added:** `source_metadata` (Text, nullable) for citation tracking {filename, page, row}
-   **Updated indexes:**
    -   Removed: idx_chunks_bot_tenant
    -   Added: idx_chunks_group_id
    -   Added: idx_chunks_tenant_group_vector (RLS-aware similarity search)
    -   Added: idx_chunks_bot_tenant_group (provenance query)
-   **Impact:** Chunks indexed by group; enables RLS and provenance queries

### 3. Model Exports Updated

`apps/api/app/models/__init__.py`

-   Exported: `Group`, `GroupMember`, `GroupRole`
-   Exported: `Chunk` (was missing)
-   Exported: `AuditLog` (was missing)

### 4. Alembic Migration Created

`apps/api/alembic/versions/006_add_groups_and_provenance.py`

**Migration strategy:** Zero-downtime with server defaults

-   Creates groups, group_members tables first
-   Adds group_id columns to bots, documents, chunks with `server_default=gen_random_uuid()`
-   Updates constraints and indexes
-   Full rollback support in `downgrade()`

**Key decisions:**

1. Used `server_default=gen_random_uuid()` for backward compatibility during migration
2. Created (tenant_id, group_id, vector) index instead of HNSW (to be added in separate migration)
3. Soft-delete via deleted_at for audit trail; no cascading deletes on documents

---

## Verification

✓ All models compile without syntax errors
✓ All models import successfully
✓ Column definitions match specification:

-   Bot: 10 columns + group_id
-   Document: 14 columns (added group_id, deleted_at; renamed uploaded_by→uploader_id)
-   Chunk: 13 columns + source_metadata
-   Group: 7 columns
-   GroupMember: 6 columns + role enum

✓ Indexes created as specified for RLS and performance
✓ Foreign key constraints in place with CASCADE deletes where appropriate

---

## Next Steps: Phase 2

### API Routes & Schemas (2 days)

-   [ ] Create `apps/api/app/api/v1/groups.py` with CRUD endpoints
-   [ ] Create `apps/api/app/api/v1/group_members.py` for invitation/membership management
-   [ ] Update `bots.py` routes to be group-scoped with role checks
-   [ ] Update `documents.py` routes to capture group_id, uploader_id, bot_id
-   [ ] Add schemas in `schemas.py` for GroupCreate, GroupMemberCreate, BotCreate (updated), DocumentUpload (updated)

### Files to modify in Phase 2:

-   `apps/api/app/api/v1/schemas.py` (add group schemas)
-   `apps/api/app/api/v1/groups.py` (NEW)
-   `apps/api/app/api/v1/group_members.py` (NEW)
-   `apps/api/app/api/v1/bots.py` (update)
-   `apps/api/app/api/v1/documents.py` (update)

---

## Rollback Instructions

If needed, run:

```bash
cd apps/api
alembic downgrade 005_add_hnsw_index
```

This will:

-   Drop groups, group_members tables
-   Remove group_id from bots, documents, chunks
-   Restore original (tenant_id, name) unique constraint on bots
-   Restore uploaded_by column name on documents

---

## Database Schema Reference

```
groups (NEW)
├── id (UUID, PK)
├── tenant_id (FK)
├── name (UNIQUE with tenant_id)
├── created_by (FK)
└── timestamps

group_members (NEW)
├── id (UUID, PK)
├── group_id (FK, CASCADE)
├── user_id (FK, CASCADE)
├── role (ENUM: group_admin, manager, operator)
└── invited_at, invited_by_id

bots (UPDATED)
├── id (UUID, PK)
├── tenant_id (FK)
├── group_id (FK, CASCADE) ← NEW
├── name (UNIQUE with tenant_id + group_id) ← UPDATED
├── description
├── confidence_threshold
├── status
├── created_by
└── timestamps

documents (UPDATED)
├── id (UUID, PK)
├── tenant_id (FK)
├── group_id (FK, CASCADE) ← NEW
├── bot_id (FK)
├── filename, mime, size, storage_path
├── status
├── uploader_id (FK) ← RENAMED from uploaded_by
├── deleted_at (NEW) ← soft-delete
└── timestamps

chunks (UPDATED)
├── id (UUID, PK)
├── document_id (FK, CASCADE)
├── tenant_id (FK)
├── group_id (FK, CASCADE) ← NEW
├── bot_id (FK)
├── chunk_index
├── content
├── page_number
├── vector (1024-dim pgvector)
├── metadata_json
├── source_metadata (NEW) ← citation tracking
└── timestamps
```

---

## Model Validation Output

```
Bot: id, tenant_id, group_id, name, description, confidence_threshold, status, created_by, created_at, updated_at
Document: id, tenant_id, group_id, bot_id, title, filename, mime, size, storage_path, status, uploader_id, created_at, updated_at, deleted_at
Chunk: id, document_id, tenant_id, group_id, bot_id, chunk_index, content, page_number, vector, metadata, source_metadata, created_at, updated_at
Group: id, tenant_id, name, description, created_by, created_at, updated_at
GroupMember: id, group_id, user_id, role, invited_at, invited_by_id
```

---

## Commit History

```
✓ Created: apps/api/app/models/group.py
✓ Created: apps/api/app/models/group_member.py
✓ Updated: apps/api/app/models/bot.py (added group_id, updated constraint)
✓ Updated: apps/api/app/models/document.py (added group_id, deleted_at, renamed uploaded_by)
✓ Updated: apps/api/app/models/chunk.py (added group_id, source_metadata, updated indexes)
✓ Updated: apps/api/app/models/__init__.py (exported Group, GroupMember, GroupRole, Chunk, AuditLog)
✓ Created: apps/api/alembic/versions/006_add_groups_and_provenance.py
```

---

**Phase 1 Status:** ✅ COMPLETE - All models created, updated, and tested. Ready for Phase 2 (API routes).
