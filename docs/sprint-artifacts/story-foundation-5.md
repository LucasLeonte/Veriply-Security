# Story 1.5: Secrets Management & Configuration + Centralized Database

**Epic:** 1. Foundation & App Shell
**Status:** In Progress
**Context:** Architecture gaps called out in docs/validation-report-architecture.md (centralize secrets into .env; remove hard-coded credentials). 4-developer team shares a centralized PostgreSQL database on a Linux Ubuntu server for both dev and prod.

## Story

As a developer and operator,
I want all secrets and environment-specific configuration to be centralized in .env files and loaded via typed settings, AND connect all developer machines and production to a single centralized PostgreSQL database on a Linux Ubuntu server,
so that the system is secure-by-default, portable across environments, compliant with good DevOps practices, and allows seamless collaboration across the dev team.

## Acceptance Criteria

### Secrets & Configuration (Single Centralized `.env`)
- [ ] **SINGLE SOURCE OF TRUTH:** One `.env` file at repository root contains ALL configuration for all services (API, Web, Database, etc.).
- [ ] `.env.example` exists at repository root with documented variables and placeholders (no real secrets); developers copy to `.env` for local/server use.
- [ ] `.env` file is ignored by Git; secrets never committed. Root `.gitignore` contains `.env` rule (verified).
- [ ] All services (Docker Compose, FastAPI, Next.js, etc.) reference the root `.env` file—no redundant per-service `.env` files.
- [ ] FastAPI loads configuration via a Pydantic BaseSettings class (e.g., `app/core/settings.py`) that reads from the root `.env`.
- [ ] Next.js reads API URL and NextAuth secrets from the root `.env` during build and runtime; Next.js `.env.local` is NOT used (all config comes from root `.env`).
- [ ] Docker Compose explicitly loads root `.env` file; all containers inherit variables from single source.
- [ ] No hard-coded credentials remain in the repo (scan using gitleaks or similar); create a pre-commit hook to prevent accidental commits of secrets.

### Centralized Database (Linux Ubuntu Server)
- [ ] PostgreSQL database running in Docker container on central Ubuntu server with persistent volume storage.
- [ ] Database accessible via network connection string: `postgresql://{db_user}:{db_password}@{server_ip}:5432/{db_name}`.
- [ ] All 4 developer machines configured to connect to central DB via `.env` files (DB_HOST points to server IP, not localhost).
- [ ] Production database uses same PostgreSQL setup on production Ubuntu server with separate credentials in prod `.env`.
- [ ] Database connection pooling configured in FastAPI to handle multiple concurrent connections from 4 developers + API instances.
- [ ] Health check endpoint `/healthz` verifies DB connectivity and returns 200 when connected.
- [ ] Database migrations (Alembic) can run from any developer machine or during deployment.
- [ ] Documentation includes setup instructions for adding new developer machines (set DB_HOST, DB_USER, DB_PASSWORD in .env).

### Testing & Documentation
- [ ] Minimal smoke tests prove configuration is loaded (API returns 200 on `/healthz` with correct config-derived settings; web renders page consuming NEXT_PUBLIC_API_URL).
- [ ] Test can verify connection to central DB and query execution succeeds.
- [ ] Documentation in README.md updated to explain env setup, variables, and centralized database connection steps.
- [ ] Team onboarding guide includes: getting DB credentials, setting .env values, verifying connection from new machine.

## Tasks / Subtasks

### 1) Repository-level env scaffolding (Single Centralized `.env`)
- [x] Add root `.env.example` with ALL variables needed across all services:
  - Database: `DB_HOST`, `DB_USER`, `DB_PASSWORD`, `DB_PORT`, `DB_NAME`
  - Ollama: `OLLAMA_HOST`, `OLLAMA_PORT`
  - JWT/Auth: `JWT_SECRET`, `NEXTAUTH_SECRET`, `NEXTAUTH_URL`
  - Next.js: `NEXT_PUBLIC_API_URL`, `NEXT_PUBLIC_APP_URL`
  - Observability: any logging/monitoring vars
  - Other: any additional service-specific secrets
- [x] Add `apps/api/.env.example` that references the root `.env` (e.g., sourcing it or loading from parent directory)
- [x] Add `apps/web/.env.example` that references the root `.env` (e.g., sourcing it or loading from parent directory)
- [x] Each app's `.env` file points to/inherits from central root `.env` so configuration is not duplicated
- [x] Verify root `.gitignore` includes `.env` rule (verify `.gitignore` entries allow `.env.example` to be committed but block `.env`)
- [x] Document in `.env.example` which variables apply to which service for clarity

### 2) Centralized Database Setup (Ubuntu Server)
- [ ] **NEW:** Create Docker setup on Ubuntu server: PostgreSQL container with named volume for persistence
- [ ] **NEW:** Expose PostgreSQL on port 5432 (ensure firewall allows inbound on port 5432 from developer machines)
- [ ] **NEW:** Initialize DB with schema and initial migrations
- [ ] **NEW:** Create database user accounts for each developer + production account with appropriate permissions
- [ ] **NEW:** Document server setup: IP address, connection credentials, and backup/restore procedures
- [ ] **NEW:** Add health check in container to verify DB is running and accessible

### 3) FastAPI typed settings & centralized DB connection
- [x] Create `apps/api/app/core/settings.py` with Pydantic BaseSettings that reads from environment:
  - Load `DB_HOST`, `DB_USER`, `DB_PASSWORD`, `DB_PORT`, `DB_NAME` from environment
  - `DATABASE_URL` constructed as `postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}`
  - Connection pool settings (e.g., pool_size=10, max_overflow=20 for multiple concurrent dev connections)
  - Load `JWT_SECRET`, `OLLAMA_HOST` from environment
- [x] Wire settings into `main.py` and database initialization code
- [x] Replace any inline constants with references to `settings`
- [x] **NOTE:** `apps/api/.env` sources/references the root `.env` so environment variables are inherited

### 4) Docker Compose configuration
- [x] Root `docker-compose.yml`: explicitly load root `.env` file with `env_file: .env`
- [x] All services (API, web, postgres, ollama) inherit variables from root `.env`
- [x] Services use the root `.env` as the single source of truth; individual app `.env` files inherit from it
- [x] Production `docker-compose.yml` on Ubuntu server: same approach, uses production `.env` file on server
- [x] Document in docker-compose.yml comments which variables apply to which service

### 5) Next.js configuration
- [x] Create `apps/web/.env.example` documenting environment variable usage
- [x] Next.js reads `NEXT_PUBLIC_API_URL`, `NEXTAUTH_URL`, `NEXTAUTH_SECRET` from the inherited environment
- [x] Update `next.config.ts` to ensure environment variables are properly loaded during build
- [ ] Verify pages can call the API URL from environment (basic fetch on a server action or route)

### 6) Secrets scanning & pre-commit
- [ ] Add `gitleaks` config and a CI step to scan PRs
- [ ] Add a pre-commit hook (optional) to run `gitleaks protect` locally

### 7) Tests & docs
- [ ] Add a small API test asserting settings resolve (pytest) and `/healthz` reports OK
- [ ] Add integration test: verify connection to centralized DB succeeds (query a test table or run migration)
- [x] **NEW:** Add team onboarding guide: "Getting DB Access" with steps to request credentials, set .env values, and test connection from new machine
- [x] Update top-level README with sections:
  - "Environment Setup" (general secrets/config)
  - "Centralized Database Setup" (dev and prod connection instructions)
  - "Adding a New Developer" (one-time setup steps)

## Dev Notes

### Secrets & Configuration
- Architecture report flags secrets management as a gap to close for MVP; this story addresses that gap directly.
- **Single `.env` model** reduces friction and misconfiguration: one file to manage for all services.
- `.env.example` is the contract—document every variable, its purpose, and which service uses it.
- Consider `python-dotenv` in local dev for API (optional); Docker Compose will load `.env` automatically.

### Centralized Database Architecture
- **Single Source of Truth:** All 4 developers + production use ONE PostgreSQL instance on the Ubuntu server.
- **Single `.env` file** also simplifies database configuration—DB_HOST, DB_USER, DB_PASSWORD all in one place.
- **Connection String Pattern:** `postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}` built from `.env` vars
- **Network Security:** 
  - PostgreSQL port (5432) should be accessible only to authorized developer IPs (firewall rules or VPN).
  - Use strong DB passwords; do NOT commit `.env` to repo.
  - Consider IP whitelisting on the server to restrict access.
- **Local Testing Optional:** Developers can optionally edit `.env` to point to a local PostgreSQL container for isolated testing; production and main dev work use the central server.
- **Connection Pooling:** FastAPI must use connection pooling (e.g., pgbouncer or sqlalchemy pool settings) to handle multiple concurrent connections from 4 developers without exhausting DB resources.
- **Backup & Recovery:** Central server requires regular backups (e.g., daily dumps or WAL archiving). Document backup/restore procedures.
- **Migrations:** Alembic migrations should be idempotent so any developer can run them against the shared DB without conflicts.

### Project Structure Notes

- **Single `.env.example`** at repository root (committed to repo)—the source of truth
- **Root `.env`** file at repository root (NOT committed; each machine/server has its own)
- **`apps/api/.env`** sources/inherits from root `.env` so API settings can load all variables
- **`apps/web/.env`** sources/inherits from root `.env` so Next.js can access all variables at build time
- API settings module: `apps/api/app/core/settings.py` reads from environment
- Docker setup: `docker-compose.yml` at root (and on Ubuntu server) with `env_file: .env` loads the central `.env`
- All `.env` files (root, API, web) excluded from git via `.gitignore`; only `.env.example` files committed

### Ubuntu Server Setup Checklist
- Install Docker and Docker Compose
- Clone repo or pull latest code
- Copy `.env.example` to `.env` and edit with production values (DB credentials, API URLs, secrets, etc.)
- Run services with: `docker-compose up -d` (reads from root `.env`)
- Initialize schema: `alembic upgrade head` (run from a dev machine or server shell)
- All configuration managed via single `.env` file on server
- Document server IP and how to request DB credentials for team onboarding

### References

- docs/validation-report-architecture.md#Gaps-/-Actions
- docker-compose.yml
- docker/postgres/docker-compose.yml (new/updated)
- apps/web/.gitignore
- .gitignore (root)
- docs/TEAM-WELCOME.md (add onboarding steps)

## Dev Agent Record

### Context Reference

- docs/sprint-artifacts/story-foundation-5.context.xml

### Agent Model Used

Claude Sonnet 4.5

### Debug Log References

- N/A

### Completion Notes List

- Implemented single centralized `.env.example` at repository root with comprehensive documentation
- Created `apps/api/.env.example` and `apps/web/.env.example` as reference documentation (all config from root)
- Built `apps/api/app/core/settings.py` with Pydantic BaseSettings
  - Loads from root .env automatically via python-dotenv
  - Database connection pooling configured (pool_size=10, max_overflow=20)
  - Validates required secrets (JWT_SECRET, DB_PASSWORD)
  - Constructs DATABASE_URL from components
- Updated `apps/api/app/main.py`:
  - Integrated settings module
  - Added CORS middleware from settings
  - Created `/healthz` endpoint with config verification
- Updated `apps/api/app/core/database.py`:
  - Uses settings.DATABASE_URL with connection pooling
  - Pool configured for 4 concurrent developers
- Updated `docker-compose.yml`:
  - Automatically loads root `.env` file
  - Added health checks for all services
  - Added network configuration
  - Supports centralized DB via DB_HOST environment variable
- Updated `apps/web/next.config.ts` for environment variable loading
- Updated `.gitignore` files to allow `.env.example` but block `.env`
- Added comprehensive README documentation:
  - Environment setup quick start
  - Centralized database architecture explanation
  - Developer onboarding guide with step-by-step instructions
  - Server administration guide
  - Troubleshooting section
- Committed to feature branch: feature/1-5-secrets-management-configuration
- **PENDING**: Integration tests for health endpoint and DB connectivity
- **PENDING**: Secrets scanning setup (gitleaks)
- **PENDING**: Database server setup on Ubuntu (server admin task)

### File List

- MODIFIED: `.env.example` (comprehensive update with all variables)
- MODIFIED: `.gitignore` (allow .env.example)
- MODIFIED: `README.md` (added env setup and centralized DB documentation)
- MODIFIED: `apps/api/.env.example` (converted to reference doc)
- NEW: `apps/api/app/core/settings.py` (Pydantic settings module)
- MODIFIED: `apps/api/app/core/database.py` (use settings, connection pooling)
- MODIFIED: `apps/api/app/main.py` (settings integration, CORS, health check)
- NEW: `apps/web/.env.example` (reference documentation)
- MODIFIED: `apps/web/.gitignore` (allow .env.example)
- MODIFIED: `apps/web/next.config.ts` (env config documentation)
- MODIFIED: `docker-compose.yml` (env loading, health checks, network)
- MODIFIED: `docs/sprint-artifacts/sprint-status.yaml` (added story 1-5)
- MODIFIED: `docs/sprint-artifacts/story-foundation-5.md` (this file)
