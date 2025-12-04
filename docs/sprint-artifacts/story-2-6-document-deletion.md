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

-   [ ] User can click "Delete" button on any document in the list
-   [ ] Confirmation modal appears with message:
    -   "Delete '[Document Name]'? This will remove all chunks and embeddings."
    -   Two buttons: "Cancel" and "Delete"
-   [ ] On confirmation:
    -   Document status changes to "Deleting"
    -   Spinner/progress indicator appears
-   [ ] Background job removes:
    -   File from object storage (S3)
    -   Document record from database
    -   All chunk records associated with document
    -   All embeddings from pgvector
-   [ ] When deletion completes:
    -   Document disappears from the list
    -   Success toast: "Document deleted successfully"
-   [ ] If user is viewing document detail, they are returned to document list

### Bulk Document Deletion

-   [ ] User can select multiple documents using checkboxes
-   [ ] A checkbox in the table header selects/deselects all visible documents
-   [ ] Selected count displays: "X document(s) selected"
-   [ ] Bulk delete action appears when documents are selected (button or menu)
-   [ ] User can click "Delete Selected" button
-   [ ] Confirmation modal appears:
    -   "Delete X document(s)? This will remove all chunks and embeddings."
    -   Two buttons: "Cancel" and "Delete X Documents"
-   [ ] On confirmation:
    -   All selected documents marked as "Deleting"
    -   Spinners appear on each document
    -   Background job processes deletion of all selected documents
-   [ ] When complete:
    -   All deleted documents disappear from list
    -   Success toast: "X document(s) deleted successfully"
-   [ ] Bulk delete supports up to 100 documents at once
-   [ ] If user tries to delete more than 100 documents, show warning:
    -   "Maximum 100 documents can be deleted at once. Please select fewer documents."

### In-Progress Deletion Status

-   [ ] While documents are being deleted, show:
    -   "Deleting..." status label
    -   Spinner icon
    -   Optional progress percentage for large deletions
-   [ ] User can continue browsing other documents while deletion is in progress
-   [ ] User can cancel deletion if it's still processing (optional feature)

### Error Handling

-   [ ] If deletion fails:
    -   Document status returns to "Ready"
    -   Error toast: "Failed to delete document. Please try again."
    -   Error details logged
-   [ ] If bulk deletion partially fails:
    -   Some documents deleted, some failed
    -   Show which documents failed
    -   Offer retry option for failed documents
-   [ ] If document not found:
    -   Error toast: "Document no longer exists"
    -   Remove from list

### Deletion Constraints

-   [ ] Cannot delete documents that are currently being processed
    -   Show tooltip: "Cannot delete while processing. Please wait."
    -   Delete button is disabled for processing documents

## Tasks / Subtasks

### 1) Frontend - Single Document Deletion UI

-   [ ] Add "Delete" button to each document row/card
-   [ ] Create confirmation modal component
-   [ ] Display document name in confirmation message
-   [ ] Call deletion API on confirm
-   [ ] Handle loading state (spinner, disabled buttons)
-   [ ] Handle error state (show error message)
-   [ ] Remove document from list on success

### 2) Frontend - Bulk Document Deletion UI

-   [ ] Add checkbox to each document row
-   [ ] Add "select all" checkbox in table header
-   [ ] Track selected documents in component state
-   [ ] Show "X document(s) selected" count
-   [ ] Show bulk delete action (button or menu) when documents selected
-   [ ] Create confirmation modal for bulk deletion
-   [ ] Validate max 100 documents (show warning if exceeded)
-   [ ] Call bulk deletion API with list of document IDs

### 3) Frontend - Deletion Status Display

-   [ ] Show "Deleting..." status in document row
-   [ ] Display spinner icon while deleting
-   [ ] Optionally show progress percentage
-   [ ] Ensure UI is responsive during deletion
-   [ ] Show success/error toast after completion

### 4) Backend - DELETE `/api/v1/documents/:doc_id` Endpoint

-   [ ] Accept document ID in URL
-   [ ] Validate document exists and belongs to user's bot
-   [ ] Enforce tenant isolation
-   [ ] Queue async deletion job OR delete synchronously (if fast)
-   [ ] Return: 204 No Content or success message
-   [ ] Audit: log deletion (user, document ID, timestamp)

### 5) Backend - DELETE `/api/v1/documents/bulk` Endpoint (Optional)

-   [ ] Accept array of document IDs in request body
-   [ ] Validate max 100 documents
-   [ ] Validate all documents belong to user's bot (security)
-   [ ] Queue async deletion jobs for all documents
-   [ ] Return: success message with count
-   [ ] Audit: log bulk deletion

### 6) Backend - Async Deletion Job

-   [ ] Accept document ID
-   [ ] Delete from object storage (S3):
    -   Check if file exists before attempting delete
    -   Handle 404 gracefully (file may not exist)
-   [ ] Delete from database:
    -   Delete chunk records for this document
    -   Delete embedding records from pgvector
    -   Delete document record
-   [ ] Use transaction for consistency
-   [ ] Log deletion for audit trail
-   [ ] Notify frontend of completion (optional: via event/notification)

### 7) Backend - Soft Delete Pattern (Optional)

-   [ ] Implement soft delete initially:
    -   Add `deleted_at` timestamp column
    -   Mark documents as deleted instead of hard delete
    -   Exclude soft-deleted docs from queries
    -   Background job performs hard delete after retention period (e.g., 30 days)
-   [ ] Allows rollback if deletion was accidental

### 8) Database - Cascade & Cleanup

-   [ ] Ensure document deletion cascades to:
    -   All chunks for that document
    -   All embeddings for those chunks
    -   Any associated metadata
-   [ ] Verify no orphaned records remain
-   [ ] Add database-level constraints if applicable

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

Claude Haiku 4.5

### Debug Log References

### Completion Notes List

### File List
