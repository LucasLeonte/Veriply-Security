# Story 7.2: Verified KB Priority

Status: ready-for-dev

## Story

As a **System**,
I want **to check the Verified KB BEFORE generating new answers**,
so that **users get consistent, human-verified responses**.

## Acceptance Criteria

1. **Given** a user query  
   **When** the RAG pipeline runs  
   **Then** the Verified KB is searched FIRST

2. **Given** a semantic match with confidence > 95%  
   **Then** the verified answer is returned immediately  
   **And** the "Verified" badge is displayed  
   **And** no LLM generation occurs

3. **Given** no match in Verified KB  
   **Then** the standard RAG pipeline continues  
   **And** answer may be generated from documents

4. **Verified KB search adds <50ms latency** end-to-end for retrieval path

## Tasks / Subtasks

- [ ] **Task 1: Two-Stage Retrieval Pipeline** (AC: #1, #2, #3)
  - [ ] Add pre-RAG lookup against `verified_qa` index scoped by tenant/group/bot
  - [ ] Return verified answer payload when similarity >= threshold
  - [ ] Bypass LLM generation and document retrieval on verified hit
  - [ ] Fall back to existing RAG path when no verified match

- [ ] **Task 2: Similarity & Thresholding** (AC: #2, #3)
  - [ ] Use cosine similarity on `question_embedding` with default threshold 0.95
  - [ ] Make threshold configurable per environment with sane defaults
  - [ ] Add safety check to avoid empty/zero vectors
  - [ ] Log scored candidates for observability (no PII)

- [ ] **Task 3: Response & UI Signal** (AC: #2)
  - [ ] Include `verified=true` flag and provenance in API response
  - [ ] Display "Verified" badge in chat/message UI when flag is set
  - [ ] Add response metadata: matched question id, confidence score, source citations

- [ ] **Task 4: Performance & Caching** (AC: #4)
  - [ ] Measure retrieval latency and ensure <50ms budget for verified lookup
  - [ ] Add optional in-memory cache for hot verified questions (scope-aware)
  - [ ] Add tracing spans/metrics for verified path vs standard RAG path

- [ ] **Task 5: Testing** (AC: all)
  - [ ] Unit tests for similarity thresholding and branching logic
  - [ ] Integration test: verified match skips LLM generation
  - [ ] Integration test: fallback to RAG when no verified match
  - [ ] Performance test: verified lookup stays within latency budget
  - [ ] UI test: "Verified" badge renders only when verified flag is true

## Dev Notes

### Architecture Context

This story makes the **Verified KB** the first-class retrieval stage. It ensures human-approved answers short-circuit the RAG pipeline, reducing hallucinations and improving consistency.

### Key Design Points

- **Separation of stages:** Lookup order is `verified_qa` → document chunks → generation.
- **Strict threshold:** Default 0.95 confidence to avoid false positives; adjustable but must be justified if lowered.
- **Scope isolation:** Always filter by tenant_id, group_id, bot_id to prevent cross-tenant leakage.
- **Provenance:** Return matched verified entry id, approval metadata, and citations for auditability.
- **Latency guardrail:** Verified lookup must stay lightweight (proper indexing + vector store tuning).

### References

- [Source: docs/epics.md#Story-7.2]
- [Source: docs/prd.md#FR55]
- [Source: docs/architecture.md#RAG-Retrieval-Flow]
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
