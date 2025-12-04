# Story 2.1: Bot Creation & Configuration

**Epic:** 2. Bot & Knowledge Management  
**Status:** ready-for-dev  
**Assigned to:** null  
**Blocked by:** 1-4-user-login-session-management

## Story

As a User,  
I want to create and configure multiple bots within my organization,  
so that I can separate knowledge bases by department or use case.

## Acceptance Criteria

### Bot Creation

-   [ ] User can navigate to Bots page from dashboard
-   [ ] User can click "Create Bot" button
-   [ ] Create Bot form displays with fields:
    -   Name (required, 2-50 chars, unique per organization)
    -   Description (optional, max 500 chars)
    -   Confidence threshold slider (0-100%, default 80%)
-   [ ] Form validates in real-time:
    -   Name: min 2 chars, max 50 chars
    -   Unique constraint checked live
    -   Description: max 500 chars
    -   Confidence threshold: numeric 0-100
-   [ ] When submitting valid form:
    -   New bot record is created in database with status "Empty"
    -   Bot is assigned to current tenant
    -   User is redirected to bot's Knowledge Base page
    -   Bot appears immediately in bot list
-   [ ] Success toast: "Bot created: [Bot Name]"
-   [ ] User sees empty state: "No documents uploaded. Upload your first document to get started."

### Bot List Display

-   [ ] User can view all bots they own in their organization
-   [ ] Bot list displays each bot with:
    -   Bot name (clickable to navigate to bot)
    -   Description preview (truncated)
    -   Document count
    -   Last updated date
    -   Confidence threshold value
    -   Actions button (Settings, Duplicate, Delete)
-   [ ] Bot list supports pagination (20 per page)
-   [ ] Bots are sortable by: name, created date, last updated
-   [ ] User can search bots by name (case-insensitive)

### Bot Settings

-   [ ] User can click "Settings" on any bot
-   [ ] Settings modal/page displays:
    -   Name (editable)
    -   Description (editable, max 500 chars)
    -   Confidence threshold (slider 0-100%)
    -   Bot ID (read-only, copyable)
    -   Created date (read-only)
-   [ ] User can edit name and description
-   [ ] Name must remain unique within organization (live validation)
-   [ ] User can adjust confidence threshold
-   [ ] Changes are saved immediately on field blur or button click
-   [ ] User sees success toast: "Settings updated"
-   [ ] Validation errors display inline

### Bot Limits & Constraints

-   [ ] Organization's bot limit is enforced per subscription tier
-   [ ] When user hits bot limit, "Create Bot" button is disabled
-   [ ] Tooltip shows: "You've reached your bot limit. Upgrade to create more."
-   [ ] Free tier: 5 bots max
-   [ ] Pro tier: 25 bots max
-   [ ] Enterprise: unlimited

### Error Handling

-   [ ] If bot name not unique: "Bot name already exists in your organization"
-   [ ] If invalid input: specific field validation message
-   [ ] If submission fails: "Failed to create bot. Please try again."
-   [ ] If reached bot limit: "You've reached your bot limit. Upgrade to create more."

## Tasks / Subtasks

### 1) Backend - Bot Creation API

-   [ ] Create POST `/api/v1/bots` endpoint
    -   Accept: name (required), description (optional), confidence_threshold (default 80)
    -   Validate: name length, uniqueness within tenant, threshold range 0-100
    -   Return: bot object with id, name, description, confidence_threshold, status, created_at
    -   Enforce: tenant isolation (RLS), authenticated user
    -   Audit: log bot creation
-   [ ] Create database migration for `bots` table schema:
    -   id (UUID primary key)
    -   tenant_id (UUID, foreign key, indexed)
    -   name (VARCHAR 2-50, not null)
    -   description (VARCHAR max 500, nullable)
    -   confidence_threshold (INT 0-100, default 80)
    -   status (ENUM: Empty, Processing, Ready, default Empty)
    -   created_at (TIMESTAMP, default now)
    -   updated_at (TIMESTAMP, default now)
    -   created_by (UUID, foreign key to users)
-   [ ] Add unique constraint: (tenant_id, name)
-   [ ] Add RLS policy: `tenant_id = current_setting('app.current_tenant_id')::uuid`
-   [ ] Add indexes: (tenant_id), (tenant_id, created_at)

### 2) Backend - Bot Settings API

-   [ ] Create GET `/api/v1/bots/{bot_id}` endpoint
    -   Return: complete bot object
    -   Enforce: RLS (bot belongs to current tenant)
-   [ ] Create PATCH `/api/v1/bots/{bot_id}` endpoint
    -   Accept: name (optional), description (optional), confidence_threshold (optional)
    -   Validate: name uniqueness (within tenant), threshold range
    -   Return: updated bot object
    -   Audit: log settings changes
-   [ ] Create GET `/api/v1/bots` endpoint (list bots)
    -   Query params: limit (default 20), offset, sort_by (name/created_at), search (name)
    -   Return: paginated list with total_count, bots array
    -   Enforce: RLS (only current tenant's bots)

### 3) Backend - Subscription Tier Enforcement

-   [ ] Add `subscription_tier` column to `tenants` table (free/pro/enterprise, default free)
-   [ ] Define tier limits:
    -   free: 5 bots
    -   pro: 25 bots
    -   enterprise: unlimited
-   [ ] In POST `/api/v1/bots`, check current bot count vs limit before creation
-   [ ] Return 402 Limit Exceeded if at limit: `{"error": "Bot limit reached", "limit": 5, "current": 5}`

### 4) Frontend - Bot List Page Component

-   [ ] Create `src/pages/bots/index.tsx` or `src/app/(dashboard)/bots/page.tsx`
-   [ ] Components:
    -   BotListHeader: title, "Create Bot" button, search field
    -   BotCard: bot name, description, doc count, confidence threshold, actions menu
    -   BotGrid or BotTable: paginated list of bot cards/rows
    -   EmptyState: show when no bots exist
    -   LoadingState: skeleton loaders while fetching
-   [ ] Features:
    -   Fetch bots on page load via GET `/api/v1/bots?limit=20&offset=0`
    -   Real-time search with debounce (300ms)
    -   Pagination: next/prev buttons or infinite scroll
    -   Sort options: name, created date
    -   Refresh button or auto-refresh on timer
-   [ ] Error handling: display error banner if fetch fails
-   [ ] Loading state: show spinners/skeletons
-   [ ] Responsive: mobile-friendly grid layout

### 5) Frontend - Create Bot Modal Component

-   [ ] Create `src/components/CreateBotModal.tsx`
-   [ ] Form fields:
    -   Name input (text, required, 2-50 chars)
    -   Description textarea (optional, max 500 chars, char counter)
    -   Confidence threshold slider (0-100%, display value)
-   [ ] Validation:
    -   Real-time feedback on name length
    -   Live check for name uniqueness (debounced API call)
    -   Threshold value range validation
-   [ ] Submit button disabled until valid
-   [ ] Loading state during submission
-   [ ] Error display: inline field errors and general errors
-   [ ] On success: close modal, add new bot to list, show success toast
-   [ ] Reusable: can be triggered from multiple contexts (button, menu item)

### 6) Frontend - Bot Settings Modal Component

-   [ ] Create `src/components/BotSettingsModal.tsx`
-   [ ] Load bot details on mount via GET `/api/v1/bots/{bot_id}`
-   [ ] Display all fields (name, description, threshold, id, created_at)
-   [ ] Allow editing: name, description, confidence_threshold
-   [ ] Field validation: same as create (live)
-   [ ] Save button triggers PATCH `/api/v1/bots/{bot_id}`
-   [ ] Optimistic updates: update UI immediately, handle server response
-   [ ] Show loading indicator on save
-   [ ] Error handling: display server errors inline
-   [ ] Copy bot ID to clipboard feature
-   [ ] Close on save or cancel

### 7) Frontend - State Management & API Hooks

-   [ ] Create custom hooks:
    -   `useBotsQuery()`: fetch bots list (uses React Query or SWR)
    -   `useBotQuery(botId)`: fetch single bot details
    -   `useCreateBot()`: mutation for POST /bots
    -   `useUpdateBot(botId)`: mutation for PATCH /bots/{botId}
    -   `useDeleteBot(botId)`: mutation for DELETE /bots/{botId} (for future)
-   [ ] Implement optimistic updates
-   [ ] Handle loading, error, success states
-   [ ] Pagination state management

### 8) Database Migrations

-   [ ] Alembic migration: create `bots` table
-   [ ] Alembic migration: add `subscription_tier` to `tenants` table (default 'free')
-   [ ] Alembic migration: add RLS policies to `bots` table
-   [ ] Alembic migration: add indexes and constraints
-   [ ] Ensure migrations are reversible

### 9) Testing

#### Backend Tests (Pytest)

-   [ ] Test POST `/api/v1/bots` (create bot):
    -   Valid input → bot created with correct status and tenant
    -   Invalid name (too short/long) → 400 validation error
    -   Duplicate name → 409 conflict error
    -   Unauthenticated → 401 unauthorized
    -   At bot limit → 402 limit exceeded
    -   RLS: can only create for own tenant
-   [ ] Test GET `/api/v1/bots` (list bots):
    -   Returns all bots for tenant
    -   Pagination works (limit, offset)
    -   Search filter works (case-insensitive)
    -   RLS: can only see own tenant's bots
    -   Cannot see other tenant's bots
-   [ ] Test GET `/api/v1/bots/{bot_id}`:
    -   Returns correct bot details
    -   RLS: forbidden if bot not in tenant
-   [ ] Test PATCH `/api/v1/bots/{bot_id}` (update):
    -   Update name: succeeds and validates uniqueness
    -   Update description: truncated if too long
    -   Update threshold: enforces 0-100 range
    -   RLS: cannot update other tenant's bot

#### Frontend Tests (Vitest/React Testing Library)

-   [ ] Test BotListPage:
    -   Render page with bot list
    -   Mock API call and verify bots displayed
    -   Search input filters bots
    -   Pagination buttons work
    -   "Create Bot" button opens modal
    -   Loading state displays
    -   Error state displays with retry
-   [ ] Test CreateBotModal:
    -   Form renders with all fields
    -   Name validation shows errors
    -   Uniqueness check works (mock debounce)
    -   Threshold slider updates value
    -   Submit button disabled until valid
    -   Successful submit closes modal, adds to list
    -   Error submit shows error message
-   [ ] Test BotSettingsModal:
    -   Load and display bot details
    -   Edit fields and submit
    -   Success toast appears
    -   Error handling works
    -   Copy bot ID to clipboard

#### Integration Test (Playwright E2E)

-   [ ] User logs in
-   [ ] Navigates to Bots page
-   [ ] Clicks "Create Bot"
-   [ ] Fills form: name="HR Bot", description="Internal HR queries", threshold=75
-   [ ] Submits form
-   [ ] Bot appears in list
-   [ ] Clicks bot to open settings
-   [ ] Updates name to "HR Bot v2"
-   [ ] Saves settings
-   [ ] Bot name updated in list
-   [ ] Tests bot limit enforcement (create 5 bots, 6th fails on free tier)

### 10) Documentation

-   [ ] Update README.md: document bot management feature
-   [ ] Document API endpoints: POST/GET/PATCH /bots
-   [ ] Add database schema diagram (bots table)
-   [ ] API examples: create bot curl/code snippets
-   [ ] Frontend architecture notes: component hierarchy, state flow

## Dev Notes

-   Bot status field will expand in future stories (when documents uploaded, status → Processing/Ready)
-   Confidence threshold interpretation:
    -   > = threshold: auto-respond (if enabled)
    -   < threshold: route to HITL review queue
    -   Can be adjusted per bot for different risk tolerances
-   Subscription tier enforcement is basic; future work: upgrade flow, metered pricing
-   Bot ID is immutable; useful for API clients accessing specific bot

### Project Structure Notes

**Backend:**

-   Models: `apps/api/app/models/bot.py` (SQLAlchemy Bot model)
-   Routes: `apps/api/app/api/routes/bots.py` (bot endpoints)
-   Schemas: `apps/api/app/schemas/bot.py` (Pydantic request/response schemas)
-   Database: `apps/api/alembic/versions/` (migration files)
-   Services: `apps/api/app/services/bot_service.py` (business logic, subscription checks)

**Frontend:**

-   Pages: `apps/web/src/app/(dashboard)/bots/page.tsx` (bot list page)
-   Components: `apps/web/src/components/BotCard.tsx`, `CreateBotModal.tsx`, `BotSettingsModal.tsx`
-   Hooks: `apps/web/src/hooks/useBotsQuery.ts`, `useCreateBot.ts`, `useUpdateBot.ts`
-   API client: `apps/web/src/lib/api/bots.ts` (API calls)
-   Types: `apps/web/src/types/bot.ts` (TypeScript interfaces)

**Database:**

-   Migration: `apps/api/alembic/versions/001_create_bots_table.py`

### References

-   [Source: docs/epics.md#Story-2.1-Bot-Creation--Configuration]
-   [Source: docs/tech-spec.md#Implementation-Stack] - Tech stack confirms FastAPI + Next.js
-   [Source: docs/architecture.md#Multi-tenancy-enforcement] - RLS policy patterns
-   [Source: docs/architecture.md#Recommended-Tech-Stack] - Database: PostgreSQL + pgvector, includes subscription tiers context
-   Functional Requirements: FR7 (create bots), FR8 (configure settings), FR9 (confidence threshold)

## Dev Agent Record

### Context Reference

-   docs/sprint-artifacts/story-2-1.context.xml

### Agent Model Used

Claude Haiku 4.5

### Completion Notes List

-   Drafted comprehensive Story 2.1 with acceptance criteria covering bot creation, list display, settings, and limits
-   Mapped all ACs to specific backend endpoints, database schema, and frontend components
-   Included subscription tier enforcement (free: 5, pro: 25, enterprise: unlimited)
-   Full test coverage across backend, frontend, and E2E
-   Database migration included with RLS policies and indexing

### Debug Log References

None

### File List

<!-- Will be updated by dev agent during implementation -->

**NEW (to be created):**

-   `apps/api/app/models/bot.py` - SQLAlchemy Bot model
-   `apps/api/app/api/routes/bots.py` - FastAPI bot endpoints
-   `apps/api/app/schemas/bot.py` - Pydantic schemas
-   `apps/api/app/services/bot_service.py` - Bot business logic
-   `apps/api/alembic/versions/XXX_create_bots_table.py` - Database migration
-   `apps/web/src/app/(dashboard)/bots/page.tsx` - Bot list page
-   `apps/web/src/components/BotCard.tsx` - Bot card component
-   `apps/web/src/components/CreateBotModal.tsx` - Create bot form modal
-   `apps/web/src/components/BotSettingsModal.tsx` - Bot settings form modal
-   `apps/web/src/hooks/useBotsQuery.ts` - Custom hook for bots list
-   `apps/web/src/hooks/useCreateBot.ts` - Custom hook for bot creation
-   `apps/web/src/hooks/useUpdateBot.ts` - Custom hook for bot updates
-   `apps/web/src/lib/api/bots.ts` - API client functions
-   `apps/web/src/types/bot.ts` - TypeScript bot types
-   `apps/api/tests/test_bots.py` - Pytest test suite
-   `apps/web/__tests__/BotListPage.test.tsx` - React component tests

**MODIFIED:**

-   `apps/api/alembic/versions/` - Add subscription_tier to tenants migration
-   `apps/web/src/app/(dashboard)/layout.tsx` - Add Bots navigation link
-   `README.md` - Add bot management section

### Learnings from Previous Story

**From Story 1-4-user-login-session-management (Status: done)**

-   **New Service Created**: `AuthService` base class with JWT token validation and refresh token handling - leverage this for bot API authentication
-   **Architectural Pattern**: JWT tokens include tenant_id in payload - confirm current tenant context available via `get_current_tenant()` dependency
-   **Session Management**: Refresh tokens invalidated on logout - apply same pattern for session-based user tracking in bot operations
-   **Testing Setup**: Auth test patterns established with mocked JWT tokens - reuse this pattern for bot endpoint tests
-   **RLS Implementation**: Row-level security enforced via PostgreSQL `current_setting('app.current_tenant_id')` - apply identically to bots table
-   **Files Created**: `apps/api/app/core/security.py` contains JWT utilities - import from here, don't recreate

[Source: docs/sprint-artifacts/story-1-4-user-login-session-management.md#Dev-Agent-Record]

## Change Log

-   2025-12-04: Initial draft created by Dario (SM)
    -   Comprehensive acceptance criteria based on epics Story 2.1
    -   Full task breakdown covering backend API, frontend UI, database, testing
    -   Subscription tier enforcement integrated
    -   RLS policies for multi-tenant isolation
    -   Previous story learnings incorporated (JWT auth, tenant context, RLS patterns)
