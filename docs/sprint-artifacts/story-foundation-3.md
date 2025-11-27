# Story 1.3: Authentication & User Session

**Epic:** 1. Foundation & App Shell
**Status:** Ready for Development
**Context:** [Tech Spec](../tech-spec.md)

## Description
Implement secure authentication using NextAuth.js (Frontend) and JWT validation (Backend).

## Tasks
1.  **Frontend Auth (NextAuth):**
    *   Configure `CredentialsProvider`.
    *   Create Login Page (`app/login/page.tsx`) with "Deep Ocean" theme.
    *   Store JWT in HTTP-only cookie.

2.  **Backend Auth (FastAPI):**
    *   Create `/api/v1/auth/login` endpoint to validate credentials and issue token.
    *   Create `get_current_user` dependency to validate JWT and extract `tenant_id`.

3.  **Middleware:**
    *   Protect `/dashboard` routes in Next.js.
    *   Protect API routes in FastAPI.

## Acceptance Criteria
*   [ ] User can log in with email/password.
*   [ ] Invalid credentials return 401.
*   [ ] Protected routes redirect to `/login` if unauthenticated.
*   [ ] Backend correctly extracts `tenant_id` from token for RLS.

## Technical Notes
*   **Token Payload:** `{ sub: user_id, tenant_id: uuid, role: string }`.
*   **Secret:** Ensure `NEXTAUTH_SECRET` matches the backend JWT secret.
