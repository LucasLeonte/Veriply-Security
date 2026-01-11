# Story 7.1: Verified KB Storage

Status: ready-for-dev

## Story

As a **System**,
I want **to maintain a separate index of verified Q&A pairs**,
so that **approved answers are prioritized in future queries**.

## Acceptance Criteria

1. **Given** a Q&A pair is approved via HITL
   **Then** it is stored in the Verified KB with:
   - Question (embedded for semantic match)
   - Answer (full text)
   - Source citations
   - Approved by (user)
   - Approved at (timestamp)
   - Bot ID (scoped)
   - Group ID (group-scoped)
   - Tenant ID (for RLS)

2. **Embeddings use same model as documents** (nomic-embed-text, 1024 dimensions)

3. **Verified KB is separate from document chunks** (dedicated table)

4. **All entries are scoped** by tenant_id, group_id, and bot_id for proper isolation

5. **Verified entries include full metadata** for traceability and audit compliance

## Tasks / Subtasks

- [ ] **Task 1: Database Schema Design** (AC: #1, #3, #4)
  - [ ] Create `verified_qa` table with columns: id, tenant_id, group_id, bot_id, question_text, question_embedding (vector 1024), answer_text, source_citations (jsonb), approved_by_user_id, approved_at, created_at, updated_at
  - [ ] Add vector index on question_embedding column for fast similarity search
  - [ ] Implement RLS policies: `tenant_id = current_tenant() AND group_id = current_group()`
  - [ ] Add composite indexes: (tenant_id, group_id, bot_id) and (tenant_id, group_id)
  - [ ] Create Alembic migration script with rollback support

- [ ] **Task 2: Backend API Models** (AC: #1, #4)
  - [ ] Define SQLAlchemy model `VerifiedQA` in `apps/api/app/models/verified_qa.py`
  - [ ] Include relationships to User (approved_by), Bot, Group, Tenant
  - [ ] Add Pydantic schemas: `VerifiedQACreate`, `VerifiedQAResponse`, `VerifiedQAUpdate`
  - [ ] Implement validation: question_text (required, max 2000 chars), answer_text (required)
  - [ ] Add created_at/updated_at timestamp handling

- [ ] **Task 3: Embedding Service Integration** (AC: #2)
  - [ ] Add method `embed_verified_question()` to existing embedding service
  - [ ] Use nomic-embed-text model (same as documents) via Ollama
  - [ ] Return 1024-dimension vector for storage
  - [ ] Handle embedding errors with proper logging and retries
  - [ ] Verify embedding dimension matches document chunks

- [ ] **Task 4: HITL Approval Integration** (AC: #1)
  - [ ] Modify HITL approval endpoint to create VerifiedQA entry on approval
  - [ ] Extract question, answer, citations from HITL item
  - [ ] Generate embedding for approved question
  - [ ] Store with proper tenant_id, group_id, bot_id scoping
  - [ ] Include approved_by_user_id from authenticated user
  - [ ] Transaction: HITL approval + VerifiedQA creation must be atomic

- [ ] **Task 5: Basic CRUD Operations** (AC: #1, #4, #5)
  - [ ] Implement `create_verified_qa(db, schema)` service function
  - [ ] Implement `get_verified_qa_by_id(db, id)` with RLS enforcement
  - [ ] Implement `list_verified_qa(db, tenant_id, group_id, bot_id)` with pagination
  - [ ] Validate all operations respect tenant/group/bot scoping
  - [ ] Add proper error handling and logging

- [ ] **Task 6: Testing** (AC: all)
  - [ ] Unit tests: VerifiedQA model CRUD operations
  - [ ] Integration test: HITL approval creates VerifiedQA entry
  - [ ] Test RLS: verify cross-tenant/cross-group isolation
  - [ ] Test embedding generation and storage
  - [ ] Test data validation and error cases
  - [ ] Add test fixtures for verified_qa entries

## Dev Notes

### Architecture Context

This story implements the foundation of the **Trust Loop** — the core differentiator of Veriply. The Verified Knowledge Base serves as a "golden dataset" of human-validated Q&A pairs that take precedence over RAG-generated answers.

**Key Architectural Patterns:**

1. **Separation of Concerns**: Verified KB is stored separately from document embeddings to enable:
   - Different query strategies (exact semantic match vs. hybrid search)
   - Independent lifecycle management (verified answers persist even if source docs deleted)
   - Clear audit trail of human approvals

2. **Multi-Tenancy with Groups**: Following the architecture's group-based knowledge model:
   - All entries scoped by (tenant_id, group_id, bot_id)
   - RLS policies enforce isolation at DB layer
   - Bots in same group share verified answers with provenance tracking

3. **Embedding Consistency**: Must use `nomic-embed-text` (1024 dims) for both:
   - Document chunks (existing)
   - Verified questions (new)
   - This ensures comparable similarity scores during retrieval

### Database Design Rationale

```sql
-- RLS policy ensures tenant + group isolation
CREATE POLICY verified_qa_isolation ON verified_qa
  USING (tenant_id = current_setting('app.current_tenant_id')::uuid 
         AND group_id = current_setting('app.current_group_id')::uuid);

-- Vector index for fast semantic search
CREATE INDEX verified_qa_embedding_idx 
  ON verified_qa USING ivfflat (question_embedding vector_cosine_ops);

-- Composite indexes for scoped queries
CREATE INDEX verified_qa_scope_idx 
  ON verified_qa (tenant_id, group_id, bot_id);
```

### Integration Points

1. **HITL Workflow** (Epic 5): 
   - When agent approves a draft → automatically create VerifiedQA entry
   - Approval must be atomic transaction (HITL status + VerifiedQA insert)

2. **Embedding Service** (Story 2.5):
   - Reuse existing `EmbeddingService` but add new method for verified questions
   - Same Ollama endpoint, same model (nomic-embed-text)

3. **Future Stories**:
   - Story 7.2: Query-time retrieval from VerifiedQA (priority check before RAG)
   - Story 7.3: Manual entry UI for seeding common questions
   - Story 7.4: Edit/delete verified entries with audit trail

### Testing Standards

Per [architecture.md#testing-strategy](../architecture.md):
- Unit tests: Model validation, CRUD operations, RLS policies
- Integration tests: End-to-end HITL approval → VerifiedQA creation
- Test data must span multiple tenants/groups to verify isolation
- Use pytest fixtures for reusable test data setup

### Project Structure Notes

**Files to Create:**
- `apps/api/app/models/verified_qa.py` — SQLAlchemy model
- `apps/api/app/schemas/verified_qa.py` — Pydantic schemas
- `apps/api/app/services/verified_qa.py` — Business logic
- `apps/api/alembic/versions/XXX_add_verified_qa.py` — Migration

**Files to Modify:**
- `apps/api/app/services/hitl.py` — Add VerifiedQA creation on approval
- `apps/api/app/services/embedding.py` — Add embed_verified_question() method
- `apps/api/app/core/database.py` — Ensure RLS context setters available

### Security & Compliance Notes

- **GDPR Compliance**: Verified entries must be deletable (Right to be Forgotten)
- **Audit Trail**: Store `approved_by_user_id` and `approved_at` for FR63 compliance
- **Data Isolation**: RLS + app-level validation prevents cross-tenant leaks
- **PII Handling**: Approved answers should already be redacted (from HITL pipeline)

### Gotchas & Warnings

⚠️ **Embedding Model Consistency**: DO NOT change to a different model (e.g., bge-m3) unless you also re-embed all existing documents. Similarity scores are only meaningful when comparing vectors from the same model.

⚠️ **Transaction Boundaries**: HITL approval + VerifiedQA creation must be in same DB transaction to prevent orphaned approvals.

⚠️ **Vector Index Tuning**: IVFFLAT index performance depends on dataset size. For <10K vectors, default settings work. For larger datasets, tune `lists` parameter in Story 7.2.

### References

- [Source: docs/prd.md#FR51-FR52] — Verified KB requirements and auto-add from HITL
- [Source: docs/epics.md#Story-7.1] — Detailed acceptance criteria
- [Source: docs/architecture.md#Multi-Tenancy-Groups-Bots] — Group-scoped KB architecture
- [Source: docs/architecture.md#Ingestion-Embeddings] — Embedding pipeline details
- [Source: apps/api/app/models/document.py] — Reference for existing embedding schema
- [Source: apps/api/app/services/embedding.py] — Existing embedding service to extend

## Dev Agent Record

### Context Reference

- docs/sprint-artifacts/7-1-verified-kb-storage.context.xml

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
