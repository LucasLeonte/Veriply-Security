# Story 1.1: Project Initialization & Monorepo Setup

**Epic:** 1. Foundation & App Shell
**Status:** Done
**Context:** [Tech Spec](../tech-spec.md)

## Description
Initialize the project repository with a Monorepo structure containing the Next.js frontend, FastAPI backend, and Docker infrastructure (including Ollama).

## Tasks
1.  **Git Initialization:**
    *   Initialize git repo.
    *   Create `.gitignore` (Node, Python, Docker).
    *   Set up `main` branch protection rules (if possible locally, or document for GitHub).

2.  **Monorepo Structure:**
    *   Create folders: `apps/web`, `apps/api`, `packages/shared`, `docker`.
    *   Initialize `apps/web` with Next.js 14 (TypeScript, Tailwind).
    *   Initialize `apps/api` with FastAPI (Poetry or pip).

3.  **Docker Infrastructure:**
    *   Create `docker-compose.yml`.
    *   Add **PostgreSQL 16** service (with `pgvector` image).
    *   Add **Redis** service.
    *   Add **Ollama** service with custom entrypoint to pull `llama3` and `nomic-embed-text`.

4.  **CI/CD Setup:**
    *   Create `.github/workflows/ci.yml`.
    *   Add jobs for Linting (ESLint/Ruff) and Testing (Vitest/Pytest).

## Acceptance Criteria
*   [ ] `npm run dev` starts frontend (localhost:3000) and backend (localhost:8000).
*   [ ] Docker Compose up spins up DB, Redis, and Ollama without errors.
*   [ ] Ollama service responds to `curl http://localhost:11434/api/tags` with `llama3`.
*   [ ] GitHub Action `ci.yml` passes on a dummy PR.

## Technical Notes
*   **Ollama Dockerfile:**
    ```dockerfile
    FROM ollama/ollama
    COPY ./pull-models.sh /pull-models.sh
    ENTRYPOINT ["/bin/bash", "/pull-models.sh"]
    ```
*   **Ports:** Web: 3000, API: 8000, DB: 5432, Redis: 6379, Ollama: 11434.

## Dev Agent Record

### Completion Notes
**Completed:** 2025-12-03
**Definition of Done:** All acceptance criteria met, code reviewed, tests passing

**Implementation Summary:**
- ✅ Monorepo structure established (apps/web, apps/api, packages/shared, docker)
- ✅ Next.js 14 frontend with TypeScript and Tailwind CSS
- ✅ FastAPI backend with Python virtual environment
- ✅ Docker Compose configuration (PostgreSQL 16 + pgvector, Redis, Ollama)
- ✅ GitHub Actions CI/CD pipeline with linting and testing
- ✅ All tests passing (frontend: 1/1, backend: 1/1)

