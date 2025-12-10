# Story 2.5: Knowledge Base Management UI

**Epic:** 2. Bot & Knowledge Management  
**Status:** drafted → ready-for-review  
**Assigned to:** Soulaymane  
**Blocked by:** 2-4-document-processing-pipeline

## Summary

As a product user (bot owner), I need a single-page UI to view, search, filter, sort and manage my bot's uploaded documents and extracted chunks so I can keep the bot's knowledge base accurate and quickly fix extraction issues.

## Personas

- Product Owner / Content Manager: uploads documents, inspects chunk previews and reprocesses when needed.
- Support Engineer: investigates processing failures via logs and triggers reprocessing.

## Background & Motivation

The document processing pipeline produces searchable chunks used by the bot. Users need a clear UI to understand what documents are present, their processing status, and whether reprocessing or deletion is required. This reduces support load and improves bot quality.

## Acceptance Criteria (condensed & testable)

1) Knowledge Base List View
- User can open the Knowledge Base page for a bot at `/bots/:bot_id/documents`.
- Page lists documents in a table or responsive card list with columns: Name (clickable), Type, Size, Status, Chunk count, Upload date, Actions (View, Delete, Reprocess).
- Status badges use colors: Processing (yellow), Ready (green), Failed (red).
- Empty state: "No documents uploaded. Upload your first document to get started." shown when zero documents.
- Pagination: default 20 documents per page with next/prev and page numbers.

2) Search, Filter & Sort
- Live search by name (case-insensitive) with debounce (250ms).
- Filter by status (All, Processing, Ready, Failed) and combined with search.
- Sortable columns: name, type, size, status (Processing → Ready → Failed), chunk_count, upload_date. Default: upload_date desc (newest first).

3) Document Detail View
- Clicking name opens a modal/slide-out with metadata, chunk count, first N chunk previews (truncate at 200 chars), and processing logs if Failed.
- Actions: Delete (confirm), Reprocess (confirm), Close.

4) Real-time Updates
- Document statuses update live via WebSocket events or polling fallback every 2s. UI updates only for changed documents.
- Show spinner/progress for documents in Processing state.

5) Responsive
- Desktop: full table. Mobile: collapse to essential columns (Name, Status, Size, Actions) with card layout.

6) Security & Multi-tenant
- All endpoints enforce tenant isolation and bot ownership. Users only see documents they own or have access to.

## Definition of Done

- Frontend components implemented under `apps/web/src/components/knowledge-base/` with unit tests.
- Backend endpoints implemented and covered by API tests in `apps/api/tests/test_documents.py`.
- End-to-end happy-path test for upload → processing → Ready status visible in UI.
- Accessibility: table and controls keyboard-navigable and labelled.

## API Contracts (examples)

1) GET /api/v1/bots/:bot_id/documents
Request query params: `?page=1&limit=20&search=invoice&status=Ready&sort_by=upload_date&sort_order=desc`
Response 200:
```
{
    "items": [
        {"id":"uuid","name":"Q4_report.pdf","type":"pdf","size":1234567,"status":"Ready","chunk_count":42,"upload_date":"2025-12-04T10:22:00Z"}
    ],
    "page":1,"limit":20,"total":57
}
```

2) GET /api/v1/documents/:doc_id
Response 200:
```
{
    "id":"uuid",
    "name":"Q4_report.pdf",
    "type":"pdf",
    "size":1234567,
    "status":"Ready",
    "chunk_count":42,
    "upload_date":"2025-12-04T10:22:00Z",
    "chunks": [ {"id":"c1","page_num":1,"preview":"First 200 chars..."} ],
    "processing_logs": null
}
```

Errors: 401/403 if unauthorized, 404 if doc not found, 400 for invalid params.

## Acceptance Tests (Gherkin)

Scenario: List documents and see processing updates
    Given bot "B1" has 3 documents, one in Processing
    When I open `/bots/B1/documents`
    Then I see 3 rows and a yellow badge for the Processing document
    And after processing completes the badge turns green and chunk count > 0

Scenario: Search & Filter
    Given documents named "invoice", "policy" exist
    When I search for "invoice"
    Then only "invoice" appears in the list

Scenario: View document details and reprocess
    Given a document in Failed state with logs
    When I open details
    Then I see processing logs and a Reprocess button
    When I click Reprocess and confirm
    Then document status becomes Processing and logs clear

## UI Components & File Paths

- `KnowledgeBaseList` — `apps/web/src/components/knowledge-base/KnowledgeBaseList.tsx`
- `DocumentRow` / `DocumentCard` — render single document
- `StatusBadge` — `apps/web/src/components/StatusBadge/StatusBadge.tsx`
- `DocumentDetail` modal — `apps/web/src/components/knowledge-base/DocumentDetail.tsx`
- Styles and tests next to components.

## Backend Implementation Notes

- Routes: `apps/api/app/routes/documents.py` add handlers for list and detail endpoints.
- Models: `apps/api/app/models/document.py`, `apps/api/app/models/chunk.py` include necessary fields.
- DB queries should support filtering, full-text search on name, and sorting.
- Pagination: use limit/offset; return total count.
- Real-time: publish status events to WebSocket topic `bot:{bot_id}:documents` when processing finishes/errors.

## Tasks / Subtasks (developer-ready)

1) Backend - Documents list API (2d)
- Implement `/api/v1/bots/:bot_id/documents` with query params, validation, tenant checks, pagination, and unit tests.

2) Backend - Document detail API (1.5d)
- Implement `/api/v1/documents/:doc_id` returning chunk previews and processing logs, with ownership checks.

3) Frontend - KnowledgeBaseList (3d)
- Build table with search, filters, sort, pagination; wire to API; add unit tests.

4) Frontend - DocumentDetail (2d)
- Modal/slide-out with chunk previews, logs, delete and reprocess actions.

5) Frontend - Real-time updates (1.5d)
- Implement WebSocket listener + polling fallback, update only changed documents.

6) QA & E2E (2d)
- Add Playwright or Cypress tests for main flows: list, search, view detail, reprocess.

Estimates are rough; pair with backend/frontend owners when scheduling.

## Test Data & Debugging

- Provide sample documents in test fixtures under `apps/api/tests/fixtures/`.
- For local testing, use `scripts/init-test-data.sh` or a small Python script to create documents with statuses Processing/Ready/Failed.

## Notes & Risks

- Real-time via WebSocket requires small server-side publisher; if not available, polling every 2s may increase load—implement exponential backoff on errors.
- Chunk previews must truncate safely to avoid leaking PII; use configured sanitizer.

## References

- `docs/architecture.md` — data model and chunking behavior
- `docs/story-2-4-document-processing-pipeline.md` — processing pipeline and statuses

## Dev Agent Record

### Context Reference
Path(s) to story context XML will be added here by context workflow.

### Agent Model Used
Generated by internal agent (story draft automation).

### Completion Notes
- Draft updated to include API contracts, Gherkin scenarios, DoD, and developer tasks.

### File List
This story file (updated). 
