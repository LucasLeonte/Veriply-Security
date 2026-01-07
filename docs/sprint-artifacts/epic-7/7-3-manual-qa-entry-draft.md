# Story 7.3: Manual Q&A Entry

**Story ID:** 7.3  
**Epic:** 7 - Verified Knowledge Base  
**Status:** drafted  
**Assigned to:** Soulaymane  
**Created:** 2026-01-07  

---

## Story Statement

As a **Power User / Knowledge Manager**,  
I want **to manually add verified Q&A pairs to the Knowledge Base**,  
So that **I can seed the Verified KB with high-confidence QA pairs without waiting for HITL approvals**, enabling faster response quality improvement.

## Acceptance Criteria

### AC1: Single Entry Form

**Given** I am on the Verified KB page  
**When** I click "Add Entry" or "New Q&A"  
**Then** I see a form modal/panel with the following fields:
- Question (text area, required, max 2000 chars, shows remaining count)
- Answer (rich text editor, required, max 8000 chars, shows remaining count)
- Tags (optional multi-select chips from existing tags or create new)
- Citations (optional, expandable section showing document references)

**And** form shows inline validation messages (errors in red, character counts in gray)

### AC2: Create and Save Entry

**When** I fill in question and answer and click "Save"  
**Then** the system:
1. Validates payload (question/answer required, enforces max lengths)
2. Generates question embedding using nomic-embed-text (768-dim vector)
3. Creates entry with: bot_id, group_id, tenant_id, question_text, question_embedding, answer_text, approved_by_user_id (current user), approved_at (now), source_citations (empty array by default), created_at, updated_at
4. Returns success toast: "Q&A pair added successfully"
5. Refreshes the Verified KB list to show the new entry
6. Clears the form for next entry (or closes modal)

**And** the entry appears immediately in the list/grid sorted by creation date (newest first)

**And** entry is scoped to the current bot (not visible in other bots' KBs)

### AC3: Bulk CSV Import

**When** I click "Import from CSV"  
**Then** I can upload a CSV file with columns: `question`, `answer` (required), `tags` (optional, comma-separated values)

**And** the system:
1. Validates file (max 10MB, CSV format)
2. Validates each row (question/answer required, enforces lengths, non-empty rows)
3. Generates embeddings for all questions in a batch (parallel)
4. Inserts all rows within a database transaction (all-or-nothing)
5. Returns summary: "Imported X rows, Y skipped" with detailed error list if any rows failed
6. Shows progress indicator for large files (e.g., "Processing row 50 of 250...")
7. Refreshes list after completion

**And** rows with errors are reported with row numbers and specific error messages (e.g., "Row 3: question exceeds 2000 chars")

**And** duplicate questions within the same bot are detected and rejected with clear message

### AC4: Authorization & Data Scope

**When** I create or import entries  
**Then** the system:
1. Enforces tenant_id/group_id/bot_id scoping (RLS via database policies)
2. Prevents cross-tenant/cross-group/cross-bot access
3. Rejects duplicate questions (case-insensitive) within same bot scope with error: "This question already exists in your knowledge base"
4. Sanitizes rich-text input to prevent XSS (escape HTML special chars, strip dangerous tags)

### AC5: List Refresh & UX

**When** I add entries or import CSV  
**Then**:
1. List refreshes without full page reload
2. Pagination state is preserved (still on page N)
3. Search filters remain active
4. New entries appear at top with slight highlight animation (1-2 sec fade)
5. Toast notifications show success/error status

---

## Tasks & Subtasks

### Task 1: Frontend - Add Entry Form (AC1, AC2, AC5)

**Assignee:** Soulaymane

- [ ] Create `VerifiedQAForm` component in `apps/web/src/components/knowledge-base/VerifiedQAForm.tsx`
  - [ ] Question textarea field with character counter (max 2000)
  - [ ] Answer rich text editor (using existing editor component) with character counter (max 8000)
  - [ ] Tags multi-select chip input
  - [ ] Citations optional section (collapsible)
  - [ ] Submit/Cancel buttons with disabled state during submission

- [ ] Add client-side validation
  - [ ] Question: required, max 2000 chars
  - [ ] Answer: required, max 8000 chars
  - [ ] Display inline error messages (color: red)
  - [ ] Show character counts dynamically

- [ ] Create `VerifiedKBPage` or extend existing KB page
  - [ ] "Add Entry" button that opens form modal/drawer
  - [ ] List/grid display of existing verified QA pairs
  - [ ] Edit and delete actions (delete with confirmation)
  - [ ] Search/filter by question text

- [ ] Implement form submission handler
  - [ ] Call POST `/api/v1/verified-qa` endpoint
  - [ ] Show loading spinner during submission
  - [ ] Handle errors: display error toast with message
  - [ ] On success: show success toast, refresh list, clear form

- [ ] Add list refresh logic
  - [ ] Fetch list after create/import
  - [ ] Preserve pagination state and search filters
  - [ ] Highlight new entry briefly (fade animation)

**Testing:**
- [ ] Unit tests: form validation (required fields, max lengths)
- [ ] Integration tests: form submission success/error
- [ ] UI tests: character counters, error messages, button states

---

### Task 2: Frontend - CSV Import Dialog (AC3, AC5)

**Assignee:** Soulaymane

- [ ] Create `CSVImportDialog` component in `apps/web/src/components/knowledge-base/CSVImportDialog.tsx`
  - [ ] File upload input (accept .csv only)
  - [ ] File validation (max 10MB, CSV format with .csv extension)
  - [ ] Preview table showing first N rows of CSV (e.g., first 5 rows)
  - [ ] "Import" button that starts batch operation

- [ ] Implement CSV parsing and upload
  - [ ] Parse CSV headers and validate (must have "question" and "answer")
  - [ ] Extract rows and prepare payload
  - [ ] Call POST `/api/v1/verified-qa/bulk-import` endpoint
  - [ ] Show progress bar (current row / total rows)

- [ ] Handle import results
  - [ ] Display summary: "Imported X rows, Y skipped"
  - [ ] If errors, show error details table (row number, error message)
  - [ ] On success, refresh list and close dialog

**Testing:**
- [ ] Unit tests: CSV header validation, row parsing
- [ ] Integration tests: successful import, error reporting
- [ ] UI tests: file upload, progress display, error list

---

### Task 3: Backend API - Create Single Entry (AC2, AC4)

**Assignee:** Soulaymane

- [ ] Add POST endpoint `/api/v1/verified-qa` in `apps/api/app/api/routes/verified_qa.py`
  - [ ] Request schema: `VerifiedQACreateRequest` (question, answer, tags, citations)
  - [ ] Extract tenant_id, group_id, bot_id from request/auth context
  - [ ] Validate payload: question/answer required, enforce max lengths
  - [ ] Check for duplicate questions (case-insensitive) within bot scope
  - [ ] Generate question embedding via `embedding_service.embed_text(question)`
  - [ ] Call `create_verified_qa()` service function to save entry
  - [ ] Return created entry with all fields including id and timestamps
  - [ ] Response schema: `VerifiedQAResponse`

- [ ] Endpoint security
  - [ ] Require authentication (Bearer token)
  - [ ] Enforce tenant_id/group_id/bot_id scoping
  - [ ] Add RLS check in database query
  - [ ] Sanitize rich-text answer (escape HTML, strip dangerous tags)

- [ ] Error handling
  - [ ] 400 Bad Request for validation errors (missing fields, max length exceeded)
  - [ ] 409 Conflict for duplicate questions
  - [ ] 401 Unauthorized if not authenticated
  - [ ] 403 Forbidden if bot not in user's scope
  - [ ] 500 Internal Server Error for embedding/DB failures with detailed logging

**Testing:**
- [ ] Unit tests: payload validation, duplicate detection, sanitization
- [ ] Integration tests: create entry, verify embedding generated, list includes new entry
- [ ] Security tests: RLS enforcement, XSS prevention, scope checks

---

### Task 4: Backend API - Bulk CSV Import (AC3, AC4)

**Assignee:** Soulaymane

- [ ] Add POST endpoint `/api/v1/verified-qa/bulk-import` in `apps/api/app/api/routes/verified_qa.py`
  - [ ] Accept multipart file upload (CSV)
  - [ ] Request schema includes file and optional tags/citations metadata
  - [ ] Parse CSV: validate headers (must have "question" and "answer")
  - [ ] Validate each row: question/answer required, enforce max lengths
  - [ ] Row count limit: max 1000 rows per import (configurable)
  - [ ] Detect duplicate questions within import and within existing bot KB
  - [ ] For valid rows: generate embeddings in batch (parallel via asyncio)
  - [ ] Insert all valid rows within a single database transaction
  - [ ] If any row fails validation, return error report (row number, error message)
  - [ ] Return summary: imported count, skipped count, errors list

- [ ] Endpoint security & scope
  - [ ] Same auth/RLS requirements as single entry endpoint
  - [ ] Enforce file size limit (max 10MB)
  - [ ] Sanitize all answer text before saving

- [ ] Error handling
  - [ ] 400 Bad Request for malformed CSV or validation errors
  - [ ] Return detailed error report per row
  - [ ] 413 Payload Too Large if file exceeds size limit
  - [ ] 422 Unprocessable Entity if CSV format invalid (missing headers, etc.)

**Testing:**
- [ ] Unit tests: CSV parsing, header validation, row validation, duplicate detection
- [ ] Integration tests: successful import (10 rows), import with some errors, max row limit enforcement
- [ ] Performance tests: batch embedding generation (100+ rows)
- [ ] Edge case tests: empty file, missing headers, special chars in Q&A, max length boundaries

---

### Task 5: Backend Service - Embedding & Storage (AC2, AC3, AC4)

**Assignee:** Soulaymane

- [ ] Extend `verified_qa_service.py` with new functions
  - [ ] `create_verified_qa()` - already exists, verify it handles embedding storage
  - [ ] `bulk_create_verified_qa()` - new function for batch import
    * Args: list of (question, answer, tags) tuples, tenant_id, group_id, bot_id, approved_by_user_id
    * Returns: dict with `created` (count), `errors` (list of row errors), `entries` (list of created VerifiedQA objects)
    * Logic: generate embeddings in batch, insert within transaction, handle errors per row
  - [ ] `check_duplicate_question()` - new function to detect duplicates (case-insensitive) within bot scope
  - [ ] `list_verified_qa()` - already exists, ensure pagination/sorting works

- [ ] Embedding integration
  - [ ] Reuse existing `embedding_service.embed_text()` for consistency with document embeddings
  - [ ] Batch embed: `embedding_service.embed_texts(questions: List[str])` for bulk operations
  - [ ] Store 768-dim vectors in `question_embedding` column (Vector(768) type)
  - [ ] On batch import, parallelize embedding generation (asyncio.gather)

- [ ] Data sanitization
  - [ ] HTML escape all answer text before storing
  - [ ] Trim whitespace from question/answer
  - [ ] Validate UTF-8 encoding

**Testing:**
- [ ] Unit tests: service functions with mock DB and embedding service
- [ ] Integration tests: create single, bulk create, duplicate detection, list operations
- [ ] Data quality tests: embedding dimensions, encoding validation

---

### Task 6: Database & Migrations (AC2, AC3, AC4)

**Assignee:** Soulaymane

- [ ] Verify `verified_qa` table schema (should be created in Story 7.1)
  - [ ] Columns: id, tenant_id, group_id, bot_id, question_text, question_embedding (Vector 768), answer_text, source_citations (JSONB), approved_by_user_id, approved_at, created_at, updated_at
  - [ ] Primary key: id (UUID)
  - [ ] Foreign keys: tenant_id → tenants, group_id → groups, bot_id → bots, approved_by_user_id → users
  - [ ] Indexes: (tenant_id, group_id, bot_id), (bot_id), (approved_at) for sorting
  - [ ] Vector index: IVFFLAT on question_embedding for semantic search

- [ ] If table doesn't exist, create migration
  - [ ] Use Alembic for schema migration
  - [ ] Apply RLS policies (see Story 7.1 for policy SQL)

- [ ] Seed test data (optional for development)
  - [ ] Add 5-10 sample verified QA pairs for testing

**Testing:**
- [ ] Verify table schema matches model definition
- [ ] Verify indexes exist and perform well
- [ ] Verify RLS policies block cross-tenant/group/bot access

---

### Task 7: Integration & End-to-End Testing (All AC)

**Assignee:** Soulaymane

- [ ] Unit tests
  - [ ] Payload validation (required fields, max lengths, special chars)
  - [ ] CSV parsing (headers, row parsing, error reporting)
  - [ ] Duplicate detection (case-insensitive)
  - [ ] Sanitization (HTML escaping, whitespace trimming)
  - [ ] Location: `apps/api/tests/services/test_verified_qa_service.py` and `apps/web/src/components/knowledge-base/__tests__/VerifiedQAForm.test.tsx`

- [ ] Integration tests
  - [ ] Create single entry (verify DB entry, embedding generated, list updated)
  - [ ] Import CSV with 10 rows (verify all inserted, list refreshed, pagination works)
  - [ ] Import with duplicate questions (verify rejection with proper error)
  - [ ] Cross-bot isolation (create in bot A, verify not visible in bot B)
  - [ ] RLS enforcement (non-admin user cannot access other tenant's entries)
  - [ ] Location: `apps/api/tests/integration/test_verified_qa_endpoints.py`

- [ ] UI/E2E tests
  - [ ] Form validation (show errors, character counts)
  - [ ] Form submission (show loading, success toast, refresh list)
  - [ ] CSV import (upload file, show progress, display results)
  - [ ] List refresh without page reload
  - [ ] Location: `apps/web/src/components/knowledge-base/__tests__/VerifiedQAPage.e2e.test.tsx` (Playwright)

**Test Coverage Target:** >= 85% code coverage for service layer, >= 70% for API routes

---

## Implementation Notes

### Architecture & Patterns

1. **Embedding Consistency**: Use the same `nomic-embed-text` 768-dim embeddings as document ingestion to ensure semantic search consistency across KB sources.

2. **Service Reuse**: Leverage existing `embedding_service` and `verified_qa_service` (created in Story 7.1) to avoid duplication.

3. **Transaction Safety**: Bulk import uses database transactions (BEGIN/COMMIT) to ensure all-or-nothing semantics. If any row fails, entire import rolls back.

4. **RLS Enforcement**: All queries filter by tenant_id, group_id, bot_id at the application layer AND via database RLS policies for defense-in-depth.

5. **Sanitization**: Rich-text answers sanitized using `html.escape()` to prevent XSS attacks; optionally use `bleach` library for stricter HTML sanitization.

6. **Duplicate Prevention**: Case-insensitive duplicate check via SQL query: `SELECT 1 FROM verified_qa WHERE LOWER(question_text) = LOWER(?)`.

### Dependencies & Prerequisites

- ✅ Story 7.1 (Verified KB Storage) - Model, schema, base service functions
- ✅ Embedding service (existing) - nomic-embed-text integration
- ✅ Rich-text editor component (existing, used in chat)
- ✅ Authentication & authorization (existing, from Foundation epic)

### File Modifications & New Files

**Backend:**
- NEW: `apps/api/app/api/routes/verified_qa.py` (endpoints for create/bulk-import)
- NEW: `apps/api/app/schemas/verified_qa.py` (request/response schemas) - **partially exists, extend if needed**
- MODIFY: `apps/api/app/services/verified_qa.py` - add `bulk_create_verified_qa()` and `check_duplicate_question()`
- NEW: `apps/api/tests/integration/test_verified_qa_endpoints.py` (integration tests)
- NEW: `apps/api/tests/services/test_verified_qa_service.py` (service unit tests)

**Frontend:**
- NEW: `apps/web/src/components/knowledge-base/VerifiedQAForm.tsx` (single entry form)
- NEW: `apps/web/src/components/knowledge-base/CSVImportDialog.tsx` (bulk import dialog)
- NEW: `apps/web/src/components/knowledge-base/VerifiedKBPage.tsx` (main page container)
- NEW: `apps/web/src/hooks/useVerifiedQA.ts` (data fetching hook)
- NEW: `apps/web/src/components/knowledge-base/__tests__/VerifiedQAForm.test.tsx` (form tests)
- NEW: `apps/web/src/components/knowledge-base/__tests__/VerifiedQAPage.e2e.test.tsx` (E2E tests)

**Migrations:**
- If needed: `apps/api/alembic/versions/0XX_verified_qa_table.py` (create table, already in 7.1)

### Open Questions & Decisions

1. **Rich-Text Editor**: Should answer field support full HTML or markdown-only? Recommend markdown for safety.
2. **Bulk Import UI**: Stream progress or batch upload with result summary? Recommend batch with summary for simplicity.
3. **CSV Headers**: Case-sensitive or case-insensitive? Recommend case-insensitive for UX.
4. **Max File Size**: Recommend 10MB; adjust if needed based on infrastructure.
5. **Batch Size**: For 1000+ row imports, consider chunking embeddings in batches of 100 to avoid memory issues.

### Known Limitations & Future Work

1. **Edit Existing Entries**: Not in scope (marked as future story 7.4).
2. **Soft Delete**: Entries cannot be deleted (compliance requirement); future story will add soft delete.
3. **Approval Workflow**: Manual entries are auto-approved (no additional workflow); HITL approvals still use separate flow.
4. **Notifications**: No user notifications when entries are modified by others (future enhancement).

---

## Learnings from Previous Story (Story 7.1)

**From Story 7.1: Verified KB Storage (Status: done)**

- **Database Schema**: `verified_qa` table is ready with all required columns and indexes
- **Service Functions**: `create_verified_qa()` and `list_verified_qa()` already implemented and tested
- **Embedding Service**: Reuse `embedding_service.embed_text()` for consistency
- **RLS Setup**: Database policies configured; apply scoping filters in all queries
- **Lessons Learned**: 
  - Question embedding is 768-dim (not 1024-d as initially thought), use nomic-embed-text
  - Metadata_json must be JSON string, not dict
  - Batch operations need transaction handling for all-or-nothing semantics

**Patterns to Reuse:**
- Scope checks: `(tenant_id, group_id, bot_id)` triad in all queries
- Embedding integration: Use `embedding_service` wrapper methods
- Service layer architecture: Keep business logic in `verified_qa_service.py`, routes thin

**Avoid Recreating:**
- Don't redefine `VerifiedQA` model (already exists, verified in 7.1)
- Don't create new embedding service (reuse existing)
- Don't duplicate RLS policy logic (use existing database policies)

---

## Dev Agent Record

### Context Reference

<!-- Story context XML will be generated and linked here by story-context workflow -->

### Agent Model Used

<!-- Will be filled during implementation -->

### Completion Status

**Overall Progress:** 0% (not yet started)

**Subtasks Breakdown:**
- Frontend: 0% (Form + Import UI)
- Backend: 0% (API endpoints + Service layer)
- Integration Tests: 0%
- Deployment: Pending

### Debug Log References

<!-- Will be added during implementation -->

### File Changes

**NEW:**
- `apps/api/app/api/routes/verified_qa.py`
- `apps/web/src/components/knowledge-base/VerifiedQAForm.tsx`
- `apps/web/src/components/knowledge-base/CSVImportDialog.tsx`
- `apps/web/src/components/knowledge-base/VerifiedKBPage.tsx`
- `apps/web/src/hooks/useVerifiedQA.ts`
- Test files (multiple)

**MODIFIED:**
- `apps/api/app/services/verified_qa.py` (add bulk functions)
- `apps/api/app/schemas/verified_qa.py` (if needed)

**DELETED:**
- None

---

## Definition of Done

- [x] Story drafted with clear acceptance criteria
- [ ] All tasks estimated and assigned
- [ ] Frontend components built and unit tested
- [ ] Backend API endpoints implemented and integration tested
- [ ] CSV import fully functional with error handling
- [ ] RLS and data scoping enforced
- [ ] XSS prevention validated
- [ ] All test suites passing (>85% code coverage target)
- [ ] Code reviewed by senior dev
- [ ] Story merged to development branch
- [ ] Deployed to staging for QA

---

## Story Resources

- [Story File Template](../.bmad/bmm/workflows/4-implementation/create-story/template.md)
- [Acceptance Criteria Checklist](../.bmad/bmm/workflows/4-implementation/create-story/checklist.md)
- [Tech Spec: Verified KB (Epic 7)](../tech-spec-epic-7.md)
- [Architecture: Data Ingestion & Embeddings](../architecture.md#Ingestion-Embeddings)
- [PRD: Functional Requirements FR51-FR55](../prd.md#FR51-FR55)
- [Story 7.1: Verified KB Storage](./7-1-verified-kb-storage.md)

---

**Story Created:** 2026-01-07  
**Last Updated:** 2026-01-07  
**Created by:** Bob (Scrum Master)

