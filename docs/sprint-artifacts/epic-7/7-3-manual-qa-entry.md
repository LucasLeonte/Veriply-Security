# Story 7.3: Manual Q&A Entry

Status: ready-for-dev

## Story

As a **User**,
I want **to manually add Q&A pairs to the Verified KB**,
so that **I can seed common questions without waiting for HITL**.

## Acceptance Criteria

1. **Given** I am on the Verified KB page  
   **When** I click "Add Entry"  
   **Then** I see a form with: Question (required), Answer (required, rich text), Tags (optional)

2. **When** I submit  
   **Then** the entry is added to Verified KB  
   **And** question is embedded automatically  
   **And** entry appears in the list

3. **I can bulk import from CSV** with columns: question, answer

## Tasks / Subtasks

- [ ] **Task 1: UI - Add Entry Form** (AC: #1, #2)
  - [ ] Build Verified KB page section with "Add Entry" button
  - [ ] Implement form fields: question (textarea), answer (rich text), tags (chips)
  - [ ] Add client-side validation (required question/answer, max lengths)
  - [ ] Show inline errors and submit/processing states

- [ ] **Task 2: API - Create Entry** (AC: #2)
  - [ ] Add POST endpoint `/api/v1/verified-qa` secured by tenant/group/bot scope
  - [ ] Validate payload; enforce required question/answer; optional tags
  - [ ] Call embedding service to generate question vector (nomic-embed-text, 1024-d)
  - [ ] Save entry with citations placeholder (empty array by default)
  - [ ] Return created entry with id, timestamps, and scope fields

- [ ] **Task 3: CSV Import** (AC: #3)
  - [ ] Support CSV upload (question, answer columns; optional tags column ignored if present)
  - [ ] Validate row count limits and per-row required fields
  - [ ] Batch embed questions and insert within transaction
  - [ ] Return summary: imported count, skipped rows with reasons
  - [ ] Add streaming/progress UI for large files (nice-to-have)

- [ ] **Task 4: List Refresh & UX** (AC: #2)
  - [ ] Refresh list/grid after create/import without full page reload
  - [ ] Show toast/alert on success or failure
  - [ ] Ensure pagination/search state persists after refresh

- [ ] **Task 5: Authorization & Validation** (AC: all)
  - [ ] Enforce tenant_id/group_id/bot_id scoping on create/import
  - [ ] Reject duplicate questions within same bot scope (case-insensitive)
  - [ ] Sanitize rich-text input to prevent XSS

- [ ] **Task 6: Testing** (AC: all)
  - [ ] Unit tests: payload validation, CSV parser edge cases
  - [ ] Integration tests: create entry, embed generated, list shows new entry
  - [ ] Integration tests: CSV import happy path and error reporting
  - [ ] UI tests: form validation messages, success states, list refresh

## Dev Notes

### Architecture Context

This story seeds the Verified KB without waiting for HITL approvals. It shares the same embedding pipeline as documents and HITL-approved entries to keep similarity scores consistent.

### Key Design Points

- **Embedding consistency:** Use `nomic-embed-text` 1024-d vectors; reuse embedding service.
- **Input hygiene:** Sanitize rich text; enforce length limits (e.g., question <= 2000 chars, answer <= 8000 chars).
- **Scope awareness:** All create/import operations must include tenant_id, group_id, bot_id; apply RLS and application checks.
- **Deduplication:** Prevent duplicate questions per bot to reduce noisy matches; surface conflicts with clear errors.
- **CSV safety:** Validate headers, row count caps, and reject files > configured size.

### References

- [Source: docs/epics.md#Story-7.3]
- [Source: docs/prd.md#FR53]
- [Source: docs/architecture.md#Ingestion-Embeddings]
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
