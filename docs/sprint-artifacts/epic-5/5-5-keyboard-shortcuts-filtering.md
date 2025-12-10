# Story 5.5: Keyboard Shortcuts & Filtering

Status: drafted

## Requirements Context Summary

-   Epic goal: enable agents to process HITL queue efficiently using keyboard shortcuts and filters. [Source: docs/epics.md#story-55-keyboard-shortcuts-filtering]
-   Product intent: trust-first workflow, maximize agent productivity with shortcuts and persistent filters. [Source: docs/prd.md]
-   Architecture guardrails: Next.js frontend, FastAPI backend; keyboard event listeners, filter state in URL, persistent filter count. [Source: docs/architecture.md][Source: docs/tech-spec.md]
-   UX cues: shortcut help modal, filter dropdowns, persistent filter state, filtered count in header. [Source: docs/ux-design-specification.md]

## Structure Alignment Summary

-   Backend: API endpoint to list queue items with filters (bot, date, status); support keyboard shortcut actions (approve, reject, edit, next).
-   Frontend: HITL dashboard keyboard shortcut listeners, filter UI (dropdowns, date picker, status), shortcut help modal, persistent filter state in URL, filtered count in header.
-   Data model: queue item includes bot_id, date, status; filter state stored in URL/query params.

## Story

As an Agent,
I want keyboard shortcuts and filters,
so that I can process the queue efficiently.

## Acceptance Criteria

1. Keyboard shortcuts: A=Approve, R=Reject, E=Edit, N=Next, ←/→=Navigate, ?=Show shortcut help. [Source: docs/epics.md#story-55-keyboard-shortcuts-filtering]
2. Filter UI: bot dropdown, date range picker, status dropdown; filter state persists in URL. [Source: docs/epics.md#story-55-keyboard-shortcuts-filtering]
3. Filtered count shows in header; shortcut help modal displays all shortcuts. [Source: docs/epics.md#story-55-keyboard-shortcuts-filtering][Source: docs/ux-design-specification.md]

## Tasks / Subtasks

-   [ ] Implement backend API to list queue items with filters; support shortcut actions. (AC: 1,2)
-   [ ] Build frontend keyboard shortcut listeners, filter UI, shortcut help modal, persistent filter state, filtered count. (AC: 1,2,3)
-   [ ] Testing: backend unit/contract tests for filter API; frontend component/e2e tests for shortcut listeners, filter UI, help modal, persistent state, filtered count. (AC: 1,2,3)

## Dev Notes

-   Keyboard shortcuts: event listeners for A, R, E, N, ←/→, ?; modal for help. [Source: docs/epics.md]
-   Filter UI: dropdowns for bot/status, date picker; filter state in URL/query params, persists across reloads. [Source: docs/ux-design-specification.md]
-   UX: filtered count in header, shortcut help modal, persistent filter state; follow shadcn/ui patterns. [Source: docs/ux-design-specification.md]

### Project Structure Notes

-   Backend: `apps/api/app/services/` (queue service), `apps/api/app/api/v1/` (filter routes), migrations in `apps/api/alembic`.
-   Frontend: `apps/web/src/app/(dashboard)/hitl/filters/` (page + components), shared hooks for filter state.
-   Shared types: add filter DTO to `packages/shared` for FE/BE alignment.

### References

-   [Source: docs/epics.md#story-55-keyboard-shortcuts-filtering]
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
