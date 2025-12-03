# Veriply — Implementation Readiness Checklist (v1)

Goal: Validate alignment across PRD, UX Design, Architecture, and Epics, and confirm technical scaffolding is runnable.

## Inputs Reviewed
- PRD: `docs/prd.md`
- UX Design: `docs/ux-design-specification.md`
- Architecture: `docs/architecture.md`
- Epics & Stories: `docs/epics.md`
- Codebase: `apps/api`, `apps/web`, Docker configs

## Readiness Criteria

1. Requirements Alignment
- PRD features traceable to epics and initial stories
- Non-functional requirements (latency, security, compliance) reflected in architecture

2. Architecture Feasibility
- Selected stack matches repo: FastAPI + Next.js + Postgres/pgvector + Ollama
- Multitenancy strategy acknowledged (RLS to be implemented)
- Ingestion + search paths present (`ingest_worker.py`, `search_api.py`)

3. UX Integration
- App structure present (`apps/web/src/app`), pages scaffolded
- HITL flows planned; basic UI theme and components (shadcn/ui) defined in UX spec

4. Test Strategy in place
- System Test Design created: `docs/test-design.md`
- Initial tests exist in `apps/api/tests` and `apps/web/__tests__`

5. Environments & Config
- Local dev via Docker Compose available
- DB connection strings configured; placeholders to move to `.env`
- Ollama embeddings endpoint configured with fallbacks in ingestion worker

6. Run-Ability
- API can start with uvicorn
- Ingestion can run with `--provider mock`
- Web can start and render a basic page

## Gaps / Follow-ups
- Implement tenant_id filtering and RLS policies in DB
- Centralize secrets via `.env` and avoid hard-coded credentials
- Add CI jobs for lint/test (API and web) and minimal E2E smoke
- Strengthen observability (metrics/traces) and error handling

## Next Steps
- Proceed to Sprint Planning with scoped epics and initial stories
- Create tickets per gap above to track work

Status: READY for implementation (MVP scope)
