# Story 4.3: User Feedback

**Epic:** 4. Chat Experience  
**Status:** ready-for-dev  
**Assigned to:** Unassigned  
**Blocked by:** 4-1-web-chat-interface

## Story

As an End-user,  
I want to provide feedback on AI answers,  
so that the system can learn from my input.

## Acceptance Criteria

### Feedback Collection UI

1. **Given** I received an AI answer in the chat  
   **When** I look at the message  
   **Then** I see two feedback icons below the response:

    - Thumbs up icon (outlined initially)
    - Thumbs down icon (outlined initially)

2. **Given** I hover over the thumbs up icon  
   **When** I look at the tooltip  
   **Then** I see: "Helpful response"

3. **Given** I hover over the thumbs down icon  
   **When** I look at the tooltip  
   **Then** I see: "Not helpful"

### Positive Feedback

4. **Given** I clicked the thumbs up icon  
   **When** the click is processed  
   **Then** the icon fills in (solid state)  
   **And** a success toast appears: "Thank you for the feedback!"  
   **And** the feedback is recorded with type: "positive"

### Negative Feedback with Reason

5. **Given** I clicked the thumbs down icon  
   **When** the click is processed  
   **Then** the icon fills in (solid state)  
   **And** a feedback form appears with the question: "What was wrong?"  
   **And** options are provided:

    - "Incorrect information"
    - "Not helpful / Irrelevant"
    - "Incomplete answer"
    - "Harmful or unsafe"
    - "Other (optional text)"

6. **Given** I selected a reason from the list  
   **When** I confirm or submit  
   **Then** the feedback is recorded with:

    - type: "negative"
    - reason: selected option
    - additional_notes: optional text if "Other" selected

7. **Given** I selected "Other"  
   **When** I see the form  
   **Then** a text field appears with placeholder: "Tell us more..."  
   **And** character count shows 0/500 chars

### Feedback Persistence & State

8. **Given** I provided feedback (thumbs up or down)  
   **When** I look at the message again  
   **Then** the icon remains filled  
   **And** I cannot provide feedback twice for the same message  
   **And** I can change my feedback (click opposite icon to switch)

9. **Given** I change my mind and click the opposite icon  
   **When** the change is processed  
   **Then** the old feedback is replaced with the new feedback  
   **And** a new reason form appears (if clicking down)  
   **And** previous reason is cleared

### Feedback Logging & User Tracking

10. **Given** I provide feedback  
    **When** the feedback is recorded  
    **Then** the feedback is logged with my user account information  
    **And** the timestamp and user_id are recorded  
    **And** the session_id and IP address are captured for audit trail  
    **And** all feedback is traceable to prevent sabotage

11. **Given** I provide negative feedback with "Harmful"  
    **When** the feedback is recorded  
    **Then** it is flagged for urgent review (logged as critical event)  
    **And** the system alerts moderation team with user info [monitored async]  
    **And** a full audit trail is created for investigation

### Error Handling

12. **Given** the feedback submission fails (network error)  
    **When** the user sees the result  
    **Then** a retry button appears  
    **And** the icon remains in a pending state (semi-filled)  
    **And** max 3 automatic retries before showing error

13. **Given** feedback submission encounters rate limiting  
    **When** the user tries again  
    **Then** a message appears: "Please wait before providing more feedback"  
    **And** icons are disabled for 1 minute

### Analytics Integration

14. **Given** feedback has been collected  
    **When** the analytics system processes it  
    **Then** the feedback contributes to:

    -   Answer quality metrics
    -   Bot confidence calibration
    -   Trust Score calculation
    -   Aggregate statistics (shown in analytics dashboard)

15. **Given** a specific AI response has 3 "Harmful" feedback items  
    **When** the system detects this pattern  
    **Then** an alert is created for moderation review

## Tasks / Subtasks

### 1) Frontend - Feedback UI Component

-   [ ] Create `FeedbackBar` component:
    -   [ ] Render below each AI message
    -   [ ] Show thumbs-up and thumbs-down icons
    -   [ ] Use shadcn/ui Button or Icon components
    -   [ ] Style: 16px icons, 8px spacing, Cool Slate colors
-   [ ] Implement icon states:
    -   [ ] Outlined (default, clickable)
    -   [ ] Filled (selected, semi-opaque on hover)
    -   [ ] Pending (semi-transparent, disabled)
    -   [ ] Disabled (grayed out after rate limit)
-   [ ] Add tooltips:
    -   [ ] Use shadcn/ui Tooltip component
    -   [ ] Hover text: "Helpful" / "Not helpful"

### 2) Frontend - Feedback Form Modal

-   [ ] Create `FeedbackReasonModal` component:
    -   [ ] Shows on thumbs-down click
    -   [ ] Modal with title: "What was wrong?"
    -   [ ] Radio button options (shadcn/ui RadioGroup):
        -   "Incorrect information"
        -   "Not helpful / Irrelevant"
        -   "Incomplete answer"
        -   "Harmful or unsafe"
        -   "Other"
    -   [ ] Conditional text field for "Other"
        -   Max 500 chars
        -   Character counter
        -   Placeholder: "Tell us more..."
    -   [ ] Submit button: "Send Feedback"
    -   [ ] Cancel button
-   [ ] Form validation:
    -   [ ] At least one reason selected
    -   [ ] "Other" requires text input (min 10 chars)
    -   [ ] Show validation errors on submit

### 3) Frontend - Feedback State Management

-   [ ] Update `useChat` hook:
    -   [ ] Add `feedbackState: { [messageId]: { type, reason, timestamp } }`
    -   [ ] Function: `submitFeedback(messageId, type, reason)`
    -   [ ] Function: `removeFeedback(messageId)` (to change feedback)
    -   [ ] Store feedback in sessionStorage: `feedback_${botId}_${sessionId}`
-   [ ] Prevent duplicate feedback:
    -   [ ] Check `feedbackState` before allowing second feedback
    -   [ ] Allow changing feedback (remove old, add new)
-   [ ] Implement rate limiting:
    -   [ ] Track feedback count per session
    -   [ ] Max 20 feedback items per 5 minutes per session
    -   [ ] Show cooldown timer if rate limited

### 4) API - Feedback Submission Endpoint

-   [ ] Create endpoint: `POST /api/v1/bots/:bot_id/feedback`
    -   [ ] Accept:
        ```typescript
        {
          answer_id: UUID;  // Reference to specific AI response
          message_id: string; // Chat message ID
          type: "positive" | "negative";
          reason?: "incorrect" | "not_helpful" | "incomplete" | "harmful" | "other";
          additional_notes?: string;
        }
        ```
    -   [ ] Extract from request context:
        -   [ ] user_id from JWT token (must be authenticated)
        -   [ ] session_id from request session
        -   [ ] ip_address from request headers (X-Forwarded-For or remote_addr)
    -   [ ] Validate:
        -   [ ] User is authenticated (has valid JWT)
        -   [ ] Bot exists and belongs to user's tenant
        -   [ ] Answer ID is valid
        -   [ ] Type is valid enum
        -   [ ] If negative: reason is required
        -   [ ] Character limit on additional_notes (500)
    -   [ ] Log submission:
        -   [ ] Create audit log entry with user_id, timestamp, action
        -   [ ] Include IP address for fraud detection
    -   [ ] Return: `{ success: true, feedback_id: UUID }`
    -   [ ] **REQUIRES AUTHENTICATION** (JWT token in Authorization header)

### 5) Backend - Feedback Data Model

-   [ ] Create `Feedback` model in SQLAlchemy:

    ```python
    class Feedback(Base):
        __tablename__ = "feedback"

        id: UUID = Column(UUID, primary_key=True, default=uuid4)
        tenant_id: UUID = Column(UUID, ForeignKey("tenants.id"), nullable=False)
        bot_id: UUID = Column(UUID, ForeignKey("bots.id"), nullable=False)
        user_id: UUID = Column(UUID, ForeignKey("users.id"), nullable=False)
        answer_id: UUID = Column(UUID, nullable=False)  # Reference to RAG response
        type: str = Column(Enum("positive", "negative"), nullable=False)
        reason: str = Column(Enum(...), nullable=True)
        additional_notes: str = Column(String(500), nullable=True)
        session_id: str = Column(String(255), nullable=True)  # Session tracking
        ip_address: str = Column(String(45), nullable=True)  # IPv4 or IPv6
        created_at: DateTime = Column(DateTime, default=utcnow, nullable=False)
        # User tracking enabled to prevent sabotage
    ```

    -   [ ] Add index on (bot_id, user_id, created_at) for user feedback history
    -   [ ] Add index on (bot_id, type, created_at) for aggregate stats
    -   [ ] Add index on (user_id, created_at) for abuse detection
    -   [ ] Enable RLS: `tenant_id = current_setting('app.current_tenant_id')::uuid`

### 6) Backend - Feedback Service

-   [ ] Create `FeedbackService` class:
    -   [ ] Method: `async def record_feedback(user_id, bot_id, answer_id, type, reason, notes, session_id, ip_address)`
    -   [ ] Validations:
        -   [ ] User exists and belongs to tenant
        -   [ ] Bot exists and belongs to user's tenant
        -   [ ] Answer ID is valid (exists in response table or memory)
    -   [ ] Store feedback in database with user tracking:
        -   [ ] Store user_id, session_id, ip_address
        -   [ ] Create audit log entry: action="feedback_submitted", user_id, details
    -   [ ] Publish feedback event to analytics service
    -   [ ] Check for "Harmful" feedback → alert moderation with user info
    -   [ ] Check for user abuse pattern:
        -   [ ] If user submits 5+ negative feedbacks with "Harmful" in 1 hour: flag account
        -   [ ] Log abuse detection event
        -   [ ] Alert admin for investigation
    -   [ ] Return feedback_id
-   [ ] Create `AuditService.log_feedback()`:
    -   [ ] Log user_id, feedback_id, type, timestamp, ip_address
    -   [ ] Create entry in `audit_logs` table for compliance
    -   [ ] Enable traceability for sabotage investigation

### 7) Backend - Analytics Integration

-   [ ] Create `FeedbackAnalyticsService`:
    -   [ ] Method: `async def aggregate_stats(bot_id, time_window: str)`
    -   [ ] Compute:
        -   [ ] Total feedback count
        -   [ ] Positive/Negative ratio
        -   [ ] Top negative reasons (grouped)
        -   [ ] "Harmful" feedback count (alert if > 3)
    -   [ ] Cache results: 1 hour TTL
    -   [ ] Endpoint: `GET /api/v1/bots/:bot_id/feedback/stats`
        -   [ ] Returns aggregate stats (no individual feedback)
        -   [ ] Requires bot owner authentication

### 8) Backend - Moderation Alerts & Abuse Detection

-   [ ] Implement alert system for critical feedback:
    -   [ ] On "Harmful" feedback received:
        -   [ ] Check count for this answer (sliding 24h window)
        -   [ ] If >= 3 "Harmful" in 24h: create `ModerationAlert`
        -   [ ] Alert includes: bot_id, answer content, feedback count, **user_id list**
        -   [ ] Alert stored in database and logged with full audit trail
    -   [ ] Endpoint: `GET /api/v1/moderation/alerts`
        -   [ ] Bot owners can view alerts for their bots
        -   [ ] Admins can view all alerts with user details
-   [ ] Implement user abuse detection:
    -   [ ] Track user feedback pattern:
        -   [ ] Count feedback submissions by user per 1-hour window
        -   [ ] Flag if same user submits 5+ "Harmful" feedbacks in 1 hour
        -   [ ] Create `UserAbuseSuspicion` alert with user_id, ip_address, feedback_ids
        -   [ ] Store in database for admin review
    -   [ ] Endpoint: `GET /api/v1/moderation/user-abuse`
        -   [ ] Admins can view suspicious users
        -   [ ] Includes user info, feedback history, IP addresses
        -   [ ] Enable account investigation and potential suspension

### 9) Testing - Component Tests

-   [ ] Test FeedbackBar component:
    -   [ ] Renders thumbs-up and thumbs-down icons
    -   [ ] Icons clickable and change state
    -   [ ] Tooltips display on hover
    -   [ ] Rate limiting disables icons after 20 feedback
-   [ ] Test FeedbackReasonModal component:
    -   [ ] Shows on thumbs-down click
    -   [ ] Radio buttons functional
    -   [ ] Text field appears for "Other"
    -   [ ] Form validates before submit
    -   [ ] Submit button sends feedback
    -   [ ] Cancel button closes modal
-   [ ] Use Vitest + React Testing Library

### 10) Testing - API Tests

-   [ ] Test feedback submission:
    -   [ ] Valid positive feedback recorded
    -   [ ] Valid negative feedback with reason recorded
    -   [ ] Additional notes saved (max 500 chars)
    -   [ ] Invalid reason rejected (400)
    -   [ ] Invalid bot rejected (404)
    -   [ ] Rate limiting enforced (429 after 20/5min)
-   [ ] Test analytics endpoint:
    -   [ ] Returns aggregate stats
    -   [ ] Excludes individual feedback
    -   [ ] Caching works (same result on repeat calls)
-   [ ] Test moderation alerts:
    -   [ ] 3 "Harmful" creates alert
    -   [ ] Alert retrievable by bot owner
    -   [ ] <3 "Harmful" does not create alert
-   [ ] Use pytest + TestClient

### 11) Testing - Integration Tests

-   [ ] E2E with Playwright:
    -   [ ] Send message → get response
    -   [ ] Click thumbs-up → verify feedback submitted
    -   [ ] Click thumbs-down → see reason form
    -   [ ] Select reason → submit feedback
    -   [ ] Verify icon remains filled
    -   [ ] Click opposite icon → change feedback
    -   [ ] Rate limit: submit 25 feedback → verify cooldown message
    -   [ ] Verify feedback appears in bot owner's analytics

### 12) Documentation & Deployment

-   [ ] Add JSDoc comments to components and service methods
-   [ ] Document feedback API in OpenAPI spec
-   [ ] Document analytics calculations in README
-   [ ] Add moderation guide for alerts
-   [ ] Privacy policy: clarify feedback is anonymous

## Dev Notes

### Architecture Patterns

-   **Anonymous Feedback**: No user tracking, session-based anonymity
-   **Feedback-as-Events**: Emit events to analytics service for decoupled processing
-   **Alert System**: Pattern for critical feedback detection and escalation
-   **Rate Limiting**: Per-session limit prevents spam feedback

### Component Reuse

-   **From Story 4.1**: Reuse ChatWindow message structure (messageId)
-   **From Epic 2**: Reuse bot authorization patterns (bot_id validation)
-   **From Epic 1**: Reuse error toast/notification patterns

### Security & Privacy

-   **User Tracking**: Feedback is logged with user_id, session_id, IP address to prevent sabotage
-   **Audit Trail**: All feedback submissions create audit log entries for compliance and investigation
-   **Abuse Detection**: User patterns monitored to identify feedback spam or coordinated sabotage
-   **Data Minimization**: Only store necessary feedback fields (no additional PII beyond user_id)
-   **Critical Alerting**: "Harmful" feedback triggers moderation review with full user context
-   **Rate Limiting**: Per-session limit prevents spam; per-user hour limit detects patterns

### Learnings from Previous Stories

From Epic 2 (Bot Management) [Source: epic-2/story-2-8-bot-isolation-enforcement.md]:

-   **Bot Isolation**: Feedback must be scoped to bot_id (no cross-bot leakage)
    -   **Apply**: Feedback table includes bot_id, query filters by bot_id
    -   **Reuse**: Bot authorization patterns from BotService.get_bot()

From Story 4.1 (Chat Interface) [Source: epic-4/story-4-1-web-chat-interface.md]:

-   **UI Patterns**: Tooltips and icons already established for chat
    -   **Reuse**: Same styling approach for feedback icons
-   **Error Handling**: Toast notifications for success/error feedback
    -   **Reuse**: Same pattern for feedback submission feedback

### Dependencies & Blockers

-   **Requires**: Story 4.1 (Chat interface) must be complete for feedback UI
-   **Optional**: Story 8.1 (Analytics dashboard) displays feedback stats
-   **Integration**: Feedback feeds into Trust Score calculation (Epic 3.4)

### References

-   Feedback specification: [Source: docs/epics.md#Story-4.3]
-   Chat interface: [Source: epic-4/story-4-1-web-chat-interface.md]
-   Analytics integration: [Source: docs/architecture.md#Analytics]
-   User tracking & audit: [Source: docs/prd.md#Security-and-Compliance, Epic 1 audit logging]
-   Abuse detection patterns: [Source: docs/architecture.md#Security]
-   Test standards: [Source: .bmad/bmm/testarch/knowledge/test-quality.md]

## Dev Agent Record

### Context Reference

-   docs/sprint-artifacts/epic-4/story-4-3.context.xml

### Agent Model Used

Claude Haiku 3.5

### Debug Log References

-   Implement feedback modal form
-   Test rate limiting logic
-   Verify anonymous feedback (no user tracking)
-   Test moderation alert trigger (3 "Harmful" threshold)

### Completion Notes List

-   [ ] Feedback icons render below AI messages
-   [ ] Thumbs-up feedback recorded
-   [ ] Thumbs-down shows reason form
-   [ ] Feedback reason validation works
-   [ ] Feedback persists in session
-   [ ] Icons remain filled after feedback
-   [ ] Rate limiting prevents spam
-   [ ] Moderation alerts created for harmful feedback
-   [ ] Analytics stats endpoint works
-   [ ] All unit tests passing
-   [ ] All integration tests passing

### File List

**Created (NEW):**

-   `apps/web/src/components/FeedbackBar.tsx` - Feedback icons component
-   `apps/web/src/components/FeedbackReasonModal.tsx` - Reason selection form
-   `apps/api/app/models/feedback.py` - Feedback SQLAlchemy model
-   `apps/api/app/services/feedback_service.py` - Feedback business logic
-   `apps/api/app/services/feedback_analytics_service.py` - Analytics aggregation
-   `apps/api/app/api/routes/feedback.py` - Feedback API endpoints
-   `apps/web/__tests__/FeedbackBar.test.tsx` - Component tests
-   `apps/api/tests/test_feedback.py` - API tests

**Modified:**

-   `apps/web/src/hooks/useChat.ts` - Add feedback state management
-   `apps/web/src/components/ChatWindow.tsx` - Add FeedbackBar to messages
-   `apps/api/app/main.py` - Register feedback router

**Deleted:**

-   None
