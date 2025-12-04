# Story 2.5: Knowledge Base Management UI

**Epic:** 2. Bot & Knowledge Management  
**Status:** drafted  
**Assigned to:** null  
**Blocked by:** 2-4-document-processing-pipeline

## Story

As a User,  
I want to view and manage my bot's documents,  
so that I can maintain an accurate knowledge base.

## Acceptance Criteria

### Knowledge Base List View

-   [ ] User can navigate to a bot's Knowledge Base page
-   [ ] Page displays a table/list of all documents with columns:
    -   Document name (clickable)
    -   Type (PDF/DOCX/TXT/MD/CSV)
    -   Size (human-readable: 1.2MB, 500KB, etc.)
    -   Status (Processing/Ready/Failed)
    -   Chunk count (number of chunks created)
    -   Upload date (formatted: "Dec 4, 2025")
    -   Actions (View, Delete, Reprocess)
-   [ ] Status badges are color-coded:
    -   Yellow/warning: Processing
    -   Green/success: Ready
    -   Red/error: Failed
-   [ ] Empty state message appears when no documents: "No documents uploaded. Upload your first document to get started."
-   [ ] Pagination: 20 documents per page with page navigation

### Document Search & Filtering

-   [ ] User can search documents by name (case-insensitive, live search)
-   [ ] User can filter documents by status (All, Processing, Ready, Failed)
-   [ ] Search and filters work together
-   [ ] Clear button appears when search/filter is active

### Document Sorting

-   [ ] User can sort by any column:
    -   Name (A-Z, Z-A)
    -   Type
    -   Size (small to large, large to small)
    -   Status (Processing → Ready → Failed)
    -   Chunk count (ascending/descending)
    -   Upload date (newest first, oldest first)
-   [ ] Default sort: newest uploaded first
-   [ ] Sort indicator (arrow or icon) shows active column and direction

### Document Detail View

-   [ ] User can click on a document name to view details
-   [ ] Detail view shows:
    -   Document name
    -   Type and file size
    -   Upload date
    -   Status
    -   Chunk count and breakdown (if available)
    -   Processing logs (if failed)
    -   Preview of first N chunks (with truncation)
    -   Back button or modal close
-   [ ] User can view chunk content to verify extraction quality
-   [ ] If processing failed, error message and retry option are visible

### Real-time Status Updates

-   [ ] Document statuses update in real-time:
    -   Initially: Processing
    -   After completion: Ready (with chunk count)
    -   On error: Failed (with error message)
-   [ ] Updates via polling (every 2 seconds) or WebSocket
-   [ ] User doesn't need to refresh page to see status changes
-   [ ] Spinner/progress indicator shows while processing

### Responsive Design

-   [ ] List view works on desktop, tablet, and mobile
-   [ ] On mobile: show essential columns (name, status, size, actions)
-   [ ] Swipe or tap to access additional actions on mobile
-   [ ] Detail view is mobile-friendly

## Tasks / Subtasks

### 1) Frontend - Knowledge Base List Component

-   [ ] Create `KnowledgeBaseList` component with:
    -   Document table/list rendering
    -   Column headers with sort indicators
    -   Search input field
    -   Status filter dropdown
    -   Pagination controls
-   [ ] Implement client-side sorting for columns
-   [ ] Implement client-side search filtering
-   [ ] Implement client-side status filtering
-   [ ] Add "Upload Document" button (CTA)
-   [ ] Display empty state when no documents

### 2) Frontend - Status Badge Component

-   [ ] Create reusable `StatusBadge` component
-   [ ] Support colors: yellow (processing), green (ready), red (failed)
-   [ ] Optional tooltip showing extended status info
-   [ ] Animation for processing state

### 3) Frontend - Real-time Updates

-   [ ] Implement polling mechanism:
    -   Every 2 seconds, fetch document list status
    -   Compare with local state
    -   Update only changed documents
-   [ ] Alternative: implement WebSocket listener for document status events
-   [ ] Show loading indicator during fetch
-   [ ] Handle errors gracefully (retry logic)

### 4) Frontend - Document Detail Modal/Page

-   [ ] Create `DocumentDetail` component
-   [ ] Fetch and display full document metadata
-   [ ] Display chunk list with preview (truncate at 200 chars)
-   [ ] Show processing logs if status is Failed
-   [ ] Add action buttons: Delete, Reprocess, Close
-   [ ] Responsive modal or slide-out panel

### 5) Backend - GET `/api/v1/bots/:bot_id/documents` API

-   [ ] Fetch all documents for a bot with pagination (20 per page)
-   [ ] Return fields: id, name, type, size, status, chunk_count, upload_date
-   [ ] Support query params: page, limit, sort_by, sort_order, search, status_filter
-   [ ] Enforce tenant isolation and bot ownership
-   [ ] Validate input parameters

### 6) Backend - GET `/api/v1/documents/:doc_id` API

-   [ ] Fetch full document details
-   [ ] Return: id, name, type, size, status, chunk_count, upload_date, chunks (paginated), processing_logs (if failed)
-   [ ] Return chunk list with id, content, page_num (if PDF)
-   [ ] Enforce tenant isolation and document ownership

### 7) Frontend - Responsive Design & Mobile Optimization

-   [ ] Test on mobile devices (iPhone, Android)
-   [ ] Collapse secondary columns on mobile (type, size)
-   [ ] Show essential info: name, status, actions
-   [ ] Add horizontal scroll for table or switch to card layout
-   [ ] Touch-friendly action buttons

## Dev Notes

- Real-time updates should gracefully degrade if WebSocket isn't available (fall back to polling)
- Consider infinite scroll as alternative to pagination for better UX
- Chunk preview should handle long text with ellipsis or truncation
- Error messages from failed processing should be user-friendly (not raw stack traces)
- Consider adding a "bulk select" feature for multi-document operations (future)

### Project Structure Notes

- Frontend components: `apps/web/src/components/knowledge-base/`
- API endpoints: `apps/api/app/routes/documents.py`
- Database models: `apps/api/app/models/document.py`, `apps/api/app/models/chunk.py`
- Tests: `apps/web/__tests__/knowledge-base.test.tsx`, `apps/api/tests/test_documents.py`

### References

- [Epic 2 Specification: Story 2.5](../epics.md#story-25-knowledge-base-management-ui)
- [Story 2.4: Document Processing Pipeline](./story-2-4-document-processing-pipeline.md)
- [Architecture: Knowledge Base Data Model](../architecture.md)

## Dev Agent Record

### Context Reference

<!-- Path(s) to story context XML will be added here by context workflow -->

### Agent Model Used

Claude Haiku 4.5

### Debug Log References

### Completion Notes List

### File List
