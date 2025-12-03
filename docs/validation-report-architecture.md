# Veriply — Architecture Validation Report (v1)

Objective: Validate the architectural decisions against PRD, UX, and testability; identify risks and actions.

## Summary
- Architecture aligns with PRD and repo stack (FastAPI, Next.js, Postgres + pgvector, Ollama).
- Key risks: multitenancy enforcement (RLS), secrets management, observability maturity.
- Recommendation: proceed with MVP; track risks via tickets.

## Validation Criteria

1. Functional Fit
- RAG Q&A with HITL supported by ingestion worker, embeddings storage, and search API.
- Frontend and backend scaffolds exist; integration to be expanded.

2. Non-Functional Requirements
- Latency targets feasible for mock embeddings; Ollama targets to be measured.
- Security/compliance addressed in design (JWT, GDPR, audit trails); implementation pending.

3. Scalability & Reliability
- pgvector suitable for MVP scale; partitioning/sharding guidance included.
- Observability planned (Prometheus/Grafana, Sentry) — add OpenTelemetry tracing.

4. Operability & Cost
- Docker Compose for dev; Kubernetes planned for prod.
- Self-hosted Ollama acceptable for privacy/cost; managed LLMs as fallback.

5. Testability
- `docs/test-design.md` set; deterministic embeddings for stable tests.

## Gaps / Actions
- Implement RLS and tenant_id propagation.
- Centralize secrets into `.env`, remove hard-coded credentials.
- Add CI pipelines for lint/tests (API & web) and smoke E2E.
- Instrument APIs with metrics/traces; error budgets.

## Decision Outcomes
- Proceed with MVP on current architecture.
- Track gaps in backlog; validate performance under Ollama in staging.

Status: VALIDATED (with follow-ups)
