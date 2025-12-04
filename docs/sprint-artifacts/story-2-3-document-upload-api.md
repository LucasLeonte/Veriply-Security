---
title: "2-3 Document Upload API"
id: 2-3-document-upload-api
epic: epic-2
status: drafted
assigned_to: null
blocked_by: 2-1-bot-creation-configuration
estimate: 3d
created_by: sm
created_date: 2025-12-04
---

# Document Upload API (2-3)

Summary
    Provide a secure, authenticated API endpoint for uploading documents into a Bot's knowledge base. The endpoint accepts file uploads, performs basic validation, stores the raw file in object storage (MinIO), creates a document record in the database, and enqueues a processing job for the document pipeline.

Background / Context
    This story is part of Epic 2 (Bot & Knowledge Management). It depends on bot creation/configuration (2-1) so uploads are associated to a bot and tenant. The document processing pipeline (2-4) will consume documents produced here.

Goals
    - Accept document uploads (PDF, DOCX, TXT, CSV) through a REST API.
    - Validate file size and type, return clear errors for invalid uploads.
    - Persist files to MinIO and create a database document record with metadata.
    - Enqueue a document processing job (async) and return document id to client.

Acceptance Criteria
    - POST /api/bots/{bot_id}/documents accepts multipart file and returns 201 with JSON {"document_id": "<id>", "status": "uploaded"} on success.
    - Endpoint rejects unauthorized requests (401) and forbidden (403) when bot belongs to another tenant.
    - Files larger than configured max size (e.g., 25MB) are rejected with 413 and meaningful message.
    - Unsupported mime types are rejected with 415.
    - Upon successful upload, a Document DB row exists with status `uploaded` and storage path set.
    - A processing job is queued and the response includes `queued: true`.

In-Scope
    - API endpoint and validation
    - Storage to MinIO (or configured object store)
    - Create DB document record (minimal metadata: filename, size, mime, uploader, bot_id, tenant_id, storage_path)
    - Emit a job to existing processing queue (e.g., Redis/RQ or background task service)

Out of Scope
    - Full processing pipeline (OCR, parsing, embeddings) — handled in 2-4
    - UI for uploads — handled in Epic 2 UI stories

API Spec (proposal)
    POST /api/bots/{bot_id}/documents
    Headers: Authorization: Bearer <token>
    Body: multipart/form-data
      - file: the document file
      - name (optional): friendly name

    Responses:
      201 Created
        {
          "document_id": "uuid",
          "status": "uploaded",
          "queued": true
        }
      400 Bad Request - missing file
      401 Unauthorized
      403 Forbidden - bot/tenant mismatch
      413 Payload Too Large
      415 Unsupported Media Type

Implementation Tasks
    - Backend
      - [ ] Add route and handler: POST /api/bots/{bot_id}/documents
      - [ ] Validate auth, tenant ownership and file size/type
      - [ ] Persist file to MinIO (use configured storage client)
      - [ ] Create DB record (Document) and set status `uploaded`
      - [ ] Enqueue processing job (publish job to existing queue)
      - [ ] Add unit/integration tests for happy path and error cases

    - DevOps / Config
      - [ ] Ensure MinIO credentials and bucket exist in env/config
      - [ ] Add any required migrations for Document model (if missing)

    - Docs
      - [ ] Add API docs snippet to OpenAPI / README

Testing Notes
    - Provide an integration test using a small test file, assert DB row created and object exists in test MinIO bucket (or mocked client).

Dependencies
    - 2-1-bot-creation-configuration (bot exists with tenant)
    - MinIO (object storage)
    - Background queue service

Owner / Suggested Assignee
    - Suggested: backend dev (Lucas)

