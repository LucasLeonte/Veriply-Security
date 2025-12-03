# Story 1.6: CI Pipeline - Lint, Tests, and Smoke E2E

**Epic:** 1. Foundation & App Shell
**Status:** Drafted
**Context:** Architecture gaps called out in docs/validation-report-architecture.md (Add CI pipelines for lint/tests (API & web) and smoke E2E)

## Story

As a developer and engineering team,
I want a robust CI pipeline that runs linting, unit tests, and smoke end-to-end tests on every PR and commit to main,
so that code quality is enforced, regressions are caught early, and deployments are reliable.

## Acceptance Criteria

- [ ] CI workflow (`.github/workflows/ci.yml`) runs on push to `main` and on all PRs.
- [ ] Linting jobs for frontend (ESLint) and backend (Ruff) pass with zero errors.
- [ ] Unit test jobs for frontend (Vitest) and backend (Pytest) pass with coverage reports.
- [ ] Smoke E2E test job spins up Docker Compose services and verifies critical paths (login, healthz, basic API call).
- [ ] Secrets scanning job (gitleaks) runs and fails the build if secrets are detected.
- [ ] All jobs run in parallel where possible; pipeline completes in <5 minutes.
- [ ] Failed CI blocks merging on GitHub (branch protection rule).
- [ ] README.md updated with CI badge and instructions for running tests locally.

## Tasks / Subtasks

1) Extend existing CI workflow
- [ ] Review current `.github/workflows/ci.yml` (already has lint-frontend, lint-backend, test-frontend, test-backend)
- [ ] Verify linting and test jobs run correctly; fix any issues
- [ ] Add coverage reporting (optional: upload to Codecov or similar)

2) Add secrets scanning job
- [ ] Install gitleaks action in CI
- [ ] Create `.gitleaks.toml` config (or use default)
- [ ] Add job to scan all commits in PR for leaked secrets
- [ ] Ensure job fails if secrets detected

3) Add smoke E2E test job
- [ ] Create job `smoke-e2e` that runs after lint/test jobs
- [ ] Spin up Docker Compose services (postgres, redis, api, web) in CI
- [ ] Use Playwright or curl-based scripts to verify:
  - API `/healthz` returns 200
  - Web frontend loads (200 status on `/`)
  - Basic login flow (optional: mock user registration and login)
- [ ] Tear down services after tests
- [ ] Store test artifacts (screenshots, logs) on failure

4) Branch protection and README
- [ ] Enable branch protection on `main`: require CI to pass before merge
- [ ] Add CI status badge to README.md
- [ ] Document how to run tests locally in README

5) Performance and optimization
- [ ] Cache dependencies (npm, pip) across jobs
- [ ] Run jobs in parallel where possible (lint/test can run concurrently)
- [ ] Optimize Docker layer caching for E2E tests

## Dev Notes

- Architecture report flags CI pipelines as a gap to close for MVP; this story addresses that gap directly.
- Existing CI workflow already covers lint and unit tests; this story extends it with secrets scanning and smoke E2E.
- Use GitHub Actions marketplace for gitleaks and Playwright setup.
- Keep E2E tests minimal (smoke only); full E2E suite can be a future story.

### Project Structure Notes

- CI workflow: `.github/workflows/ci.yml`
- Gitleaks config: `.gitleaks.toml` (root)
- E2E test scripts: `tests/e2e/` (new directory) or inline bash/curl in CI
- Coverage reports: `apps/api/coverage/`, `apps/web/coverage/`

### References

- docs/validation-report-architecture.md#Gaps-/-Actions
- .github/workflows/ci.yml (existing)
- docs/test-design.md

## Dev Agent Record

### Context Reference

- N/A (story context XML will be produced by `story-context` workflow)

### Agent Model Used

Claude Sonnet 4.5

### Debug Log References

- N/A

### Completion Notes List

- Drafted Story 1.6 with acceptance criteria and tasks

### File List

- NEW: `docs/sprint-artifacts/story-foundation-6.md`
