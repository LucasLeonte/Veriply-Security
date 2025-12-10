# Story 5.4: Rejection Flow

Status: drafted

## Requirements Context Summary

-   Epic goal: allow agents to reject poor AI drafts with a reason, log analytics, and optionally write a correct answer. [Source: docs/epics.md#story-54-rejection-flow]
-   Product intent: trust-first workflow, rejection reasons feed analytics, manual correction option, auto-load next item. [Source: docs/prd.md]
-   Architecture guardrails: Next.js frontend, FastAPI backend, PostgreSQL; rejection modal, reason logging, optional manual answer, alert on high rejection rate. [Source: docs/architecture.md][Source: docs/tech-spec.md]
-   UX cues: rejection modal, reason selection, optional manual answer, auto-load next item, alerting. [Source: docs/ux-design-specification.md]

## Structure Alignment Summary

-   Backend: API endpoint to reject draft, log reason, optionally accept manual answer, dequeue item, trigger alert if rejection rate high.
-   Frontend: HITL dashboard rejection UI, modal for reason selection, manual answer field, auto-load next item, alerting.
-   Data model: queue item includes rejection_reason, manual_answer (optional), status, rejection_logged, alert_triggered.

## Story

As an Agent,
I want to reject bad drafts with a reason,
so that the system learns from failures.

## Acceptance Criteria

1. Rejection modal appears with reason options; agent selects reason and confirms. [Source: docs/epics.md#story-54-rejection-flow]
2. Item is removed from queue, reason is logged, agent can optionally write a correct answer. [Source: docs/epics.md#story-54-rejection-flow]
3. Rejection reasons feed analytics; alert triggers on high rejection rate. [Source: docs/epics.md#story-54-rejection-flow][Source: docs/ux-design-specification.md]
4. Auto-load next item after rejection. [Source: docs/epics.md#story-54-rejection-flow]

## Tasks / Subtasks

-   [ ] Implement backend API for rejection flow: log reason, manual answer, dequeue item, trigger alert. (AC: 1,2,3,4)
-   [ ] Build frontend rejection UI: modal, reason selection, manual answer field, auto-load next item, alerting. (AC: 1,2,3,4)
-   [ ] Testing: backend unit/contract tests for rejection API; frontend component/e2e tests for modal, reason selection, manual answer, alert, auto-load. (AC: 1,2,3,4)

## Dev Notes

-   Rejection modal: reason options (hallucination, wrong tone, outdated, irrelevant, other); manual answer field optional. [Source: docs/epics.md]
-   Analytics: log rejection reason, feed to dashboard; trigger alert if rate exceeds threshold. [Source: docs/architecture.md]
-   UX: modal, reason selection, manual answer, auto-load next item, alerting; follow shadcn/ui patterns. [Source: docs/ux-design-specification.md]

### Project Structure Notes

-   Backend: `apps/api/app/services/` (queue service), `apps/api/app/api/v1/` (rejection routes), migrations in `apps/api/alembic`.
-   Frontend: `apps/web/src/app/(dashboard)/hitl/reject/` (page + components), shared hooks for rejection flow.
-   Shared types: add rejection DTO to `packages/shared` for FE/BE alignment.

### References

-   [Source: docs/epics.md#story-54-rejection-flow]
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
