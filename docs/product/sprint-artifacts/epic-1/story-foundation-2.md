# Story 1.2: Database Schema & Multi-Tenancy

**Epic:** 1. Foundation & App Shell
**Status:** Ready for Development
**Context:** [Tech Spec](../tech-spec.md)

## Description
Set up the PostgreSQL database with `pgvector` and implement the core multi-tenant schema using Row-Level Security (RLS).

## Tasks
1.  **Database Setup:**
    *   Ensure `pgvector` extension is enabled in migration.
    *   Configure SQLAlchemy with `asyncpg`.

2.  **Core Models (SQLAlchemy):**
    *   `Tenant` (id, name, plan).
    *   `User` (id, email, tenant_id, role).
    *   `Bot` (id, name, tenant_id, config).
    *   `Document` (id, title, tenant_id, status).

3.  **RLS Implementation:**
    *   Create a migration to enable RLS on all tables.
    *   Create a Policy: `current_setting('app.current_tenant_id') = tenant_id`.

4.  **FastAPI Dependency:**
    *   Create `get_db` dependency that sets `app.current_tenant_id` in the session based on the JWT token.

## Acceptance Criteria
*   [ ] Alembic migrations run successfully.
*   [ ] Tables exist with `tenant_id` foreign keys.
*   [ ] RLS prevents Tenant A from querying Tenant B's users (verified via test).
*   [ ] `pgvector` type is available for embeddings.

## Technical Notes
*   **RLS SQL:**
    ```sql
    CREATE POLICY tenant_isolation ON users
    USING (tenant_id = current_setting('app.current_tenant_id')::uuid);
    ```
