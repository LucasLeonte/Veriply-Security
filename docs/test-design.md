# Veriply — System Test Design (Initial)

Scope: End-to-end and system-level testability review aligned with current architecture and PRD.

Targets:
- APIs: FastAPI services in `apps/api` (search, ingestion, health)
- Frontend: Next.js 14 App Router in `apps/web`
- Data: PostgreSQL + pgvector (`embeddings` table)
- Models: Ollama (bge-m3 embeddings), mock provider for deterministic tests

## Test Strategy

Principles:
- Risk-based: prioritize multi-tenancy isolation, data integrity, and HITL verification flows
- Deterministic tests where possible (mock embeddings)
- Fast feedback: API unit/integration, E2E smoke, then deep scenarios

Layers:
1. Unit tests (API/web): Controllers, services, utils
2. Integration tests: DB + embedding providers (mock first, Ollama when available)
3. E2E tests: User flows (knowledge ingestion → search → verification)
4. Non-functional checks: latency, reliability, security basics

## Key Test Scenarios

1. Ingestion pipeline
- Given docs in `/docs`, when running ingestion with `--provider mock`, then chunks and vectors are inserted into `embeddings` and metadata captures source path.
- Error paths: missing folder, DB unavailable, invalid vector dimension.

2. Search API
- Given a query, when embeddings exist, then `/search` returns top-k with similarity and metadata parsed.
- Validate behavior when Ollama unavailable: proper HTTP 500 with clear message.
- Tenant isolation (future): queries scoped by `tenant_id`.

3. Health endpoints
- `/health` returns model and ok status.

4. Frontend smoke
- Next.js page renders, API integration available, basic SSR/CSR checks.

## Test Data & Fixtures
- Deterministic vectors via `deterministic_vector()` ensure stable similarity ordering.
- Small sample docs under `docs/` used for ingestion tests.

## Tooling
- Python: pytest, httpx/aiohttp for API tests, async fixtures
- Web: Playwright or Cypress for E2E (prefer Playwright for SSR)
- CI: add jobs for lint, unit, integration, E2E (matrix for mock vs Ollama)

## Quality Gates
- Unit/integration pass required before merge
- E2E smoke required on main
- Latency budget: search p95 < 200ms (mock), track when Ollama enabled

## Next Actions
- Add pytest suite under `apps/api/tests` expanding current tests
- Scaffold Playwright under `apps/web` with a smoke test
- Implement tenant_id filtering in search when multitenancy enabled

