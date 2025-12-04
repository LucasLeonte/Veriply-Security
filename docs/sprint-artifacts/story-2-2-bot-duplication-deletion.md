# Story 2.2: Bot Duplication & Deletion

**Epic:** 2. Bot & Knowledge Management  
**Status:** drafted  
**Assigned to:** Lucas  
**Blocked by:** 2-1-bot-creation-configuration

## Story

As a User,  
I want to duplicate or delete bots,  
so that I can quickly create similar bots or clean up unused ones.

## Acceptance Criteria

### Bot Duplication

-   [ ] User can click "Duplicate" button on any bot from bot list or bot settings
-   [ ] Duplicate confirmation modal displays showing:
    -   Original bot name
    -   New bot name (default: "[Original Name] (Copy)")
    -   Confirmation message: "This will create a new bot with the same settings. Documents will NOT be copied."
-   [ ] User can edit the new bot name before confirming
-   [ ] When user confirms duplication:
    -   New bot is created with status "Empty"
    -   New bot inherits: description, confidence_threshold
    -   New bot does NOT inherit: documents, embeddings, chat history
    -   New bot gets unique bot_id
    -   New bot name is "[Original Name] (Copy)" or user-provided name
-   [ ] Name uniqueness validation applies (within tenant)
-   [ ] Success toast displays: "Bot duplicated: [New Bot Name]"
-   [ ] User is redirected to new bot's page or bot list updates with new bot
-   [ ] Original bot remains unchanged

### Bot Deletion

-   [ ] User can click "Delete" button on any bot from bot list or bot settings
-   [ ] Deletion warning modal displays:
    -   Bot name
    -   Warning message: "This will permanently delete the bot and all its documents. This cannot be undone."
    -   Document count (if any)
    -   Confirmation input: "Type the bot name to confirm"
-   [ ] User must type exact bot name (case-sensitive) to enable delete button
-   [ ] Delete button is disabled until name matches exactly
-   [ ] When user confirms deletion:
    -   Bot record is deleted from database
    -   All associated documents are deleted from storage
    -   All associated embeddings are deleted from vector store
    -   All associated chat history is deleted
    -   All associated chunks are deleted
-   [ ] For bots with large knowledge bases (>100 documents):
    -   Deletion runs as background job
    -   Progress indicator shows deletion status
    -   User sees toast: "Deletion in progress. This may take a few minutes."
    -   User can navigate away; deletion continues in background
-   [ ] For small bots (≤100 documents):
    -   Deletion completes immediately
    -   Success toast: "Bot deleted: [Bot Name]"
-   [ ] Bot is removed from bot list immediately after deletion starts
-   [ ] User is redirected to bot list page after deletion

### Error Handling

-   [ ] If duplication fails: "Failed to duplicate bot. Please try again."
-   [ ] If deletion fails: "Failed to delete bot. Please try again."
-   [ ] If user tries to delete a bot that doesn't exist: "Bot not found"
-   [ ] If user tries to delete another tenant's bot: 403 Forbidden
-   [ ] If background deletion job fails: user receives notification with retry option

## Tasks / Subtasks

### 1) Backend - Bot Duplication API

-   [ ] Create POST `/api/v1/bots/{bot_id}/duplicate` endpoint
    -   Accept: optional `name` parameter (new bot name)
    -   Validate: user owns the bot (RLS), name uniqueness within tenant
    -   Logic:
        -   Fetch source bot details
        -   Create new bot with: name="[source.name] (Copy)" or provided name, description=source.description, confidence_threshold=source.confidence_threshold, status="Empty"
        -   Assign to same tenant, created_by current user
    -   Return: new bot object with all details
    -   Audit: log bot duplication with source_bot_id and new_bot_id
-   [ ] Ensure RLS policies apply (user can only duplicate own tenant's bots)
-   [ ] Add test coverage for duplication logic

### 2) Backend - Bot Deletion API

-   [ ] Create DELETE `/api/v1/bots/{bot_id}` endpoint
    -   Validate: user owns the bot (RLS)
    -   Logic:
        -   Check document count for bot
        -   If >100 documents: enqueue background deletion job, return 202 Accepted
        -   If ≤100 documents: execute synchronous deletion, return 204 No Content
    -   Synchronous deletion:
        -   Delete bot record (cascade will handle foreign keys)
        -   Delete all documents from storage (S3/MinIO)
        -   Delete all embeddings from pgvector
        -   Delete all chunks
        -   Delete all chat history
    -   Background deletion:
        -   Create deletion task in Celery/Redis queue
        -   Task deletes in batches: documents → storage → embeddings → chunks → chat history → bot record
        -   Task updates deletion progress in database or cache
    -   Audit: log bot deletion with timestamp and user
-   [ ] Add database CASCADE constraints:
    -   documents.bot_id → ON DELETE CASCADE
    -   chunks.document_id → ON DELETE CASCADE
    -   embeddings.chunk_id → ON DELETE CASCADE
    -   chat_sessions.bot_id → ON DELETE CASCADE
-   [ ] Create background job service `BotDeletionService`:
    -   Method: `delete_bot_async(bot_id, tenant_id)`
    -   Batch processing for large datasets
    -   Error handling and retry logic
    -   Progress tracking (optional for MVP)
-   [ ] Add test coverage for both sync and async deletion paths

### 3) Backend - Deletion Progress API (Optional for MVP)

-   [ ] Create GET `/api/v1/bots/{bot_id}/deletion-status` endpoint
    -   Return: status (pending/in-progress/completed/failed), progress percentage, estimated time remaining
    -   Use Redis or database table to track deletion jobs
-   [ ] Implement polling or SSE for real-time progress updates

### 4) Frontend - Bot Duplication Modal Component

-   [ ] Create `src/components/DuplicateBotModal.tsx`
-   [ ] Form fields:
    -   Original bot name (read-only, displayed)
    -   New bot name input (editable, default: "[Original] (Copy)")
    -   Warning message about documents not being copied
-   [ ] Validation:
    -   Real-time name length validation (2-50 chars)
    -   Live uniqueness check (debounced)
-   [ ] Submit button disabled until valid
-   [ ] On success: close modal, refresh bot list, show success toast
-   [ ] Error handling: display inline errors

### 5) Frontend - Bot Deletion Modal Component

-   [ ] Create `src/components/DeleteBotModal.tsx`
-   [ ] Display:
    -   Bot name (bold, prominent)
    -   Warning message with document count
    -   Confirmation input field: "Type the bot name to confirm"
    -   Delete button (red, danger style)
-   [ ] Validation:
    -   Enable delete button only when typed name matches exactly (case-sensitive)
-   [ ] Submit logic:
    -   Call DELETE `/api/v1/bots/{bot_id}`
    -   Handle 202 (async) vs 204 (sync) responses
    -   If async: show progress toast, optionally poll for status
    -   If sync: show success toast immediately
-   [ ] Remove bot from local state/list immediately
-   [ ] Error handling: display error message, allow retry

### 6) Frontend - Update BotCard Actions Menu

-   [ ] Add "Duplicate" action to BotCard dropdown menu
    -   Opens DuplicateBotModal with bot details
-   [ ] Add "Delete" action to BotCard dropdown menu
    -   Opens DeleteBotModal with bot details
-   [ ] Ensure actions are only available for bots user owns

### 7) Frontend - State Management & API Hooks

-   [ ] Create custom hooks:
    -   `useDuplicateBot(botId)`: mutation for POST /bots/{botId}/duplicate
    -   `useDeleteBot(botId)`: mutation for DELETE /bots/{botId}
    -   `useDeletionStatus(botId)`: query for GET /bots/{botId}/deletion-status (optional)
-   [ ] Optimistic updates: remove bot from list immediately on delete
-   [ ] Handle async deletion: show progress or polling state
-   [ ] Refresh bot list after successful duplication

### 8) Database Schema Updates

-   [ ] Verify CASCADE constraints exist on:
    -   documents → bot_id
    -   chunks → document_id
    -   embeddings → chunk_id
    -   chat_sessions → bot_id
-   [ ] Add migration if missing cascade constraints
-   [ ] Test cascade behavior in development

### 9) Background Job Infrastructure

-   [ ] Ensure Celery/Redis queue is configured
-   [ ] Create `tasks/bot_deletion.py` with async deletion task
-   [ ] Add retry logic (max 3 retries)
-   [ ] Add error logging and alerting
-   [ ] Test async task execution locally

### 10) Testing

#### Backend Tests (Pytest)

-   [ ] Test POST `/api/v1/bots/{bot_id}/duplicate`:
    -   Valid duplication → new bot created with correct attributes
    -   Default name "[Original] (Copy)" applied
    -   Custom name provided → used instead
    -   Duplicate name conflict → 409 error
    -   RLS: cannot duplicate other tenant's bot → 403
    -   Source bot not found → 404
-   [ ] Test DELETE `/api/v1/bots/{bot_id}`:
    -   Small bot (≤100 docs) → synchronous deletion, 204 response
    -   Large bot (>100 docs) → async deletion, 202 response
    -   Bot with documents → all documents, chunks, embeddings deleted
    -   Bot with chat history → all chat sessions deleted
    -   RLS: cannot delete other tenant's bot → 403
    -   Bot not found → 404
-   [ ] Test cascade deletion:
    -   Verify documents deleted when bot deleted
    -   Verify chunks deleted when document deleted
    -   Verify embeddings deleted when chunk deleted

#### Frontend Tests (Vitest/React Testing Library)

-   [ ] Test DuplicateBotModal:
    -   Render modal with bot details
    -   Default name includes "(Copy)"
    -   Name validation works
    -   Submit disabled until valid
    -   Successful duplication closes modal and updates list
-   [ ] Test DeleteBotModal:
    -   Render modal with warning
    -   Delete button disabled until name typed correctly
    -   Case-sensitive name matching works
    -   Successful deletion removes bot from list
    -   Async deletion shows progress indicator

#### Integration Test (Playwright E2E)

-   [ ] User logs in
-   [ ] Navigates to bot list
-   [ ] Clicks "Duplicate" on a bot
-   [ ] Edits new bot name
-   [ ] Confirms duplication
-   [ ] New bot appears in list with correct name and settings
-   [ ] Clicks "Delete" on a bot
-   [ ] Types bot name to confirm
-   [ ] Confirms deletion
-   [ ] Bot is removed from list
-   [ ] Navigates to deleted bot's page → 404 or redirects to list

### 11) Documentation

-   [ ] Update API documentation: POST /bots/{id}/duplicate, DELETE /bots/{id}
-   [ ] Document cascade deletion behavior
-   [ ] Add examples for duplication and deletion
-   [ ] Update user guide: how to duplicate/delete bots

## Dev Notes

### Cascade Deletion Strategy

-   Use database CASCADE constraints for data integrity
-   Foreign key relationships:
    -   `documents.bot_id` → `bots.id` ON DELETE CASCADE
    -   `chunks.document_id` → `documents.id` ON DELETE CASCADE
    -   `embeddings.chunk_id` → `chunks.id` ON DELETE CASCADE
    -   `chat_sessions.bot_id` → `bots.id` ON DELETE CASCADE
-   This ensures automatic cleanup when bot is deleted
-   Background job handles object storage cleanup (S3/MinIO files)

### Async Deletion Threshold

-   100 documents chosen as threshold for async vs sync deletion
-   Rationale:
    -   Small bots: instant feedback better UX
    -   Large bots: prevent API timeout, allow user to continue working
-   Threshold configurable via environment variable: `BOT_DELETION_ASYNC_THRESHOLD`

### Duplication Scope

-   **Copied:** name (with suffix), description, confidence_threshold, tenant_id
-   **NOT copied:** documents, embeddings, chunks, chat_history, bot_id
-   Rationale: Knowledge base and history are specific to original bot context; user likely wants fresh KB for new use case

### Project Structure Notes

**Backend:**

-   Routes: `apps/api/app/api/routes/bots.py` (add duplicate & delete endpoints)
-   Services: `apps/api/app/services/bot_service.py` (add duplication and deletion logic)
-   Tasks: `apps/api/app/tasks/bot_deletion.py` (async deletion worker)
-   Schemas: `apps/api/app/schemas/bot.py` (add DuplicateBotRequest if needed)
-   Tests: `apps/api/tests/test_bots.py` (add duplication & deletion tests)

**Frontend:**

-   Components: `apps/web/src/components/DuplicateBotModal.tsx`, `DeleteBotModal.tsx`
-   Hooks: `apps/web/src/hooks/useBotsQuery.ts` (add useDuplicateBot, useDeleteBot)
-   Update: `apps/web/src/components/BotCard.tsx` (add Duplicate/Delete actions to menu)

**Database:**

-   Migration: `apps/api/alembic/versions/XXX_add_cascade_constraints.py` (if not present)

### References

-   [Source: docs/epics.md#Story-2.2-Bot-Duplication--Deletion]
-   [Source: docs/architecture.md#Multi-tenancy-enforcement] - RLS policy patterns
-   [Source: docs/tech-spec.md#Ingestion-Pipeline] - Background job infrastructure (Celery/Redis)
-   Functional Requirements: FR10 (bot deletion), FR11 (bot duplication), FR12 (bot isolation)

### Learnings from Previous Story

**From Story 2-1-bot-creation-configuration (Status: done)**

-   **Bot Model & Schema**: `apps/api/app/models/bot.py` contains the Bot SQLAlchemy model with fields: id, tenant_id, name, description, confidence_threshold, status, created_at, updated_at, created_by
-   **Bot Service**: `apps/api/app/services/bot_service.py` contains business logic for bot operations and subscription limit checks - extend this service with duplication and deletion methods
-   **Bot Routes**: `apps/api/app/api/routes/bots.py` contains FastAPI bot endpoints (GET, POST, PATCH) - add DELETE and POST /duplicate here
-   **RLS Enforcement**: All bot queries enforce tenant_id filtering via RLS policies - ensure duplication and deletion respect same patterns
-   **API Hooks**: Frontend uses `useBotsQuery`, `useCreateBot`, `useUpdateBot` from `apps/web/src/hooks/useBotsQuery.ts` - add `useDuplicateBot` and `useDeleteBot` following same patterns
-   **BotCard Component**: `apps/web/src/components/BotCard.tsx` displays bot with actions menu - extend menu with Duplicate and Delete options
-   **Subscription Tier**: Tenant model includes subscription_tier (FREE/PRO/ENTERPRISE) - duplication should respect bot limits same as creation
-   **Testing Patterns**: `apps/api/tests/test_bots.py` has 30+ pytest tests covering CRUD operations - follow same structure for duplication/deletion tests
-   **Unique Constraint**: (tenant_id, name) unique constraint enforced - duplication must generate unique names
-   **Database Migration**: Alembic migrations pending but schema defined - add CASCADE constraints in new migration

[Source: docs/sprint-artifacts/story-2-1-bot-creation-configuration.md#Dev-Agent-Record]

## Dev Agent Record

### Context Reference

<!-- Path(s) to story context XML will be added here by context workflow -->

### Agent Model Used

Claude Sonnet 4.5

### Completion Notes List

-   Story 2.2 drafted with comprehensive acceptance criteria for bot duplication and deletion
-   Cascade deletion strategy defined with database constraints
-   Async deletion threshold (100 documents) for UX optimization
-   Clear scope: duplication copies settings only, not knowledge base
-   All tasks mapped to existing project structure from Story 2.1
-   Test coverage planned across backend, frontend, and E2E
-   Previous story learnings incorporated for consistency

### Debug Log References

### File List

<!-- Will be updated by dev agent during implementation -->

## Change Log

-   2025-12-04: Initial draft created by SM (following create-story workflow)
    -   Based on Epic 2 Story 2.2 from docs/epics.md
    -   Comprehensive acceptance criteria for duplication and deletion flows
    -   Async deletion strategy for large bots (>100 docs)
    -   Cascade deletion using database constraints
    -   Previous story learnings integrated (Bot model, service, routes, hooks, components)
    -   Full test coverage planned
