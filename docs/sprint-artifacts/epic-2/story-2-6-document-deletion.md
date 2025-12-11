# Story 2.6: Document Deletion

**Epic:** 2. Bot & Knowledge Management  
**Status:** drafted  
**Assigned to:** null  
**Blocked by:** 2-5-knowledge-base-management-ui

## Story

As a User,  
I want to delete documents from my knowledge base,  
so that I can remove outdated or incorrect information.

## Acceptance Criteria

### Single Document Deletion

-   [x] User can click "Delete" button on any document in the list
-   [x] Confirmation modal appears with message:
    -   "Delete '[Document Name]'? This will remove all chunks and embeddings."
    -   Two buttons: "Cancel" and "Delete"
-   [x] On confirmation:
    -   Document status changes to "Deleting"
    -   Spinner/progress indicator appears
-   [x] Background job removes:
    -   File from object storage (S3)
    -   Document record from database
    -   All chunk records associated with document
    -   All embeddings from pgvector
-   [x] When deletion completes:
    -   Document disappears from the list
    -   Success toast: "Document deleted successfully"
-   [ ] If user is viewing document detail, they are returned to document list

### Bulk Document Deletion

-   [x] User can select multiple documents using checkboxes
-   [x] A checkbox in the table header selects/deselects all visible documents
-   [x] Selected count displays: "X document(s) selected"
-   [x] Bulk delete action appears when documents are selected (button or menu)
-   [x] User can click "Delete Selected" button
-   [x] Confirmation modal appears:
    -   "Delete X document(s)? This will remove all chunks and embeddings."
    -   Two buttons: "Cancel" and "Delete X Documents"
-   [x] On confirmation:
    -   All selected documents marked as "Deleting"
    -   Spinners appear on each document
    -   Background job processes deletion of all selected documents
-   [x] When complete:
    -   All deleted documents disappear from list
    -   Success toast: "X document(s) deleted successfully"
-   [x] Bulk delete supports up to 100 documents at once
-   [x] If user tries to delete more than 100 documents, show warning:
    -   "Maximum 100 documents can be deleted at once. Please select fewer documents."

### In-Progress Deletion Status

-   [x] While documents are being deleted, show:
    -   "Deleting..." status label
    -   Spinner icon
    -   Optional progress percentage for large deletions
-   [x] User can continue browsing other documents while deletion is in progress
-   [ ] User can cancel deletion if it's still processing (optional feature)

### Error Handling

-   [x] If deletion fails:
    -   Document status returns to "Ready"
    -   Error toast: "Failed to delete document. Please try again."
    -   Error details logged
-   [x] If bulk deletion partially fails:
    -   Some documents deleted, some failed
    -   Show which documents failed
    -   Offer retry option for failed documents
-   [x] If document not found:
    -   Error toast: "Document no longer exists"
    -   Remove from list

### Deletion Constraints

-   [x] Cannot delete documents that are currently being processed
    -   Show tooltip: "Cannot delete while processing. Please wait."
    -   Delete button is disabled for processing documents

## Tasks / Subtasks

### 1) Frontend - Single Document Deletion UI

-   [x] Add "Delete" button to each document row/card
-   [x] Create confirmation modal component
-   [x] Display document name in confirmation message
-   [x] Call deletion API on confirm
-   [x] Handle loading state (spinner, disabled buttons)
-   [x] Handle error state (show error message)
-   [x] Remove document from list on success

### 2) Frontend - Bulk Document Deletion UI

-   [x] Add checkbox to each document row
-   [x] Add "select all" checkbox in table header
-   [x] Track selected documents in component state
-   [x] Show "X document(s) selected" count
-   [x] Show bulk delete action (button or menu) when documents selected
-   [x] Create confirmation modal for bulk deletion
-   [x] Validate max 100 documents (show warning if exceeded)
-   [x] Call bulk deletion API with list of document IDs

### 3) Frontend - Deletion Status Display

-   [x] Show "Deleting..." status in document row
-   [x] Display spinner icon while deleting
-   [x] Optionally show progress percentage
-   [x] Ensure UI is responsive during deletion
-   [x] Show success/error toast after completion

### 4) Backend - DELETE `/api/v1/documents/:doc_id` Endpoint

-   [x] Accept document ID in URL
-   [x] Validate document exists and belongs to user's bot
-   [x] Enforce tenant isolation
-   [x] Queue async deletion job OR delete synchronously (if fast)
-   [x] Return: 204 No Content or success message
-   [x] Audit: log deletion (user, document ID, timestamp)

### 5) Backend - DELETE `/api/v1/documents/bulk` Endpoint (Optional)

-   [x] Accept array of document IDs in request body
-   [x] Validate max 100 documents
-   [x] Validate all documents belong to user's bot (security)
-   [x] Queue async deletion jobs for all documents
-   [x] Return: success message with count
-   [x] Audit: log bulk deletion

### 6) Backend - Async Deletion Job

-   [x] Accept document ID
-   [x] Delete from object storage (S3):
    -   Check if file exists before attempting delete
    -   Handle 404 gracefully (file may not exist)
-   [x] Delete from database:
    -   Delete chunk records for this document
    -   Delete embedding records from pgvector
    -   Delete document record
-   [x] Use transaction for consistency
-   [x] Log deletion for audit trail
-   [ ] Notify frontend of completion (optional: via event/notification)

### 7) Backend - Soft Delete Pattern (Optional)

-   [ ] Implement soft delete initially:
    -   Add `deleted_at` timestamp column
    -   Mark documents as deleted instead of hard delete
    -   Exclude soft-deleted docs from queries
    -   Background job performs hard delete after retention period (e.g., 30 days)
-   [ ] Allows rollback if deletion was accidental

### 8) Database - Cascade & Cleanup

-   [x] Ensure document deletion cascades to:
    -   All chunks for that document
    -   All embeddings for those chunks
    -   Any associated metadata
-   [x] Verify no orphaned records remain
-   [x] Add database-level constraints if applicable

## Dev Notes

- Deletion is a destructive operation; consider adding a "restore" option during retention period
- Soft delete pattern is recommended for compliance/audit purposes
- Use background jobs for large deletions to avoid timeout on API endpoint
- Batch delete operations in chunks (e.g., 10 at a time) if dealing with 100s of embeddings
- Vector store deletion may require special handling (not all DBs cascade delete)
- Consider rate limiting on deletion to prevent abuse

### Project Structure Notes

- Frontend components: `apps/web/src/components/knowledge-base/`
- API endpoints: `apps/api/app/routes/documents.py`
- Database models: `apps/api/app/models/document.py`, `apps/api/app/models/chunk.py`
- Background jobs: `apps/api/ingest_worker.py`
- Object storage: S3 client in `apps/api/app/storage/`
- Tests: `apps/web/__tests__/`, `apps/api/tests/test_documents.py`

### References

- [Epic 2 Specification: Story 2.6](../epics.md#story-26-document-deletion)
- [Story 2.5: Knowledge Base Management UI](./story-2-5-knowledge-base-management-ui.md)
- [Architecture: Data Deletion & Cleanup](../architecture.md)

## Dev Agent Record

### Context Reference

<!-- Path(s) to story context XML will be added here by context workflow -->

### Agent Model Used

Claude Sonnet 4.5

### Debug Log References

### Completion Notes List

**2025-12-11 - Story 2.6 Implementation Complete**

Implemented comprehensive document deletion feature with both single and bulk deletion capabilities:

**Frontend Components Created:**
1. `useDocumentDeletion` hook - Manages deletion state and API calls
2. `DeleteConfirmationModal` - Single document deletion confirmation
3. `BulkDeleteConfirmationModal` - Bulk deletion with 100-doc limit validation
4. `DocumentDeleteButton` - Reusable delete button (3 variants, 3 sizes)
5. `BulkDeleteToolbar` - Selection management and bulk actions

**Frontend Components Updated:**
1. `KnowledgeBaseList` - Added selection state, bulk delete integration
2. `DocumentCard` - Added checkbox, "Deleting..." status, disabled states

**Backend Implementation:**
1. Enhanced `DELETE /api/v1/documents/{document_id}` endpoint:
   - Processing status check (409 error)
   - Tenant isolation
   - Cascade deletion of chunks
   - Async storage cleanup
   - Comprehensive logging

2. New `POST /api/v1/documents/bulk-delete` endpoint:
   - Max 100 documents validation
   - Batch deletion with transaction
   - Processing document checks
   - Tenant isolation
   - Bulk storage cleanup

3. Created `deletion_service.py`:
   - `cleanup_storage()` - S3 and local filesystem support
   - `cleanup_s3()` - AWS S3 deletion with graceful 404 handling
   - `cleanup_local()` - Local file deletion
   - Async job queuing for background cleanup
   - Error handling and logging

4. Added schemas:
   - `BulkDeleteRequest` - Validation for bulk delete
   - `BulkDeleteResponse` - Standardized response format

**Testing:**
- Created `test_document_deletion.py` with 11 comprehensive test cases
- Single deletion: success, 404, processing check, tenant isolation
- Bulk deletion: success, limit validation, empty list, mixed scenarios, processing check, tenant isolation

**Key Features:**
✅ Single & bulk document deletion
✅ 100-document bulk limit enforcement
✅ Processing document protection
✅ Visual "Deleting..." status
✅ Select all / deselect all
✅ Cascade deletion (docs → chunks → embeddings)
✅ Async storage cleanup (S3 + local)
✅ Tenant isolation
✅ Comprehensive error handling
✅ Toast notifications (placeholder)
✅ Audit logging

**Remaining Optional Features:**
- Soft delete pattern (retention period)
- Real-time deletion status updates via WebSocket
- Cancel deletion in progress
- Replace placeholder toast utility with real library
- Redirect from document detail page after deletion

**Files Modified/Created:**
Frontend (7 files):
- hooks/useDocumentDeletion.ts
- components/modals/DeleteConfirmationModal.tsx
- components/modals/BulkDeleteConfirmationModal.tsx
- components/knowledge-base/DocumentDeleteButton.tsx
- components/knowledge-base/BulkDeleteToolbar.tsx
- components/kb/KnowledgeBaseList.tsx
- components/kb/DocumentCard.tsx

Backend (4 files):
- api/routes/documents.py
- schemas/document.py
- services/deletion_service.py
- tests/test_document_deletion.py

API Clients (2 files):
- lib/api/documents.ts
- lib/api/mockDocuments.ts

**Technical Notes:**
- CASCADE DELETE configured at database level for chunks
- Storage cleanup is fire-and-forget (doesn't block API response)
- Supports both S3 (boto3) and local filesystem storage
- Transaction-based deletion ensures consistency
- All operations enforce tenant isolation
- Processing documents (status="processing") are protected from deletion

### File List
