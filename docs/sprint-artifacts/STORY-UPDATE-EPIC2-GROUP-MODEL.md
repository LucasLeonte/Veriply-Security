# Story Update: Epic 2 Refactor for Group Model

**Status:** Ready for Development  
**Priority:** High (blocks implementation)  
**Date Created:** 2025-12-11  
**Owner:** Dev Lead

---

## Overview

Epic 2 stories (2.1–2.7) were written for the old model: **Tenant → Bots (isolated KB per bot)**.

The new model is: **Tenant → Groups → Bots (shared KB per group, bot provenance)**.

This is a **model refactor**, not a rewrite. Update the existing stories to reflect the new architecture.

---

## Change Summary

### Old Model

-   Users create bots within a tenant
-   Each bot has its own isolated KB
-   No explicit "group" concept
-   No bot/uploader provenance tracking

### New Model

-   Users create groups within a tenant
-   Users invite group members with roles (Group Admin, Manager, Operator)
-   Multiple bots per group share a **single Group KB**
-   Documents tagged with `bot_id`, `uploader_id` for provenance
-   RLS enforced on `(tenant_id, group_id)` + role-based permissions

---

## Stories to Update

### Story 2.1: Bot Creation & Configuration

**Current (Old Model):**

```
As a User,
I want to create and configure multiple bots within my organization,
So that I can separate knowledge bases by department or use case.
```

**Update to (New Model):**

```
As a Manager or Group Admin,
I want to create and configure multiple bots within my group,
So that I can specialize bots by function and share a single Knowledge Base.
```

**Changes to Acceptance Criteria:**

1. **Prereq:** Update from `Story 1.6` → `Story 1.8` (group membership now required)
2. **Permissions:** Only Manager+ can create bots; Operators cannot
3. **Scoping:** All bots in the form should say "Create Bot for [Current Group]"
4. **Technical Notes:**
    - Add: `group_id` to database schema note
    - Add: "All bots in a group read/write to the same KB"
    - Clarify: Bot names unique **within group**, not tenant
5. **Coverage:** Same FRs (FR7, FR8, FR9) but group-scoped

**Specific Text Changes:**

-   "within my organization" → "within my group"
-   "separate knowledge bases by department" → "specialize bots by function and share a single Knowledge Base"
-   "Story 1.6" → "Story 1.8"
-   Add AC: "Operators cannot create bots (Manager+ only)"
-   Add AC: "All bots in a group read/write to the same KB"
-   Technical note: "Database: `bots` table with tenant_id + **group_id** + RLS"
-   Technical note: Add "All bots in a group read/write to the same KB"

---

### Story 2.2: Bot Duplication & Deletion

**Current (Old Model):**

```
As a User,
I want to duplicate or delete bots,
So that I can quickly create similar bots or clean up unused ones.
```

**Update to (New Model):**

```
As a Manager or Group Admin,
I want to update bot settings and delete bots,
So that I can refine bot configurations or remove outdated bots from my group.
```

**Changes to Acceptance Criteria:**

1. **Remove:** "Duplicate" feature (not in new model; keep focus on update/delete)
    - Alternatively: Keep duplication but state it copies settings, not KB (since KB is shared)
2. **Change deletion behavior:**
    - OLD: "Bot record is deleted, All documents are deleted, All embeddings are deleted"
    - NEW: "Bot record is deleted, The Group KB remains (shared across group), All chat sessions for this bot are deleted"
3. **Permissions:** Only Manager+ can delete; Operators cannot
4. **Technical Notes:**
    - OLD: "Cascade delete: bot → documents → chunks → embeddings"
    - NEW: "Cascade delete: bot → chat_sessions only (NOT documents/chunks, as KB is group-scoped)"
5. **Coverage:** FR10 (adapted to group model) - remove duplication mention if dropped

**Specific Text Changes:**

-   Rename to "Bot Update & Deletion" (not duplication)
-   Remove "Duplicate" AC entirely OR keep it but change to: "New bot created with same settings; **Empty KB share** (all bots in group share the same KB)"
-   Change deletion warning: "This will permanently delete the bot. The Group KB will be preserved (shared by other bots)."
-   Delete AC: Update to show documents remain, only bot is deleted
-   Technical note: Change cascade delete description
-   Add AC: "Deletion is async with progress indicator"

---

### Story 2.3: Document Upload API

**Current (Old Model):**

```
As a User,
I want to upload documents to my bot's knowledge base,
```

**Update to (New Model):**

```
As a Manager or Operator,
I want to upload documents to my group's shared Knowledge Base,
```

**Changes to Acceptance Criteria:**

1. **Permission:** Operators CAN upload (unlike bot creation)
2. **Location:** Upload goes to **Group KB**, not bot-specific KB
3. **Metadata:** Capture `bot_id`, `uploader_id`, `group_id` during upload
4. **Technical Notes:**
    - Add metadata capture: tenant_id, group_id, bot_id, uploader_id, timestamp
    - Clarify: "Files stored in S3 with tenant/group/bot path prefix"
5. **Coverage:** FR13 (group-scoped)

**Specific Text Changes:**

-   "my bot's knowledge base" → "my group's shared Knowledge Base"
-   Add AC: "Upload metadata is recorded: tenant_id, group_id, bot_id, uploader_id, timestamp"
-   Add AC: "Operators can upload; Group Admin and Manager can upload"
-   Technical note: Add metadata fields
-   Technical note: "Covers FR13 (group-scoped)"
-   Update prereq: "Story 2.1" → "Story 2.3" (depends on KB view story existing first)

---

### Story 2.4: Document Processing Pipeline

**Current (Old Model):**

```
As a System,
I want to extract, chunk, and embed uploaded documents,
```

**Update to (New Model):**

```
As a System,
I want to extract, chunk, and embed uploaded documents with bot/uploader provenance,
```

**Changes to Acceptance Criteria:**

1. **Provenance:** Store `bot_id`, `uploader_id`, `group_id` in each chunk
2. **Metadata:** Each chunk includes:
    - tenant_id, group_id, bot_id (which bot uploaded)
    - uploader_id, document_id, chunk_index
    - created_at, source metadata (filename, page/row)
3. **Embeddings table structure:** Include composite index `(tenant_id, group_id, embedding)` for RLS-aware queries
4. **Technical Notes:**
    - Update embedding model reference if needed (currently "bge-m3" → check if still correct or use "nomic-embed-text")
    - Add RLS policy note: "RLS policy: only users in tenant+group can see/query chunks"
5. **Coverage:** FR14, FR15, FR16 (with group/bot provenance)

**Specific Text Changes:**

-   Title: Add "with Provenance"
-   AC: Add "metadata is recorded: tenant_id, group_id, bot_id, uploader_id, created_at"
-   AC: "Store embeddings in pgvector with metadata: tenant_id, group_id, bot_id, document_id, chunk_index, created_at"
-   Technical note: Add composite index description
-   Technical note: Add RLS policy note
-   Technical note: Update embedding model spec (verify: bge-m3 vs nomic-embed-text)
-   Coverage: "Covers FR14, FR15, FR16 (with group/bot provenance)"

---

### Story 2.5: Group Knowledge Base View & Provenance (NEW - INSERT)

**Status:** Already added in epic refactor, but dev should validate it exists.

**Location:** Between 2.4 and 2.6 in updated epics.md

**Prereq:** Story 2.1 (need groups/bots first)

**Content Check:**

-   Includes document provenance display (uploader, bot_id)
-   Shows which bots reference each document
-   Permission checks: Operators view only, Manager+ can delete
-   Soft-delete support for audit trail

---

### Story 2.6–2.7 (Document Management)

**Current:** "Story 2.5: View Documents" and "Story 2.6: Document Reprocessing"

**Update:** These remain largely unchanged but should reference Group KB instead of bot-specific KB.

**Changes:**

-   Prereq: Update to reference new story numbers
-   Text: "view my bot's documents" → "view my group's knowledge base documents"
-   Access control: Document actions scoped to group membership

---

## Testing Updates

### Story 9 (Testing & QA) Validations

Ensure the following tests are added:

1. **Story 9.1:** Unit Tests for KB Provenance

    - ✓ Already drafted; verify chunk metadata fields match schema

2. **Story 9.2:** RLS Integration Tests

    - ✓ Already drafted; test (tenant_id, group_id) isolation

3. **Story 9.3:** E2E Multi-Bot KB Upload & Query

    - ✓ Already drafted; covers the exact scenario (2 bots, 1 KB)

4. **Story 9.4:** RBAC Enforcement Tests

    - ✓ Already drafted; verify Manager+ CRUD, Operator read-only

5. **Story 9.5:** Ingestion Tagging & Audit Trail
    - ✓ Already drafted; verify bot_id, uploader_id recorded

---

## Implementation Checklist for Dev

-   [ ] Review this document with team
-   [ ] Update Story 2.1 acceptance criteria and prereqs
-   [ ] Update Story 2.2 to remove duplication (or adapt it), change deletion behavior
-   [ ] Update Story 2.3 permissions and metadata capture
-   [ ] Update Story 2.4 to include provenance/chunk metadata
-   [ ] Verify Story 2.5 (Group KB View) exists in epics.md
-   [ ] Verify Stories 2.6–2.7 (if they exist) reference Group KB
-   [ ] Update any technical notes/database schema comments
-   [ ] Verify FRs coverage in each story (all should be group-scoped)
-   [ ] Cross-reference Epic 9 testing stories
-   [ ] Update any implementation guides or database migration notes

---

## Files to Update

-   **Primary:** `docs/epics.md` (Epic 2 stories 2.1–2.7)
-   **Secondary:**
    -   `docs/tech-spec.md` (verify database schema diagrams reflect group model)
    -   `docs/architecture.md` (verify group/bot/KB sections match)
    -   Any sprint artifacts referencing old Epic 2 structure

---

## Questions for Dev

1. Should Story 2.2 keep "Duplicate" or drop it? (New model: duplicating settings but KB is shared anyway)
2. Embedding model: Confirm `bge-m3` vs `nomic-embed-text` for Story 2.4
3. Should soft-delete for documents be tracked in audit_logs table?

---

## Timeline

-   **Target:** Complete story updates within 1 sprint
-   **Blocker:** Implementation cannot start until these are finalized
-   **Depends on:** Architecture & Tech-Spec finalization (both complete as of 2025-12-11)
