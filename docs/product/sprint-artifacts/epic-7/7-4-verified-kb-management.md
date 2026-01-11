# Story 7.4: Verified KB Management

Status: ready-for-dev

## Story

As a **User**,
I want **to edit or remove Verified KB entries**,
so that **I can maintain accuracy over time**.

## Acceptance Criteria

1. **Given** I am on the Verified KB page  
   **Then** I see a searchable list of entries with:
   - Question preview
   - Answer preview
   - Created by / date
   - Actions (Edit, Delete)

2. **When** I click "Edit"  
   **Then** I can modify question or answer  
   **And** embedding is regenerated on save

3. **When** I click "Delete"  
   **Then** I see confirmation  
   **And** on confirm, entry is removed

4. **I can search entries by keyword**

5. **I can filter by date range or creator**

## Tasks / Subtasks

- [ ] **Task 1: UI - List & Controls** (AC: #1, #4, #5)
  - [ ] Build paginated list/grid with question/answer previews and metadata
  - [ ] Add search bar (client-side debounced; server-side filter)
  - [ ] Add filters: date range, creator/user
  - [ ] Provide action buttons for Edit/Delete per row

- [ ] **Task 2: Edit Flow** (AC: #2)
  - [ ] Create edit modal/drawer with question/answer fields and validation
  - [ ] On save, regenerate embedding for updated question via embedding service
  - [ ] Update entry with audit metadata (updated_at, updated_by)
  - [ ] Handle optimistic UI update with rollback on failure

- [ ] **Task 3: Delete Flow** (AC: #3)
  - [ ] Add confirmation dialog with consequences (removes from verified search)
  - [ ] Implement soft-delete with `deleted_at` (preferred) or hard delete per policy
  - [ ] Ensure soft-deleted entries are excluded from retrieval

- [ ] **Task 4: API & Query Layer** (AC: #1, #4, #5)
  - [ ] List endpoint with pagination, search (ILIKE on question/answer), filters (date range, creator)
  - [ ] Edit endpoint with re-embedding and validation
  - [ ] Delete endpoint with scope enforcement and audit logging
  - [ ] Enforce tenant_id/group_id/bot_id scoping in all queries

- [ ] **Task 5: Observability & Audit** (AC: #2, #3)
  - [ ] Log edits/deletes with user, timestamps, and reason codes
  - [ ] Expose metrics: edit count, delete count, search latency
  - [ ] Add change history table or revision log for traceability

- [ ] **Task 6: Testing** (AC: all)
  - [ ] Unit tests: list filters/search, edit validation, delete behavior
  - [ ] Integration tests: edit regenerates embedding; delete hides entry from lookup
  - [ ] UI tests: search/filter interactions, edit/save flow, delete confirmation

## Dev Notes

### Architecture Context

This story delivers lifecycle management for verified entries, ensuring the Verified KB stays accurate and auditable.

### Key Design Points

- **Edit regen:** Any question change must regenerate embedding to keep similarity results consistent.
- **Soft delete preferred:** Preserve auditability; exclude `deleted_at` rows from retrieval and UI lists.
- **Searchability:** Support keyword search on question/answer with pagination to avoid heavy client loads.
- **Scope & security:** Enforce tenant/group/bot scoping; respect RLS; validate user permissions for edit/delete.
- **Auditability:** Record who edited/deleted and when; consider reason codes for deletes.

### References

- [Source: docs/epics.md#Story-7.4]
- [Source: docs/prd.md#FR54]
- [Source: docs/architecture.md#Data-Governance]
- [Source: docs/sprint-artifacts/7-1-verified-kb-storage.md]

## Dev Agent Record

### Context Reference

<!-- Path(s) to story context XML will be added here by context workflow -->

### Agent Model Used

<!-- Will be filled by dev agent -->

### Debug Log References

<!-- Will be added during implementation -->

### Completion Notes List

<!-- Dev agent will add notes here upon completion:
- New patterns/services created
- Architectural deviations (if any)
- Technical debt items
- Warnings for next story
- Files created/modified
-->

### File List

<!-- Dev agent will list files here:
- NEW: (files created)
- MODIFIED: (files changed)
- DELETED: (files removed)
-->
