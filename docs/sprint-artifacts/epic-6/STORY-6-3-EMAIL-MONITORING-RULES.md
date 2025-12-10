# Story 6.3: Email Monitoring & Rules

Status: drafted

## Story

As a User,
I want to configure which emails trigger draft generation,
so that I only get AI-generated drafts for relevant messages and avoid notification overload.

## Acceptance Criteria

1. **Given** I have a connected email account (Gmail or Outlook)  
   **When** I click "Configure Monitoring"  
   **Then** I can set monitoring rules including:
   - Monitored folders/labels (e.g., Inbox, Support, Sales)
   - Keywords to include (optional, e.g., "quote", "pricing")
   - Keywords to exclude (optional, e.g., "newsletter", "unsubscribe")
   - Bot to use for draft generation
   - Enable/disable status for the rule

2. **When** a new email arrives matching my rules  
   **Then** it is queued for draft generation  
   **And** the email is not processed multiple times

3. **Given** I have configured multiple rules  
   **Then** rules are evaluated in priority order  
   **And** first matching rule wins  
   **And** I can reorder rule priority via drag-and-drop

4. **Given** I want to test my rules  
   **Then** I can use a "Test Rule" feature with sample email content  
   **And** system shows whether the sample would match the rule

5. **Given** I want to pause monitoring temporarily  
   **Then** I can pause/resume monitoring with a toggle switch  
   **And** paused rules do not process new emails  
   **And** monitoring status is clearly visible

6. **Given** system polls for new emails  
   **Then** polling frequency is every 5 minutes (configurable per user)  
   **And** polling respects API rate limits  
   **And** errors are logged and surfaced to user

## Tasks / Subtasks

- [ ] Task 1: Database schema for monitoring rules (AC: #1, #3, #5)
  - [ ] Create database migration for `email_monitoring_rules` table
  - [ ] Columns: `id`, `tenant_id`, `user_id`, `integration_id` (FK to email_integrations), `bot_id` (FK to bots), `folder_labels` (jsonb array), `include_keywords` (text array), `exclude_keywords` (text array), `priority` (integer), `is_active` (boolean), `created_at`, `updated_at`
  - [ ] Create index on `(tenant_id, integration_id, is_active, priority)`
  - [ ] Add RLS policy filtered by `tenant_id`

- [ ] Task 2: Backend rule management API (AC: #1, #3, #5)
  - [ ] POST `/api/v1/email-rules` - Create new monitoring rule
  - [ ] GET `/api/v1/email-rules` - List all rules for user
  - [ ] PUT `/api/v1/email-rules/:id` - Update rule
  - [ ] DELETE `/api/v1/email-rules/:id` - Delete rule
  - [ ] PUT `/api/v1/email-rules/reorder` - Update rule priorities
  - [ ] PUT `/api/v1/email-rules/:id/toggle` - Enable/disable rule
  - [ ] Validate bot_id belongs to user's tenant

- [ ] Task 3: Email polling worker (AC: #2, #6)
  - [ ] Create background worker: `apps/api/app/workers/email_poller.py`
  - [ ] Implement polling logic for Gmail (using Gmail API)
  - [ ] Implement polling logic for Outlook (using Microsoft Graph API)
  - [ ] Use Redis to track last processed email timestamp per integration
  - [ ] Implement rate limiting with exponential backoff
  - [ ] Schedule worker to run every 5 minutes (using APScheduler or Celery Beat)
  - [ ] Add configurable polling interval per user (stored in user preferences)

- [ ] Task 4: Rule matching engine (AC: #2, #3)
  - [ ] Implement rule evaluation function: `match_email_to_rules(email, rules)`
  - [ ] Check folder/label match (Gmail labels, Outlook folders)
  - [ ] Check keyword inclusion (case-insensitive, partial match)
  - [ ] Check keyword exclusion (case-insensitive, partial match)
  - [ ] Apply priority ordering (lowest priority number = highest priority)
  - [ ] Return first matching rule or None
  - [ ] Track processed emails in `email_processing_queue` table to prevent duplicates

- [ ] Task 5: Test rule feature (AC: #4)
  - [ ] POST `/api/v1/email-rules/:id/test` - Test rule with sample email
  - [ ] Accept email content in request body (subject, body, sender, folder)
  - [ ] Return match result: boolean + explanation of why matched/didn't match
  - [ ] Implement dry-run mode (no actual processing)

- [ ] Task 6: Frontend rule configuration UI (AC: #1, #3, #4, #5)
  - [ ] Create page: `apps/web/src/app/dashboard/email-rules/page.tsx`
  - [ ] Form to create/edit monitoring rule with fields:
    - Email account selector (dropdown of connected accounts)
    - Bot selector (dropdown of user's bots)
    - Folder/label multi-select (fetch from email provider API)
    - Include keywords input (tag-style input)
    - Exclude keywords input (tag-style input)
    - Enable/disable toggle
  - [ ] Rules list with drag-and-drop reordering (use dnd-kit)
  - [ ] "Test Rule" modal with sample email input
  - [ ] Display match result with explanation
  - [ ] Pause/resume toggle at page level
  - [ ] Show last poll time and next poll time

- [ ] Task 7: Error handling and monitoring (AC: #6)
  - [ ] Log polling errors with context (integration_id, error type)
  - [ ] Surface connection errors in UI ("Failed to poll emails. Reconnect your account.")
  - [ ] Implement retry logic with exponential backoff
  - [ ] Add metric tracking: emails polled, rules matched, errors
  - [ ] Create alert for repeated polling failures

- [ ] Task 8: Testing (All ACs)
  - [ ] Unit test rule matching engine with various scenarios
  - [ ] Unit test polling worker logic
  - [ ] Integration test rule CRUD API
  - [ ] Integration test email polling (use mock email provider)
  - [ ] Test duplicate email prevention
  - [ ] Test rule priority evaluation
  - [ ] E2E test creating rule → receiving email → draft queued

## Dev Notes

### Technical Constraints

- **Polling vs Webhooks:**
  - MVP uses polling (simpler, works with all email providers)
  - Gmail supports push notifications (Pub/Sub) - consider for v2
  - Outlook supports webhooks (Microsoft Graph subscriptions) - consider for v2

- **Rate Limits:**
  - Gmail API: 250 quota units/user/second, 1 billion/day
  - Microsoft Graph: Throttling varies by endpoint (typically 2000 requests/minute)
  - Implement exponential backoff on 429 responses

- **Deduplication Strategy:**
  - Store hash of (integration_id + email_id) in `email_processing_queue`
  - Check hash before processing to prevent duplicates
  - Clean up old hashes after 30 days

- **Performance:**
  - Batch API requests when fetching new emails
  - Use cursor-based pagination for large mailboxes
  - Cache folder/label lists (refresh every 24 hours)

### Learnings from Previous Story

**From Story 6-2: Outlook OAuth Integration**

- **Reuse Components:**
  - Gmail and Outlook API wrappers already implemented
  - `email_integrations` table has connection details
  - Frontend integration selector pattern established

- **Architectural Pattern:**
  - Rules must validate `integration_id` belongs to user's tenant
  - Apply same RLS policies for tenant isolation
  - Use existing encryption for storing sensitive rule data (if needed)

### Project Structure Notes

- **Backend:**
  - Create module: `apps/api/app/email_automation/rules.py` - Rule management logic
  - Create module: `apps/api/app/email_automation/matcher.py` - Rule matching engine
  - Create worker: `apps/api/app/workers/email_poller.py` - Background polling
  - API routes: `apps/api/app/routes/email_rules.py`
  - Database model: `apps/api/app/models/email_monitoring_rules.py`
  - Migration: `apps/api/alembic/versions/xxx_add_email_monitoring_rules.py`

- **Frontend:**
  - Create page: `apps/web/src/app/dashboard/email-rules/page.tsx`
  - Components:
    - `apps/web/src/components/email-rules/RuleForm.tsx`
    - `apps/web/src/components/email-rules/RulesList.tsx`
    - `apps/web/src/components/email-rules/TestRuleModal.tsx`
  - Reuse shadcn/ui: Form, Select, Input, Switch, DndKit for drag-and-drop

- **Worker Infrastructure:**
  - Use APScheduler or Celery Beat for scheduling
  - Redis for tracking last poll timestamps
  - Configure worker in `docker-compose.yml` or Kubernetes manifest

### Architecture Alignment

- Background worker follows async processing pattern (aligns with document processing from Epic 2)
- Rule evaluation uses priority-based matching (similar to confidence scoring in Epic 3)
- Multi-tenancy enforced via RLS (consistent with Epic 1 foundation)
- Redis for state management (aligns with HITL queue from Epic 5)

### References

- [Source: docs/epics.md - Epic 6: Email Automation, Story 6.3]
- [Source: docs/prd.md - FR46: Email monitoring rules, FR50: Configure folders]
- [Source: docs/architecture.md - Background job section]
- [Gmail API - Watch/Push Notifications](https://developers.google.com/gmail/api/guides/push)
- [Microsoft Graph - Change Notifications](https://docs.microsoft.com/en-us/graph/webhooks)

## Dev Agent Record

### Context Reference

<!-- Path(s) to story context XML will be added here by context workflow -->

### Agent Model Used

_To be filled by dev agent_

### Debug Log References

_To be filled by dev agent_

### Completion Notes List

_To be filled by dev agent_

### File List

_To be filled by dev agent_
