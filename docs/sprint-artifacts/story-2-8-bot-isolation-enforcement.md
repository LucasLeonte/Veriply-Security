# Story 2.8: Bot Isolation Enforcement

**Epic:** 2. Bot & Knowledge Management  
**Status:** drafted  
**Assigned to:** null  
**Blocked by:** 2-1-bot-creation-configuration

## Story

As a System,  
I want to ensure documents and queries are scoped to their assigned bot,  
so that HR Bot doesn't access Sales Bot's knowledge.

## Acceptance Criteria

### Document Isolation

-   [ ] Documents are always associated with a specific bot
-   [ ] When querying documents, the system filters by bot_id
-   [ ] A user viewing Bot A's Knowledge Base page only sees documents uploaded to Bot A
-   [ ] Bot B's documents are never included in Bot A's list
-   [ ] Query `SELECT * FROM documents WHERE bot_id = ?` is enforced everywhere

### Query/Search Isolation

-   [ ] When a user performs a semantic search via Bot A:
    -   Only Bot A's chunks are searched (via `WHERE bot_id = bot_a_id` in pgvector search)
    -   Bot B's embeddings are never retrieved
-   [ ] When a user performs a search via Bot B:
    -   Only Bot B's chunks are searched
    -   Bot A's embeddings are never retrieved
-   [ ] Cross-bot queries return 0 results, never mixed results

### Chat History Isolation

-   [ ] Each bot maintains its own chat history
-   [ ] User cannot see Chat A's conversation history in Chat B
-   [ ] Query `SELECT * FROM chat_history WHERE bot_id = ?` is enforced
-   [ ] Conversations are never mixed between bots

### API Security

-   [ ] All API endpoints that accept `bot_id` parameter validate:
    -   Bot ID is valid UUID format
    -   Bot belongs to the authenticated user's tenant
    -   Authenticated user has permission to access this bot
-   [ ] Direct API call with wrong bot_id is rejected:
    -   Request: `GET /api/v1/bots/bot_b_id/documents` (user owns bot_a)
    -   Response: 403 Forbidden
    -   Message: "You do not have permission to access this bot"
-   [ ] SQL injection prevention: all queries use parameterized statements

### Vector Store Isolation

-   [ ] Vector search includes bot_id in WHERE clause:
    -   `SELECT embedding FROM chunks WHERE bot_id = ? AND similarity > threshold`
-   [ ] Embeddings are never shared across bots
-   [ ] Vector index is scoped by bot_id (if supported by pgvector)

### Row-Level Security (RLS)

-   [ ] Database RLS policies enforce bot isolation:
    -   Users can only view/modify documents for their bots
    -   RLS policy: `bot_id IN (SELECT id FROM bots WHERE tenant_id = current_user_tenant_id)`
    -   Policies applied to: documents, chunks, chat_history, embeddings tables
-   [ ] RLS policies are tested and enforced on all queries

### Audit & Logging

-   [ ] All bot access is logged (for compliance):
    -   User ID, bot ID, action (view, search, query), timestamp
    -   Useful for detecting unauthorized access attempts
-   [ ] Failed cross-bot access attempts are logged as security events
-   [ ] Audit trail shows bot isolation violations (if any)

### Error Handling

-   [ ] If user tries to access bot they don't own:
    -   Error: "You do not have permission to access this bot" (403)
    -   Action is logged as security event
-   [ ] If bot_id is not found:
    -   Error: "Bot not found" (404)
    -   User doesn't see different error for "not found" vs "not owned" (security)
-   [ ] If bot_id is invalid format:
    -   Error: "Invalid bot ID format" (400)

## Tasks / Subtasks

### 1) Backend - API Endpoint Protection

-   [ ] Add middleware/decorator for all bot-scoped endpoints:
    -   Extract bot_id from URL parameter or request body
    -   Verify bot belongs to authenticated user's tenant
    -   Return 403 if not authorized
-   [ ] Apply to endpoints:
    -   GET/POST `/api/v1/bots/:bot_id/documents`
    -   GET/POST/DELETE `/api/v1/documents/:doc_id`
    -   GET/POST `/api/v1/bots/:bot_id/search`
    -   GET/POST `/api/v1/bots/:bot_id/chat`
    -   All other bot-scoped endpoints
-   [ ] Test with bot IDs from different tenants/users

### 2) Backend - Database RLS Policies

-   [ ] Create RLS policies for `documents` table:
    -   Policy: `bot_id IN (SELECT id FROM bots WHERE tenant_id = current_user_tenant_id)`
    -   Apply to: SELECT, UPDATE, DELETE
-   [ ] Create RLS policies for `chunks` table:
    -   Policy: `document_id IN (SELECT id FROM documents WHERE bot_id IN (...))`
-   [ ] Create RLS policies for `chat_history` table:
    -   Policy: `bot_id IN (SELECT id FROM bots WHERE tenant_id = current_user_tenant_id)`
-   [ ] Enable RLS on all tables
-   [ ] Test RLS by executing queries as different users

### 3) Backend - Vector Search Isolation

-   [ ] Update all vector search queries to include bot_id filter:
    -   `SELECT * FROM chunks WHERE bot_id = ? AND embedding <-> query_vector < threshold ORDER BY ...`
-   [ ] Search for all vector search queries in codebase:
    -   `apps/api/app/services/search.py`
    -   `apps/api/app/routes/chat.py`
    -   `apps/api/app/routes/search.py`
-   [ ] Verify bot_id is passed as parameter (never hardcoded or user-provided)
-   [ ] Test search with multiple bots to ensure isolation

### 4) Backend - Chat History Isolation

-   [ ] Ensure chat history queries include bot_id:
    -   `SELECT * FROM chat_history WHERE bot_id = ? AND conversation_id = ?`
-   [ ] Verify RLS or explicit filtering on chat history endpoints
-   [ ] Test chat history retrieval across bots

### 5) Backend - Bot Ownership Validation Function

-   [ ] Create helper function: `validate_bot_access(user_id, bot_id) -> bool`
    -   Check bot belongs to user's tenant
    -   Return True if allowed, False otherwise
-   [ ] Use this function in all bot-scoped endpoints
-   [ ] Document the function for team reference

### 6) Backend - Audit Logging

-   [ ] Add logging to all bot access:
    -   Log: user_id, bot_id, action, timestamp, IP address
    -   On successful access, log at INFO level
    -   On unauthorized access, log at WARNING/SECURITY level
-   [ ] Create audit table: `bot_access_audit` (user_id, bot_id, action, timestamp, status)
-   [ ] Log to this table for compliance

### 7) Backend - Security Testing

-   [ ] Create test suite for bot isolation:
    -   Test 1: User A queries documents from Bot A (should succeed)
    -   Test 2: User A queries documents from Bot B (User B's bot) (should fail 403)
    -   Test 3: Vector search in Bot A doesn't return Bot B's results
    -   Test 4: Chat history from Bot A doesn't appear in Bot B
    -   Test 5: Direct SQL injection attempt blocked (parameterized query)
    -   Test 6: RLS policies enforced on database level
-   [ ] Run security tests in CI/CD pipeline

### 8) Frontend - Error Handling

-   [ ] If user receives 403 Forbidden response:
    -   Show error toast: "You do not have permission to access this bot"
    -   Redirect to bots list or dashboard
-   [ ] If user receives 404 Not Found response:
    -   Show generic error: "Bot not found"
-   [ ] Never expose internal error details to user

## Dev Notes

- Bot isolation is a critical security feature; test thoroughly before deployment
- RLS policies provide database-level protection; API-level validation is additional layer
- Always use parameterized queries; never concatenate user input into SQL
- Consider adding a "bot scope" context variable to all requests for consistency
- Audit logging helps detect and investigate unauthorized access attempts
- Regularly review and test isolation to catch regressions

### Project Structure Notes

- API middleware/decorators: `apps/api/app/middleware/auth.py` or `apps/api/app/dependencies.py`
- RLS policies: `apps/api/alembic/versions/` (database migrations)
- Vector search: `apps/api/app/services/search.py`
- Chat endpoints: `apps/api/app/routes/chat.py`
- Bot validation: `apps/api/app/services/bot_service.py` (new helper function)
- Audit logging: `apps/api/app/services/audit_logger.py` (new module)
- Tests: `apps/api/tests/test_bot_isolation.py` (new test file)

### References

- [Epic 2 Specification: Story 2.8](../epics.md#story-28-bot-isolation-enforcement)
- [Story 2.1: Bot Creation & Configuration](./story-2-1-bot-creation-configuration.md)
- [Architecture: Multi-Tenancy & Security](../architecture.md)
- [SECURITY-CONFIG: JWT & Authorization](../SECURITY-CONFIG-JWT.md)

## Dev Agent Record

### Context Reference

<!-- Path(s) to story context XML will be added here by context workflow -->

### Agent Model Used

Claude Haiku 4.5

### Debug Log References

### Completion Notes List

### File List
