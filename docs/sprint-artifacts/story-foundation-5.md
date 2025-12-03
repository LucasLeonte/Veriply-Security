# Story 1.5: Secrets Management & Configuration

**Epic:** 1. Foundation & App Shell
**Status:** Drafted
**Context:** Architecture gaps called out in docs/validation-report-architecture.md (centralize secrets into .env; remove hard-coded credentials)

## Story

As a developer and operator,
I want all secrets and environment-specific configuration to be centralized in .env files and loaded via typed settings,
so that the system is secure-by-default, portable across environments, and compliant with good DevOps practices.

## Acceptance Criteria

- [ ] .env.example files exist at repository root, apps/api, and apps/web with documented variables and placeholders (no real secrets).
- [ ] .env files are ignored by Git; secrets never committed. Root .gitignore contains .env rule (verified).
- [ ] Docker Compose loads environment variables from root .env; services can override via service-level env.
- [ ] FastAPI loads configuration via a Pydantic BaseSettings class (e.g., `app/core/settings.py`) and uses environment variables for DB URL, JWT secret, and Ollama host.
- [ ] Next.js reads API URL and NextAuth secrets from environment variables; local dev uses `.env.local`.
- [ ] No hard-coded credentials remain in the repo (scan using gitleaks or similar); create a pre-commit hook to prevent accidental commits of secrets.
- [ ] Minimal smoke tests prove configuration is loaded (API returns 200 on `/healthz` with correct config-derived settings; web renders page consuming NEXT_PUBLIC_API_URL).
- [ ] Documentation in README.md updated to explain env setup and variables.

## Tasks / Subtasks

1) Repository-level env scaffolding
- [ ] Add root `.env.example` with Postgres, Ollama, JWT, NextAuth, and observability vars
- [ ] Add `apps/api/.env.example` and `apps/web/.env.local.example`
- [ ] Double-check `.gitignore` includes `.env*` patterns (root and apps/web already configured)

2) FastAPI typed settings
- [ ] Create `apps/api/app/core/settings.py` with Pydantic BaseSettings and defaults
- [ ] Wire settings into `main.py` and database initialization code
- [ ] Replace any inline constants with references to `settings`

3) Docker Compose integration
- [ ] Load root `.env` from compose; verify services receive values
- [ ] Document overrides per-environment (e.g., CI uses different values)

4) Next.js configuration
- [ ] Use `.env.local` for local dev; document `NEXT_PUBLIC_API_URL`, `NEXTAUTH_URL`, `NEXTAUTH_SECRET`
- [ ] Verify pages can call the API URL from env (basic fetch on a server action or route)

5) Secrets scanning & pre-commit
- [ ] Add `gitleaks` config and a CI step to scan PRs
- [ ] Add a pre-commit hook (optional) to run `gitleaks protect` locally

6) Tests & docs
- [ ] Add a small API test asserting settings resolve (pytest) and `/healthz` reports OK
- [ ] Update top-level README with an "Environment Setup" section

## Dev Notes

- Architecture report flags secrets management as a gap to close for MVP; this story addresses that gap directly.
- Keep variable names consistent across Docker, API, and Web to reduce friction.
- Consider `python-dotenv` in local dev for API (optional); not needed in containers.

### Project Structure Notes

- API settings module target: `apps/api/app/core/settings.py`
- Web env files: `apps/web/.env.local` (local use only) and `.env.production.local` for prod overrides (not tracked).

### References

- docs/validation-report-architecture.md#Gaps-/-Actions
- docker-compose.yml
- apps/web/.gitignore
- .gitignore (root)

## Dev Agent Record

### Context Reference

- N/A (story context XML will be produced by `story-context` workflow)

### Agent Model Used

GPT-5

### Debug Log References

- N/A

### Completion Notes List

- Created env scaffolding examples for root, API, and Web
- Updated sprint-status with development_status entries

### File List

- NEW: `.env.example`
- NEW: `apps/api/.env.example`
- NEW: `apps/web/.env.local.example`
- NEW: `docs/sprint-artifacts/story-foundation-5.md`
