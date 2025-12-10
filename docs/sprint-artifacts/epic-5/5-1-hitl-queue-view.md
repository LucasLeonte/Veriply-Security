# Story 5.1: HITL Queue View

Status: drafted

## Requirements Context Summary

- Epic goal: build the agent dashboard queue so agents see pending low-confidence items with query preview, bot name, confidence %, and wait time, sorted oldest-first. [Source: docs/epics.md#epic-5-hitl-verification]
- Product intent: trust-first workflow where low-confidence answers route to HITL review before sending; must surface confidence and queue aging. [Source: docs/prd.md]
- Architecture guardrails: Next.js 14 frontend, FastAPI backend, PostgreSQL + pgvector with RLS; real-time updates recommended via WebSocket with Redis/queue backend. [Source: docs/architecture.md][Source: docs/tech-spec.md]
- UX cues: trust signals and queue density, with clear empty state messaging for agents. [Source: docs/ux-design-specification.md]

## Structure Alignment Summary

- Target paths: backend queue APIs and data model in `apps/api`; frontend dashboard queue in `apps/web` HITL dashboard view.
- Multi-tenancy: enforce tenant_id/bot_id filters on queue queries; reuse existing auth/session middleware patterns.
- Real-time channel: WebSocket or SSE endpoint backed by Redis/pub-sub to stream queue updates; fall back to polling if needed.
- Data model: `review_queue` table with status, bot_id, query preview, confidence %, created_at; index on (tenant_id, status, created_at) for ordering.

## Story

As an Agent,
I want to see a queue of pending review items,
so that I know what needs my attention.

## Acceptance Criteria

1. Queue shows item count badge and a list sorted by oldest-first; each item displays query preview, bot name, confidence %, and time waiting. [Source: docs/epics.md#story-51-hitl-queue-view]
2. Queue updates in real time when new items arrive without manual refresh (WebSocket/SSE; polling fallback acceptable for resiliency). [Source: docs/epics.md#story-51-hitl-queue-view][Source: docs/architecture.md]
3. Empty state displayed: "No items pending review. Nice work!" when the queue is empty. [Source: docs/epics.md#story-51-hitl-queue-view]

## Tasks / Subtasks

- [ ] Design and migrate `review_queue` schema (tenant_id, bot_id, query_preview, confidence_pct, time_waiting/created_at, status=pending/in_progress), plus index for (tenant_id, status, created_at). (AC: 1)
- [ ] Implement API/handler to list queue items oldest-first with pagination and filters; enforce RLS/tenant scoping. (AC: 1)
- [ ] Implement real-time stream (WebSocket/SSE) emitting queue changes; include fallback polling interval when socket unavailable. (AC: 2)
- [ ] Build frontend queue view in HITL dashboard: badge count, sorted list tiles with required fields, empty state copy. (AC: 1,3)
- [ ] Add auth/permissions guard so only authorized agents can access queue for their tenant/bot. (AC: 1)
- [ ] Testing: backend unit/contract tests for queue API and WebSocket; frontend component test for rendering badge/list/empty state; e2e happy-path covering real-time update. (AC: 1,2,3)

## Dev Notes

- Real-time: prefer WebSocket channel from FastAPI (or ASGI lifespan) backed by Redis pub/sub for queue events; ensure reconnect/backoff and heartbeat. [Source: docs/architecture.md]
- Ordering: default sort created_at ascending to satisfy oldest-first; expose secondary sort by time_waiting for consistency. [Source: docs/epics.md#story-51-hitl-queue-view]
- Data flow: queue entries produced by low-confidence routing (Epic 3 story 3.4); story remains blocked until that feed exists—plan mock fixtures for frontend dev. [Source: docs/epics.md#story-34-confidence-scoring-routing]
- Multi-tenancy & security: apply tenant_id/bot_id filters server-side; ensure WebSocket topics are tenant-scoped; no cross-tenant leakage. [Source: docs/tech-spec.md]
- UX: apply trust-first styling with badge semantics (pending/amber); keep list dense per Zendesk-like layout; reuse shadcn/ui patterns. [Source: docs/ux-design-specification.md]

### Project Structure Notes

- Backend: `apps/api/app/services/` (queue service), `apps/api/app/api/v1/` (queue routes/WS), migrations in `apps/api/alembic`.
- Frontend: `apps/web/src/app/(dashboard)/hitl/` (page + components), shared hooks for WebSocket client.
- Shared types: add queue item DTO to `packages/shared` if available for FE/BE alignment.

### References

- [Source: docs/epics.md#epic-5-hitl-verification]
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