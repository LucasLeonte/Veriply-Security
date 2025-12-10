# Story 5.3: Approve & Edit Flow

Status: drafted

## Requirements Context Summary

- Epic goal: allow agents to approve or edit AI drafts before sending, ensuring only accurate answers reach users. [Source: docs/epics.md#story-53-approve-edit-flow]
- Product intent: trust-first workflow, agent approval triggers response send and Verified KB update; edits tracked for analytics. [Source: docs/prd.md]
- Architecture guardrails: Next.js frontend, FastAPI backend, PostgreSQL + pgvector; atomic transaction for send/store/dequeue, diff tracking for edits. [Source: docs/architecture.md][Source: docs/tech-spec.md]
- UX cues: approve button, edit field, diff view, success toast, auto-load next item. [Source: docs/ux-design-specification.md]

## Structure Alignment Summary

- Backend: API endpoint to approve/edit draft, send response, update Verified KB, dequeue item, record diff if edited.
- Frontend: HITL dashboard approve/edit UI, approve button (disabled until >3s review), edit field, diff view, success toast, auto-load next item.
- Data model: queue item includes draft_text, status, diff (if edited), response_sent, verified_kb_updated.

## Story

As an Agent,
I want to approve or edit a draft before sending,
so that only accurate answers reach the user.

## Acceptance Criteria

1. Approve button sends response, updates Verified KB, removes item from queue, auto-loads next item. [Source: docs/epics.md#story-53-approve-edit-flow]
2. Edit field allows agent to modify draft; system records diff between AI and human edit. [Source: docs/epics.md#story-53-approve-edit-flow][Source: docs/ux-design-specification.md]
3. Approve button disabled until agent reviews for >3 seconds; success toast on send. [Source: docs/epics.md#story-53-approve-edit-flow]

## Tasks / Subtasks

- [ ] Implement backend API for approve/edit flow: send response, update Verified KB, dequeue item, record diff. (AC: 1,2)
- [ ] Build frontend approve/edit UI: approve button, edit field, diff view, success toast, auto-load next item. (AC: 1,2,3)
- [ ] Add approve button disabled state until >3s review. (AC: 3)
- [ ] Testing: backend unit/contract tests for approve/edit API; frontend component/e2e tests for approve/edit UI, diff view, toast, auto-load. (AC: 1,2,3)

## Dev Notes

- Atomic transaction: send response, update KB, dequeue item in one step. [Source: docs/architecture.md]
- Diff tracking: store AI vs human edit for analytics; show diff view in UI. [Source: docs/ux-design-specification.md]
- UX: approve button, edit field, success toast, auto-load next item; follow shadcn/ui patterns. [Source: docs/ux-design-specification.md]

### Project Structure Notes

- Backend: `apps/api/app/services/` (queue service), `apps/api/app/api/v1/` (approve/edit routes), migrations in `apps/api/alembic`.
- Frontend: `apps/web/src/app/(dashboard)/hitl/approve/` (page + components), shared hooks for approve/edit.
- Shared types: add approve/edit DTO to `packages/shared` for FE/BE alignment.

### References

- [Source: docs/epics.md#story-53-approve-edit-flow]
- [Source: docs/prd.md]
- [Source: docs/architecture.md]
- [Source: docs/tech-spec.md]
- [Source: docs/ux-design-specification.md]

## Dev Agent Record

### Context Reference

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List

## Change Log

- 2025-12-10: Draft created (status set to drafted).