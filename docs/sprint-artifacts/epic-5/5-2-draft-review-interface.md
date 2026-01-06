# Story 5.2: Draft Review Interface

Status: stukje gedaan

## Requirements Context Summary

-   Epic goal: enable agents to review AI draft responses with full context, confidence score, and editing capability. [Source: docs/epics.md#story-52-draft-review-interface]
-   Product intent: trust-first workflow, agents verify/edit AI drafts before sending; must show query, context, and editable draft. [Source: docs/prd.md]
-   Architecture guardrails: Next.js frontend, FastAPI backend, PostgreSQL + pgvector; rich text editor for draft, context chunk display, citation support. [Source: docs/architecture.md][Source: docs/tech-spec.md]
-   UX cues: split view (query/context left, draft right), confidence badge, expandable context, citation highlighting. [Source: docs/ux-design-specification.md]

## Structure Alignment Summary

-   Backend: API endpoint to fetch queue item details (query, context chunks, draft, confidence, bot name, time in queue); update draft on edit/approve.
-   Frontend: HITL dashboard review page with split view, context chunk list, editable draft, confidence badge, citation highlighting.
-   Data model: queue item includes query, context_chunks[], draft_text, confidence_pct, bot_name, created_at, status.

## Story

As an Agent,
I want to see the AI draft alongside the query and context,
so that I can verify accuracy before approving.

## Acceptance Criteria

1. Review interface shows split view: left panel (query + context chunks with sources), right panel (editable AI draft), top bar (confidence score, bot name, time in queue). [Source: docs/epics.md#story-52-draft-review-interface]
2. Context chunks are expandable/collapsible; source documents are clickable (open in new tab). [Source: docs/epics.md#story-52-draft-review-interface]
3. Draft supports rich text editing and citation syntax highlighting. [Source: docs/epics.md#story-52-draft-review-interface][Source: docs/ux-design-specification.md]

## Tasks / Subtasks

-   [ ] Design queue item DTO (query, context_chunks[], draft_text, confidence_pct, bot_name, created_at, status). (AC: 1)
-   [ ] Implement backend API to fetch queue item details and update draft. (AC: 1,3)
-   [ ] Build frontend split view: left (query/context), right (editable draft), top bar (confidence, bot name, time). (AC: 1)
-   [ ] Add expandable/collapsible context chunk UI; make sources clickable. (AC: 2)
-   [ ] Integrate rich text editor for draft with citation highlighting. (AC: 3)
-   [ ] Testing: backend unit/contract tests for API; frontend component/e2e tests for split view, editing, context chunk expansion, citation highlighting. (AC: 1,2,3)

## Dev Notes

-   Rich text editor: use Tiptap or similar for draft editing; support citation syntax (e.g., [Source: ...]). [Source: docs/ux-design-specification.md]
-   Context chunk UI: expandable/collapsible, show source doc name, allow click to open doc in new tab. [Source: docs/epics.md]
-   Data flow: queue item fetched by ID; draft updated via API on edit/approve. [Source: docs/tech-spec.md]
-   UX: split view layout, confidence badge, time in queue, bot name; follow shadcn/ui patterns. [Source: docs/ux-design-specification.md]

### Project Structure Notes

-   Backend: `apps/api/app/services/` (queue service), `apps/api/app/api/v1/` (queue routes), migrations in `apps/api/alembic`.
-   Frontend: `apps/web/src/app/(dashboard)/hitl/review/` (page + components), shared hooks for queue item fetch/edit.
-   Shared types: add queue item DTO to `packages/shared` for FE/BE alignment.

### References

-   [Source: docs/epics.md#story-52-draft-review-interface]
-   [Source: docs/prd.md]
-   [Source: docs/architecture.md]
-   [Source: docs/tech-spec.md]
-   [Source: docs/ux-design-specification.md]

## Dev Agent Record

### Context Reference

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List

## Change Log

-   2025-12-10: Draft created (status set to drafted).
