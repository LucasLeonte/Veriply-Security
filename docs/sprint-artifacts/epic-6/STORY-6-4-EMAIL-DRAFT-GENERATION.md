# Story 6.4: Email Draft Generation

Status: drafted

## Story

As a System,
I want to generate email draft responses based on the knowledge base,
so that users have AI-generated starting points for replies that can be reviewed before sending.

## Acceptance Criteria

1. **Given** a new email triggers a monitoring rule  
   **When** the system processes it  
   **Then** the following pipeline executes:

    - Email content is extracted (subject, body, sender, thread)
    - PII is redacted from email content
    - RAG retrieves relevant context from bot's knowledge base
    - LLM generates a draft reply
    - Draft is added to HITL queue for review

2. **Given** an email draft is generated  
   **Then** the draft includes:

    - Subject: "Re: [Original Subject]"
    - Body: AI-generated response based on context
    - Citations as internal notes (not in final email body)
    - Confidence score (0-100%)
    - Reference to original email thread

3. **Given** draft generation completes  
   **Then** generation time is less than 30 seconds  
   **And** user sees draft in HITL queue immediately

4. **Given** RAG retrieves no relevant context  
   **Then** system generates draft: "Thank you for your email. I need to review this and will get back to you shortly."  
   **And** confidence score is set to 0%  
   **And** draft is marked as "Low Context" and assigned to the requesting user for self-review (not routed to a team)

5. **Given** email processing fails  
   **Then** error is logged with email ID and error details  
   **And** user can manually retry from UI  
   **And** email is marked as "Processing Failed" in queue

6. **Given** multiple emails arrive in quick succession  
   **Then** they are processed in order (FIFO queue)  
   **And** system respects LLM rate limits  
   **And** processing does not block other system operations

## Tasks / Subtasks

-   [ ] Task 1: Email processing queue infrastructure (AC: #1, #6)

    -   [ ] Create database table: `email_processing_queue`
    -   [ ] Columns: `id`, `tenant_id`, `integration_id`, `rule_id`, `email_id` (from provider), `email_subject`, `email_body`, `sender_email`, `thread_id`, `status` (pending/processing/completed/failed), `error_message`, `created_at`, `processed_at`
    -   [ ] Create index on `(tenant_id, status, created_at)`
    -   [ ] Add RLS policy filtered by `tenant_id`
    -   [ ] Implement FIFO queue processing using Redis or database ordering

-   [ ] Task 2: Email content extraction (AC: #1)

    -   [ ] Implement Gmail email fetcher: `fetch_gmail_email(email_id, integration)`
    -   [ ] Implement Outlook email fetcher: `fetch_outlook_email(email_id, integration)`
    -   [ ] Extract structured data: subject, body (plain text), sender, thread_id
    -   [ ] Handle HTML emails (strip HTML, preserve formatting where needed)
    -   [ ] Extract email metadata: received time, importance, labels

-   [ ] Task 3: PII redaction for email content (AC: #1)

    -   [ ] Reuse PII redaction from Epic 3 (Story 3.5)
    -   [ ] Redact email addresses (except company domain)
    -   [ ] Redact phone numbers
    -   [ ] Redact credit card numbers
    -   [ ] Store redacted version for LLM, original for reference
    -   [ ] Log redaction actions for audit

-   [ ] Task 4: RAG integration for email context (AC: #1, #4)

    -   [ ] Reuse RAG pipeline from Epic 3 (Stories 3.1, 3.2)
    -   [ ] Query vector store with email content as query text
    -   [ ] Scope search to bot specified in matching rule
    -   [ ] Retrieve top 5 relevant chunks
    -   [ ] Calculate context relevance score
    -   [ ] Handle no-context scenario (relevance score < threshold)

-   [ ] Task 5: Email-specific LLM prompt template (AC: #2)

    -   [ ] Create email draft generation prompt template
    -   [ ] Include: retrieved context, original email, instructions
    -   [ ] Prompt format:

        ```
        You are a helpful email assistant. Generate a professional reply to the email below using ONLY the provided context.

        Context from knowledge base:
        {retrieved_chunks}

        Original Email:
        From: {sender}
        Subject: {subject}
        {body}

        Generate a reply that:
        - Addresses the sender's question/request
        - Uses information from the context only
        - Is professional and courteous
        - Maintains company tone
        - If context insufficient: politely say you need to review and will respond soon
        ```

    -   [ ] Configure temperature: 0.3 (slightly creative for natural tone)
    -   [ ] Add citation extraction logic for internal notes

-   [ ] Task 6: Draft creation and HITL queue integration (AC: #1, #2, #3)

    -   [ ] Create database table: `email_drafts`
    -   [ ] Columns: `id`, `tenant_id`, `queue_id` (FK to email_processing_queue), `bot_id`, `subject`, `body`, `citations` (jsonb), `confidence_score`, `original_email_id`, `thread_id`, `status` (pending_review/approved/rejected/sent), `reviewed_by`, `reviewed_at`, `created_at`
    -   [ ] Add draft to HITL queue (reuse HITL infrastructure from Epic 5)
    -   [ ] Link draft to original email for context
    -   [ ] Store confidence score and citations as metadata

-   [ ] Task 7: Worker for draft generation (AC: #6)

    -   [ ] Create background worker: `apps/api/app/workers/email_draft_generator.py`
    -   [ ] Poll `email_processing_queue` for pending items
    -   [ ] Execute pipeline: extract → redact → RAG → LLM → draft
    -   [ ] Update queue item status as processing progresses
    -   [ ] Handle errors gracefully (mark as failed, log details)
    -   [ ] Implement rate limiting for LLM calls
    -   [ ] Set processing timeout: 30 seconds per email

-   [ ] Task 8: Error handling and retry logic (AC: #5)

    -   [ ] Implement exponential backoff for transient failures
    -   [ ] Store error details in `email_processing_queue.error_message`
    -   [ ] Add manual retry endpoint: POST `/api/v1/email-queue/:id/retry`
    -   [ ] Display failed items in UI with retry button
    -   [ ] Set max retry attempts: 3

-   [ ] Task 9: Frontend - Email draft queue view (AC: #3, #5)

    -   [ ] Extend HITL queue to show email drafts (reuse from Epic 5)
    -   [ ] Display draft card with:
        -   Original email preview (sender, subject, body excerpt)
        -   Generated draft
        -   Confidence score
        -   Citations (expandable)
        -   Actions: Approve, Edit, Reject, Retry (if failed)
    -   [ ] Show processing status: "Generating draft..." loading state
    -   [ ] Filter by status: Pending, Failed, All

-   [ ] Task 10: Testing (All ACs)
    -   [ ] Unit test email extraction for Gmail
    -   [ ] Unit test email extraction for Outlook
    -   [ ] Unit test PII redaction on email content
    -   [ ] Unit test RAG retrieval with email queries
    -   [ ] Unit test prompt template rendering
    -   [ ] Integration test full pipeline: email → draft → HITL queue
    -   [ ] Test no-context scenario
    -   [ ] Test error handling and retry
    -   [ ] Performance test: 30-second SLA
    -   [ ] E2E test: trigger rule → process email → see draft in UI

## Dev Notes

### Technical Constraints

-   **Performance SLA:**

    -   Total draft generation: < 30 seconds
    -   RAG retrieval: < 3 seconds
    -   LLM generation: < 20 seconds (streamed)
    -   If timeout exceeded, mark as failed and allow retry

-   **Email Threading:**

    -   Preserve thread_id from original email
    -   Use thread_id in draft reply for proper threading
    -   Gmail: Uses thread_id from Gmail API
    -   Outlook: Uses conversationId from Graph API

-   **PII Compliance:**

    -   Redact before sending to LLM (GDPR requirement)
    -   Store both redacted and original versions
    -   Log all PII redactions for audit trail

-   **Rate Limiting:**
    -   LLM calls: Respect Ollama rate limits (or OpenAI fallback limits)
    -   Email API calls: Respect Gmail/Outlook rate limits
    -   Use queue to prevent thundering herd

### Learnings from Previous Story

**From Story 6-3: Email Monitoring & Rules**

-   **Reuse Components:**

    -   Email polling worker infrastructure
    -   Gmail and Outlook API wrappers
    -   Rule matching engine provides `bot_id` for scoping RAG

-   **Integration Points:**
    -   Email poller adds items to `email_processing_queue`
    -   Draft generator worker consumes from queue
    -   Use same Redis instance for coordination

**From Epic 3: RAG Q&A Engine**

-   **Reuse Components:**

    -   `apps/api/app/rag/vector_search.py` - Semantic search
    -   `apps/api/app/rag/context_generation.py` - Answer generation
    -   `apps/api/app/rag/citation.py` - Citation extraction
    -   `apps/api/app/rag/pii_redaction.py` - PII handling (Story 3.5)

-   **Architectural Pattern:**
    -   Same RAG pipeline, different prompt template
    -   Reuse confidence scoring logic from Story 3.4
    -   Apply bot-level isolation for vector search

### Project Structure Notes

-   **Backend:**

    -   Create module: `apps/api/app/email_automation/draft_generator.py` - Main orchestration
    -   Create module: `apps/api/app/email_automation/email_extractor.py` - Email fetching
    -   Create worker: `apps/api/app/workers/email_draft_generator.py` - Background processing
    -   Database models:
        -   `apps/api/app/models/email_processing_queue.py`
        -   `apps/api/app/models/email_drafts.py`
    -   API routes: `apps/api/app/routes/email_drafts.py`
    -   Migrations:
        -   `apps/api/alembic/versions/xxx_add_email_processing_queue.py`
        -   `apps/api/alembic/versions/xxx_add_email_drafts.py`

-   **Frontend:**

    -   Extend HITL queue page: `apps/web/src/app/dashboard/hitl/page.tsx`
    -   Components:
        -   `apps/web/src/components/email-drafts/DraftCard.tsx`
        -   `apps/web/src/components/email-drafts/OriginalEmailPreview.tsx`
    -   Reuse shadcn/ui: Card, Badge, Button, Dialog

-   **Worker Infrastructure:**
    -   Configure in `docker-compose.yml` or Kubernetes manifest
    -   Use same Redis instance as email poller
    -   Set worker concurrency based on LLM capacity

### Architecture Alignment

-   Integrates with RAG pipeline from Epic 3 (Stories 3.1, 3.2, 3.3, 3.4)
-   Extends HITL queue infrastructure from Epic 5
-   Follows async background processing pattern (consistent with Epic 2 document processing)
-   Multi-tenancy enforced via RLS (Epic 1 foundation)
-   PII redaction follows GDPR compliance requirements

### References

-   [Source: docs/epics.md - Epic 6: Email Automation, Story 6.4]
-   [Source: docs/prd.md - FR47: Email draft generation, FR49: HITL queue]
-   [Source: docs/architecture.md - RAG pipeline section]
-   Epic 3 Stories: 3.1 (Vector Search), 3.2 (Answer Generation), 3.3 (Citations), 3.4 (Confidence Scoring), 3.5 (PII Redaction)
-   Epic 5 Stories: 5.1 (HITL Queue View), 5.2 (Draft Review Interface)

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
