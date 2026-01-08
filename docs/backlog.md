# Engineering Backlog

This backlog collects cross-cutting or future action items that emerge from reviews and planning.

Routing guidance:

- Use this file for non-urgent optimizations, refactors, or follow-ups that span multiple stories/epics.
- Must-fix items to ship a story belong in that story’s `Tasks / Subtasks`.
- Same-epic improvements may also be captured under the epic Tech Spec `Post-Review Follow-ups` section.

| Date | Story | Epic | Type | Severity | Owner | Status | Notes |
| ---- | ----- | ---- | ---- | -------- | ----- | ------ | ----- |
| 2026-01-08 | 7.2 | 7 | Enhancement | High | TBD | Open | Implement optional in-memory cache for verified KB hot questions; scope-aware keys; respect `VERIFIED_KB_CACHE_ENABLED` and `VERIFIED_KB_CACHE_TTL_SECONDS`. |
| 2026-01-08 | 7.2 | 7 | Test | Medium | TBD | Open | Add integration performance test validating verified lookup path stays <50ms under realistic load (pgvector + test DB). |