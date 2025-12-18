# Story 1.7: CI Pipeline - Lint, Tests, and Smoke E2E

**Epic:** 1. Foundation & Auth  
**Status:** Review  
**Assigned to:** Unassigned  
**Blocked by:** None

## Story

As a developer and engineering team,
I want a robust CI pipeline that runs linting, unit tests, and smoke end-to-end tests on every PR and commit to main,
so that code quality is enforced, regressions are caught early, and deployments are reliable.

## Acceptance Criteria

### CI Workflow Execution
- [ ] CI workflow (`.github/workflows/ci.yml`) runs automatically on:
  - Every push to `main` branch
  - Every pull request (all branches → main)
- [ ] All CI jobs complete in under 5 minutes
- [ ] Job execution:
  - Lint jobs run in parallel (frontend + backend)
  - Test jobs run in parallel (frontend + backend, after lint)
  - Secrets scanning runs in parallel with lint/test
  - Smoke E2E runs after all other jobs pass

### Linting
- [ ] Frontend linting (ESLint) passes with zero errors and zero warnings
  - Runs on `apps/web/`
  - Config: `apps/web/eslint.config.mjs`
  - Fails CI if errors found
- [ ] Backend linting (Ruff) passes with zero errors
  - Runs on `apps/api/`
  - Config: `pyproject.toml` or `.ruff.toml`
  - Fails CI if errors found

### Unit Tests
- [ ] Frontend unit tests (Vitest) pass with coverage reports
  - Test files: `apps/web/**/__tests__/**/*.test.ts(x)`
  - Coverage report generated: `apps/web/coverage/`
  - Coverage threshold: 70% statements (warn if below)
  - Fails CI if tests fail
- [ ] Backend unit tests (Pytest) pass with coverage reports
  - Test files: `apps/api/tests/`
  - Coverage report generated: `apps/api/coverage/`
  - Coverage threshold: 70% statements (warn if below)
  - Fails CI if tests fail
- [ ] Coverage reports uploaded to Codecov or stored as artifacts
- [ ] Test timeout: individual tests max 30s

### Secrets Scanning
- [ ] Secrets scanning job (gitleaks) runs on all commits in PR
  - Config: `.gitleaks.toml` (root directory)
  - Detects: API keys, tokens, passwords, private keys
  - Fails CI if secrets detected
  - Provides actionable error message with location

### Smoke E2E Tests
- [ ] Smoke E2E job (`smoke-e2e`) runs after lint/test jobs
- [ ] Services started in CI environment:
  - PostgreSQL (via Docker)
  - Redis (via Docker, if needed)
  - API server (`apps/api`, http://localhost:8000)
  - Web frontend (`apps/web`, http://localhost:3000)
  - All via Docker Compose (`docker-compose.yml`)
- [ ] Services startup timeout: 30s max per service
- [ ] E2E tests verify critical paths:
  - [ ] API `/healthz` endpoint returns 200 OK
  - [ ] Web frontend loads (GET `/` returns 200)
  - [ ] Basic login flow (register user, login, verify JWT)
- [ ] E2E test framework: Playwright (preferred) or curl/bash scripts
- [ ] Test execution:
  - E2E tests run with headless browser (Playwright)
  - Timeout per test: 30s
  - Retry failed tests once
  - Fails CI if any test fails
- [ ] Artifacts on failure:
  - Screenshots captured
  - Browser logs saved
  - Docker service logs saved
  - All stored in CI artifacts for debugging

### Branch Protection
- [ ] GitHub branch protection rule enabled on `main`:
  - Require CI to pass before merge
  - Require status checks: all jobs must pass
  - Prevent force push
  - Dismiss stale PR reviews on push
- [ ] Cannot merge PR until all CI jobs pass

### Documentation
- [ ] README.md includes:
  - CI status badge (latest build status)
  - Instructions for running tests locally:
    - Frontend: `npm test` (Vitest)
    - Backend: `pytest` (Pytest)
    - E2E: `npm run test:e2e` (Playwright)
  - CI workflow overview (what runs, why, how to debug)
  - Troubleshooting section (common CI failures)

## Tasks / Subtasks

### 1) Review & Extend Existing CI Workflow
- [ ] Review `.github/workflows/ci.yml`:
  - Verify lint-frontend job exists and works
  - Verify lint-backend job exists and works
  - Verify test-frontend job exists and works
  - Verify test-backend job exists and works
  - Fix any broken jobs
- [ ] Verify all lint/test jobs run in parallel (not sequentially)
- [ ] Add job outputs for status reporting

### 2) Add Secrets Scanning Job
- [ ] Create `.gitleaks.toml` config file (root)
  - Enable default rules for API keys, tokens, credentials
  - Exclude test files and documentation files (.md, .txt)
  - Exclude files: `.gitleaks.toml`, `README.md`
- [ ] Add `gitleaks` GitHub Action job:
  - Action: `gitleaks-action`
  - Run on: every commit in PR and main
  - Fail on: any secrets detected
  - Provide clear error message with file/line

### 3) Add Smoke E2E Test Job
- [ ] Create job `smoke-e2e` in CI workflow:
  - Depends on: lint, test jobs (runs after)
  - Runs on: Ubuntu latest
- [ ] Docker setup:
  - Build/pull images from `docker-compose.yml`
  - Start services: `docker-compose up -d`
  - Wait for services ready (health checks)
  - Timeout: 60s total
- [ ] Create E2E test suite (use Playwright):
  - Tests location: `tests/e2e/` or `apps/web/tests/e2e/`
  - Test 1: API health check
    ```
    GET http://localhost:8000/healthz
    Expect: 200 OK
    ```
  - Test 2: Web frontend loads
    ```
    GET http://localhost:3000/
    Expect: 200, HTML contains "Veriply"
    ```
  - Test 3: Basic login flow
    ```
    Register user (POST /api/auth/register)
    Login (POST /api/auth/login)
    Verify JWT token received
    ```
- [ ] E2E test configuration:
  - Playwright config: `playwright.config.ts`
  - Headless mode: true
  - Screenshots on failure: enabled
  - Video on failure: optional (heavy in CI)
  - Timeout: 30s per test, 2 retries
- [ ] Artifact capture:
  - On failure: screenshots, logs, video (if enabled)
  - Store in: `test-results/` directory
  - Upload to CI artifacts
- [ ] Teardown:
  - Stop and remove Docker containers: `docker-compose down`
  - Clean up any temp files

### 4) Performance & Caching
- [ ] Add dependency caching:
  - npm cache: `npm install` → cache `node_modules/`
  - pip cache: `pip install` → cache `.pip/`
  - Docker layer caching: use buildkit, cache build stages
- [ ] Parallel job execution:
  - Lint jobs: run in parallel
  - Test jobs: run in parallel
  - Secrets scanning: run in parallel (doesn't block)
  - E2E: runs after others (sequential, depends on earlier jobs)
- [ ] Job timeouts:
  - Lint jobs: 10 min timeout max
  - Test jobs: 15 min timeout max
  - E2E job: 20 min timeout max
- [ ] Matrix builds (optional):
  - Run tests on multiple Node versions (if applicable)
  - Run tests on multiple Python versions (if applicable)

### 5) GitHub Configuration
- [ ] Configure branch protection on `main`:
  - Go to: Settings → Branches → Add rule
  - Branch name: `main`
  - Require pull request reviews: No (or yes, team preference)
  - Require status checks to pass: Yes
  - Status checks: Select all CI jobs (lint-frontend, lint-backend, test-frontend, test-backend, gitleaks, smoke-e2e)
  - Require branches to be up to date: Yes
  - Dismiss stale reviews: Yes
  - Restrict who can push: No (or yes, team preference)
- [ ] Add CI badge to README.md:
  ```markdown
  [![CI Status](https://github.com/DarioDML/Veriply/workflows/CI/badge.svg)](https://github.com/DarioDML/Veriply/actions)
  ```

### 6) Update README.md
- [ ] Add section: "Development & Testing"
  - Running tests locally:
    ```bash
    # Frontend
    cd apps/web
    npm install
    npm test              # Vitest
    npm run test:e2e      # Playwright E2E
    
    # Backend
    cd apps/api
    pip install -r requirements.txt
    pytest                # Pytest
    ```
  - Running linting:
    ```bash
    # Frontend
    cd apps/web
    npm run lint
    
    # Backend
    cd apps/api
    ruff check .
    ```
- [ ] Add section: "CI/CD Pipeline"
  - Describe what runs on every PR/commit
  - Link to GitHub Actions
  - Troubleshooting tips
- [ ] Add CI status badge at top of README

### 7) Testing the CI Pipeline
- [ ] Create test PR with intentional issues:
  - Lint error in frontend → verify CI catches it
  - Test failure in backend → verify CI catches it
  - Committed secret (fake) → verify gitleaks catches it
- [ ] Verify E2E tests run and pass
- [ ] Verify merge is blocked until all CI passes
- [ ] Verify CI is unblocked once issues fixed

## Dev Notes

- **Existing CI:** Start by reviewing what's already in `.github/workflows/ci.yml`; don't rebuild, extend it
- **Gitleaks:** Use default rules unless specific false positives; customize `.gitleaks.toml` as needed
- **E2E scope:** Keep smoke tests minimal (health, load, basic flow); full integration tests can be future stories
- **Docker in CI:** GitHub Actions ubuntu-latest runner has Docker pre-installed; use `docker-compose` directly
- **Timeouts:** Conservative estimates; monitor actual runs and adjust if needed
- **Coverage thresholds:** Start at 70%; raise to 80% once established
- **Performance:** Parallel jobs save time; E2E runs last (must wait for lint/test to pass)

### Project Structure Notes

- CI workflow: `.github/workflows/ci.yml`
- Gitleaks config: `.gitleaks.toml` (root)
- E2E tests: `tests/e2e/` (new) or `apps/web/tests/e2e/`
- Playwright config: `playwright.config.ts` (root or apps/web)
- Coverage: `apps/api/coverage/`, `apps/web/coverage/`
- Docker: `docker-compose.yml` (root)

### References

- docs/validation-report-architecture.md: CI pipelines gap
- docs/test-design.md: test strategy overview
- `.github/workflows/ci.yml`: existing workflow
- GitHub Actions docs: https://docs.github.com/en/actions

## Dev Agent Record

### Context Reference

- docs/sprint-artifacts/story-foundation-7.context.xml

### Agent Model Used

Claude Sonnet 4.5

### Completion Notes

- Drafted comprehensive Story 1.7 (CI Pipeline) foundation file
- Detailed acceptance criteria for linting, testing, secrets scanning, E2E smoke tests
- Mapped to specific GitHub Actions, Docker setup, and branch protection configuration
- Includes performance optimization strategies and README documentation requirements
