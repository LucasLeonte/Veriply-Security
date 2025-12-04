# Story 2.7: Document Reprocessing

**Epic:** 2. Bot & Knowledge Management  
**Status:** drafted  
**Assigned to:** null  
**Blocked by:** 2-6-document-deletion

## Story

As a User,  
I want to reprocess a document to update its embeddings,  
so that I can refresh the AI's understanding after editing the source.

## Acceptance Criteria

### Document Reprocessing Trigger

-   [ ] User can access "Reprocess" button on:
    -   Documents with status "Ready"
    -   Documents with status "Failed"
-   [ ] Reprocess button is disabled for documents currently "Processing" or "Deleting"
-   [ ] Tooltip on disabled button: "Cannot reprocess while processing or deleting"
-   [ ] User can click "Reprocess" to initiate
-   [ ] Confirmation modal appears:
    -   Message: "Reprocess document '[Name]'? This will replace all chunks and embeddings with fresh data."
    -   Two buttons: "Cancel" and "Reprocess"

### Reprocessing Workflow

-   [ ] On confirmation:
    -   Document status changes to "Processing"
    -   Old chunks for this document are deleted
    -   Old embeddings for old chunks are deleted from vector store
    -   File is re-extracted from object storage
    -   File is re-chunked using same logic as initial processing
    -   New embeddings are generated using same model (bge-m3)
    -   New chunks stored with metadata
-   [ ] Processing completes:
    -   Document status changes to "Ready"
    -   Chunk count may differ from previous processing
    -   Last updated date reflects reprocess time
    -   Success toast: "Document reprocessed successfully"

### Multi-Document Reprocessing

-   [ ] User can select multiple documents and click "Reprocess Selected"
-   [ ] Confirmation modal shows:
    -   "Reprocess X document(s)? This will replace all chunks and embeddings with fresh data."
    -   Two buttons: "Cancel" and "Reprocess X Documents"
-   [ ] All selected documents are queued for reprocessing
-   [ ] Maximum 100 documents at once (validation and warning)
-   [ ] Documents are reprocessed sequentially or in parallel (configurable)
-   [ ] Progress indicator shows: "X of Y documents reprocessed"
-   [ ] Individual document statuses update in real-time

### Reprocessing Queue

-   [ ] If reprocessing queue is busy, show message:
    -   "Queued for reprocessing. Position: 3 in queue"
-   [ ] Display estimated wait time if available
-   [ ] User can cancel queued reprocess before it starts

### Error Handling

-   [ ] If reprocessing fails:
    -   Document status changes to "Failed"
    -   Error message displayed: "Reprocessing failed. Reason: [specific error]"
    -   Original chunks and embeddings are restored (rollback)
    -   User can retry or manually delete and re-upload
-   [ ] If document file no longer exists in storage:
    -   Error: "Source file not found. Cannot reprocess."
    -   Suggest deleting document and re-uploading

### Reprocessing Use Cases

-   [ ] Reprocess after updating embedding model to vector database
-   [ ] Reprocess if chunking strategy has been optimized
-   [ ] Reprocess if user manually corrected extraction issues (by updating file in storage)
-   [ ] Reprocess to update bot's knowledge when content updated

## Tasks / Subtasks

### 1) Frontend - Reprocess Button UI

-   [ ] Add "Reprocess" button to each document row/card
-   [ ] Button disabled for Processing/Deleting status
-   [ ] Show tooltip on hover for disabled state
-   [ ] Enable for Ready/Failed status
-   [ ] Click opens confirmation modal

### 2) Frontend - Reprocess Confirmation Modal

-   [ ] Display document name in modal
-   [ ] Show warning message about chunk/embedding replacement
-   [ ] Two buttons: "Cancel" and "Reprocess"
-   [ ] Cancel closes modal without action
-   [ ] Reprocess calls API

### 3) Frontend - Bulk Reprocess UI (Optional)

-   [ ] Extend bulk selection checkboxes to support "Reprocess Selected"
-   [ ] Show "Reprocess X Documents" button when documents selected
-   [ ] Validate max 100 documents
-   [ ] Show confirmation modal for bulk reprocess
-   [ ] Call bulk reprocess API

### 4) Frontend - Reprocessing Status & Progress

-   [ ] Document status displays "Processing" while reprocessing
-   [ ] Show spinner icon
-   [ ] If queue is long, display queue position: "Queued... Position: 3"
-   [ ] Update real-time as status changes (via polling or WebSocket)
-   [ ] Show success/error toast on completion

### 5) Backend - POST `/api/v1/documents/:doc_id/reprocess` Endpoint

-   [ ] Accept document ID in URL
-   [ ] Validate document exists and belongs to user's bot
-   [ ] Validate document status is Ready or Failed
-   [ ] Validate document file still exists in storage
-   [ ] Queue async reprocess job
-   [ ] Return: success message or job ID
-   [ ] Audit: log reprocess request

### 6) Backend - POST `/api/v1/documents/bulk-reprocess` Endpoint (Optional)

-   [ ] Accept array of document IDs
-   [ ] Validate max 100 documents
-   [ ] Validate all documents belong to user's bot
-   [ ] Queue async reprocess jobs for all
-   [ ] Return: success message with job IDs

### 7) Backend - Async Reprocess Job

-   [ ] Accept document ID
-   [ ] Update document status to "Processing"
-   [ ] Get old chunks and delete from database
-   [ ] Delete corresponding embeddings from pgvector
-   [ ] Retrieve file from object storage
-   [ ] Re-extract text (same extraction logic as Story 2.4)
-   [ ] Re-chunk (same chunking logic)
-   [ ] Generate new embeddings (same model)
-   [ ] Store new chunks in database
-   [ ] Update document status to "Ready"
-   [ ] If any step fails:
        -   Update status to "Failed"
        -   Log error details
        -   Consider rollback strategy
-   [ ] Audit: log reprocess completion

### 8) Backend - Rollback Strategy (Optional)

-   [ ] If reprocessing fails midway:
    -   Keep old chunks/embeddings until new ones complete
    -   If new processing fails, old chunks remain active
    -   Mark document as "Failed" with recovery option
-   [ ] Alternative: soft delete old chunks instead of hard delete before reprocessing
    -   If new processing fails, restore old chunks
    -   If successful, hard delete old chunks after retention period

## Dev Notes

- Reprocessing is useful when embedding model is updated or chunking strategy improves
- Consider batching reprocess jobs to manage system load
- Extraction, chunking, and embedding logic should be DRY (same code as Story 2.4)
- Rollback strategy depends on storage and transaction support
- May want to show comparison of old vs new chunk count to user
- Consider adding reprocess history/audit trail

### Project Structure Notes

- Frontend components: `apps/web/src/components/knowledge-base/`
- API endpoints: `apps/api/app/routes/documents.py`
- Reprocess job: `apps/api/ingest_worker.py` (new task handler)
- Document models: `apps/api/app/models/document.py`, `apps/api/app/models/chunk.py`
- Extraction/chunking logic: `apps/api/app/services/document_processor.py`
- Tests: `apps/web/__tests__/`, `apps/api/tests/`

### References

- [Epic 2 Specification: Story 2.7](../epics.md#story-27-document-reprocessing)
- [Story 2.4: Document Processing Pipeline](./story-2-4-document-processing-pipeline.md)
- [Story 2.6: Document Deletion](./story-2-6-document-deletion.md)
- [Architecture: Document Processing & Embeddings](../architecture.md)

## Dev Agent Record

### Context Reference

<!-- Path(s) to story context XML will be added here by context workflow -->

### Agent Model Used

Claude Haiku 4.5

### Debug Log References

### Completion Notes List

### File List
