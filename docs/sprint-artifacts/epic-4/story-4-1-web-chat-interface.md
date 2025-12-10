# Story 4.1: Web Chat Interface

**Epic:** 4. Chat Experience  
**Status:** ready-for-dev  
**Assigned to:** Unassigned  
**Blocked by:** 3-2-context-only-answer-generation

## Story

As an End-user,  
I want to interact with a bot via a web-based chat interface,  
so that I can get answers to my questions.

## Acceptance Criteria

### Chat Interface Display

1. **Given** I navigate to a bot's public chat URL (`/chat/:bot_id`)  
   **When** the page loads  
   **Then** I see:
    - Chat window with bot name and avatar in header
    - Welcome message configured by the bot owner (max 500 chars)
    - Input field with placeholder "Ask a question..."
    - Send button (enabled/disabled based on input state)
    - Clean, responsive layout (mobile-first design)
2. **Given** the chat interface is loading
   **When** data is being fetched  
   **Then** I see a loading skeleton instead of broken layout  
   **And** no errors are displayed to user (logged server-side)

### Message Sending & Display

3. **Given** I type a question and press Enter or click Send  
   **When** the request is submitted  
   **Then** my message appears in the chat immediately (optimistic update)  
   **And** a typing indicator appears below my message
   **And** input field is cleared and disabled

4. **Given** the AI response is being generated  
   **When** tokens stream in via Server-Sent Events (SSE)  
   **Then** I see the response appear token-by-token (streaming display)  
   **And** the response is formatted with markdown support (bold, lists, code blocks)  
   **And** citations appear inline with format: `[Source: Document Name]`

5. **Given** the response is complete  
   **When** streaming finishes  
   **Then** the typing indicator disappears  
   **And** input field is re-enabled  
   **And** focus returns to input for next question

### Error Handling

6. **Given** an error occurs during response generation  
   **When** the error is received  
   **Then** I see a friendly error message: "Sorry, I encountered an issue. Please try again."  
   **And** the message includes a retry button  
   **And** full error details are logged server-side (not shown to user)

7. **Given** the bot is not found  
   **When** I navigate to invalid bot URL  
   **Then** I see: "Bot not found or is not available"  
   **And** I'm offered to return to home or contact support

### Session & History

8. **Given** I'm in a chat session  
   **When** I send multiple messages  
   **Then** all messages persist in the chat window for the session duration  
   **And** chat history is stored in browser localStorage (session-based)  
   **And** messages survive page refresh within same session

9. **Given** I close the chat window or leave the page  
   **When** I return later  
   **Then** the chat history is cleared (session-based, not persistent)  
   **And** I start a fresh conversation

### Responsiveness & Accessibility

10. **Given** I'm using a mobile browser  
    **When** the chat interface loads  
    **Then** all elements are touch-friendly (44x44px minimum)  
    **And** keyboard is not blocked by chat window  
    **And** scrolling works smoothly

11. **Given** I'm using a screen reader  
    **When** I interact with the chat  
    **Then** messages are announced with proper ARIA labels  
    **And** button roles are clear  
    **And** focus is managed correctly (WCAG 2.1 AA)

### Performance

12. **Given** I'm on a slow network connection  
    **When** I send a message  
    **Then** UI responds immediately (optimistic update)  
    **And** streaming begins within 2 seconds  
    **And** chat doesn't freeze or stutter

## Tasks / Subtasks

### 1) Frontend - Chat Component & Layout

-   [ ] Create Next.js page: `apps/web/src/app/chat/[botId]/page.tsx`
    -   [ ] Server component to fetch bot metadata and public settings
    -   [ ] Client component for interactive chat UI
    -   [ ] Verify bot is public/enabled before rendering
-   [ ] Build ChatWindow component:
    -   [ ] Header with bot name, avatar, close button
    -   [ ] Messages container with auto-scroll on new messages
    -   [ ] Loading skeleton for initial load
    -   [ ] Message thread display (user messages right-aligned, AI left-aligned)
    -   [ ] Typing indicator animation component
-   [ ] Build MessageInput component:
    -   [ ] Text area with Enter-to-send (Shift+Enter for newline)
    -   [ ] Send button with disabled state
    -   [ ] Character count indicator (optional)
    -   [ ] Markdown rendering for user messages
-   [ ] Apply styling:
    -   [ ] Use shadcn/ui Card, Input, Button components
    -   [ ] Tailwind for responsive layout (mobile-first)
    -   [ ] Cool Slate color theme from UX spec [Source: docs/ux-design-specification.md]
    -   [ ] 16px base font, high contrast for accessibility

### 2) Frontend - Streaming Response Display

-   [ ] Create MessageStreaming component:
    -   [ ] SSE event listener for incoming tokens
    -   [ ] Buffer tokens and update DOM efficiently
    -   [ ] Parse markdown in streamed content (use `react-markdown`)
    -   [ ] Render citations inline with detected pattern: `[Source: ...]`
    -   [ ] Performance: batch updates every 100ms or when newline detected
-   [ ] Integrate markdown rendering:
    -   [ ] Use `react-markdown` for safe parsing
    -   [ ] Support: bold, italic, lists, code blocks, links
    -   [ ] Disable dangerous HTML (no script tags, XSS prevention)
-   [ ] Handle edge cases:
    -   [ ] Long responses (>5000 chars) - no performance degradation
    -   [ ] Rapid token arrival (GPUs fast) - buffer and batch
    -   [ ] Network interruption - display partial response + retry option

### 3) Frontend - Session & History Management

-   [ ] Implement session storage:
    -   [ ] Store chat messages in localStorage: `key = chat_session_${botId}_${timestamp}`
    -   [ ] Persist on each message add/receive
    -   [ ] Clear on page unload (via useEffect cleanup)
    -   [ ] Implement "Start New Conversation" button
-   [ ] Message structure in storage:
    ```typescript
    interface ChatMessage {
        id: string; // UUID for React keys
        role: "user" | "assistant";
        content: string;
        timestamp: number;
        citations?: { source: string; url?: string }[];
    }
    ```

### 4) Frontend - Error Handling & User Feedback

-   [ ] Add error boundary component:
    -   [ ] Catches rendering errors, shows friendly message
    -   [ ] Logs to Sentry [Source: docs/architecture.md#Observability]
-   [ ] Implement retry mechanism:
    -   [ ] On message send failure: show "Retry" button
    -   [ ] On response error: show error message with retry
    -   [ ] Max 3 retries before giving up
-   [ ] Add loading and empty states:
    -   [ ] Skeleton loader while bot metadata loads
    -   [ ] "Waiting for response..." during initial connection

### 5) API - Chat Query Endpoint

-   [ ] Create endpoint: `POST /api/v1/bots/:bot_id/chat/query`
    -   [ ] Accept: `{ query: string, context?: string[] }` (context added in Story 4.2)
    -   [ ] Return: Server-Sent Events (SSE) stream with response tokens
    -   [ ] Validate:
        -   [ ] Bot exists and is public [Source: docs/epics.md#Story-4.1]
        -   [ ] Query length > 0 and < 5000 chars
        -   [ ] No special characters that break processing
-   [ ] Integrate with RAG pipeline:
    -   [ ] Call `POST /api/v1/bots/:bot_id/search` to retrieve context chunks
    -   [ ] Pass context + query to LLM via Ollama
    -   [ ] Stream tokens via SSE (chunk encoding)
    -   [ ] Parse citations from response and return structured

### 6) API - Public Bot Metadata Endpoint

-   [ ] Create endpoint: `GET /api/v1/bots/:bot_id/public`
    -   [ ] Returns public info: name, avatar, welcome_message, is_public
    -   [ ] Caches response (5 min TTL)
    -   [ ] Does NOT require authentication
    -   [ ] Used by public chat page to render header

### 7) Backend - SSE Response Streaming

-   [ ] Implement SSE streaming in FastAPI:
    ```python
    @router.post("/bots/{bot_id}/chat/query")
    async def chat_query(bot_id: UUID, query: ChatQuery):
        async def event_generator():
            async for token in llm_stream(query):
                yield f"data: {json.dumps({'token': token})}\n\n"
        return StreamingResponse(event_generator(), media_type="text/event-stream")
    ```
    -   [ ] Handle connection drops gracefully
    -   [ ] Set proper CORS headers for public endpoint
    -   [ ] Implement timeout (5 min max response time)

### 8) Testing - Component Tests

-   [ ] Test ChatWindow component:
    -   [ ] Renders welcome message on load
    -   [ ] Displays user message on send
    -   [ ] Shows typing indicator during response
    -   [ ] Streams tokens and updates display
    -   [ ] Error message on API failure
    -   [ ] "Start New Conversation" clears history
-   [ ] Test MessageInput component:
    -   [ ] Enter key sends message
    -   [ ] Shift+Enter adds newline
    -   [ ] Send button disabled when empty
    -   [ ] Input cleared after send
-   [ ] Use Vitest + React Testing Library [Source: apps/web/vitest.config.ts]

### 9) Testing - API Tests

-   [ ] Test `/api/v1/bots/:bot_id/public` endpoint:
    -   [ ] Returns 200 with bot metadata
    -   [ ] Returns 404 for invalid bot
    -   [ ] Returns 403 if bot is not public
-   [ ] Test `/api/v1/bots/:bot_id/chat/query` endpoint:
    -   [ ] Streams response tokens correctly
    -   [ ] Validates query length
    -   [ ] Returns error on invalid bot
    -   [ ] Handles LLM timeout gracefully
-   [ ] Use pytest + FastAPI TestClient [Source: apps/api/tests/]

### 10) Integration - SSE Connection

-   [ ] Configure Next.js to handle EventSource API:
    -   [ ] No special config needed (native browser API)
    -   [ ] Ensure API cors allows public access
-   [ ] Test end-to-end:
    -   [ ] Send message from web chat
    -   [ ] Verify tokens stream in
    -   [ ] Verify response appears in chat
    -   [ ] Manual E2E test with Playwright

### 11) Documentation & Deployment

-   [ ] Add JSDoc comments to components
-   [ ] Document API endpoint schema in OpenAPI/Swagger
-   [ ] Add usage examples in README
-   [ ] Verify performance on slow networks (throttle in DevTools)

## Dev Notes

### Architecture Patterns

-   **Public API Design**: Chat endpoint requires NO authentication (public access) but validates bot is public
-   **SSE Streaming**: Used for real-time token delivery, avoiding WebSocket complexity
-   **Optimistic Updates**: User message appears immediately (UX feedback), actual confirmation from server
-   **Error Isolation**: Errors logged server-side, friendly messages to users (security + UX)

### Component Reuse Opportunities

-   **From Epic 1 & 2**:

    -   Reuse `AuthService` JWT token handling (if user is logged in)
    -   Reuse validation patterns for bot_id (from Story 2-1)
    -   Reuse error handling patterns from `DeleteBotModal` and `DuplicateBotModal` [Source: epic-2/STORY-2-2-CODE-REVIEW.md]

-   **From Architecture**:
    -   Chat interface follows shadcn/ui component patterns established in admin UI
    -   Reuse Tailwind configuration for responsive design [Source: docs/architecture.md]
    -   Markdown rendering already tested in Epic 3 drafts

### Testing Standards

-   Follow test patterns from Story 2-2 (bot operations) [Source: epic-2/story-2-2-bot-duplication-deletion.md#Dev-Notes]
-   Unit tests for components (isolation with mocks)
-   Integration tests for API endpoints
-   E2E test: Navigate to chat → Send message → Verify response streams
-   Performance test: Slow network (3G throttle) should not freeze UI

### Security Considerations

-   **XSS Prevention**: Sanitize markdown input, never render raw HTML
-   **Rate Limiting**: Consider rate limit on `/chat/query` endpoint (10 req/min per IP)
-   **Public Access**: Verify bot is public before allowing query (in API, not just frontend)
-   **PII in Queries**: Epic 3.5 (PII Redaction) handles encryption [Source: docs/sprint-artifacts/epic-3/story-3-5-pii-redaction.md]

### Project Structure Alignment

-   **Frontend**: `apps/web/src/app/chat/[botId]/` (Next.js App Router dynamic route)
-   **Components**: `apps/web/src/components/Chat*` (MessageInput, ChatWindow, MessageStreaming)
-   **Hooks**: `apps/web/src/hooks/useChat.ts` (manage chat state and API calls)
-   **API Client**: `apps/web/src/lib/api/chat.ts` (SSE event source wrapper)
-   **Backend**: `apps/api/app/api/routes/chat.py` (query endpoint)
-   **Services**: `apps/api/app/services/chat_service.py` (RAG integration, LLM calling)

### Learnings from Previous Story

From Story 2-8 (Bot Isolation Enforcement) [Source: epic-2/story-2-8-bot-isolation-enforcement.md]:

-   **New Pattern**: Bot isolation via `bot_id` filtering in all queries

    -   **Reuse**: Apply same pattern to chat messages (filter by `bot_id`)
    -   **Service Created**: `BotService.get_bot()` for authorization - reuse for public bot lookup
    -   **Implementation**: Check [Source: epic-2/story-2-8-bot-isolation-enforcement.md#Dev-Notes] for RLS patterns

-   **Files Created in Epic 2**:
    -   `apps/api/app/models/bot.py` - Bot model with isolation methods (REUSE)
    -   `apps/api/app/services/bot_service.py` - BotService with authorization logic (REUSE)
    -   `apps/web/src/components/BotCard.tsx` - Bot card display (reference for styling)
-   **Architectural Decision**: All API endpoints now validate bot ownership before responding

    -   **Apply to Chat**: Public endpoint validates `is_public` flag instead of ownership
    -   **File to Reference**: [Source: epic-2/story-2-2-bot-duplication-deletion.md] shows bot endpoint pattern

-   **Testing Setup**: RLS enforcement and bot isolation already tested

    -   **Reuse**: Test patterns from `test_bots.py` for authorization tests
    -   **New**: Add test for public bot access (no auth required)

-   **Technical Debt Note**: Story 2-8 mentions potential rate limiting as future work - consider adding simple in-memory cache for public bot metadata

### Dependencies & Blockers

-   **Blocker**: Epic 3.2 (Context-Only Answer Generation) must be complete

    -   **Why**: Need LLM response endpoint working before building chat UI
    -   **Status**: Epic 3 stories are `ready-for-dev` but not started yet
    -   **Recommendation**: Start 3-2 in parallel with 4-1 or coordinate timing

-   **Optional Dependency**: Epic 5.1 (HITL Queue) for low-confidence routing
    -   **Note**: For this story, assume all responses go directly to user
    -   **Future**: Story 4.4 adds low-confidence detection + HITL routing

### References

-   Chat interface spec: [Source: docs/epics.md#Story-4.1]
-   RAG integration: [Source: docs/sprint-artifacts/epic-3/story-3-2-context-only-answer-generation.md]
-   UX design system: [Source: docs/ux-design-specification.md]
-   Architecture: [Source: docs/architecture.md#Chat-Experience]
-   Previous bot operations code: [Source: epic-2/story-2-1-bot-creation-configuration.md]
-   Streaming patterns: [Source: epic-2/story-2-2-bot-duplication-deletion.md#Dev-Agent-Record]
-   Test patterns: [Source: apps/api/tests/test_bots.py], [Source: apps/web/__tests__/DeleteBotModal.test.tsx]

## Dev Agent Record

### Context Reference

- docs/sprint-artifacts/epic-4/story-4-1.context.xml

### Agent Model Used

Claude Haiku 3.5

### Debug Log References

-   Setup Next.js public route for bot chat
-   Configure FastAPI SSE endpoint for streaming
-   Mock LLM responses during development (Story 3-2 integration comes later)

### Completion Notes List

-   [ ] Chat component renders with welcome message
-   [ ] User can type and send messages
-   [ ] Messages appear in chat window
-   [ ] Error handling displays friendly messages
-   [ ] Session history persists in localStorage
-   [ ] Responsive design works on mobile
-   [ ] API endpoints tested and working
-   [ ] Streaming response displays correctly
-   [ ] All unit tests passing
-   [ ] All integration tests passing

### File List

**Created (NEW):**

-   `apps/web/src/app/chat/[botId]/page.tsx` - Public chat page
-   `apps/web/src/components/ChatWindow.tsx` - Chat message display
-   `apps/web/src/components/MessageInput.tsx` - Message input field
-   `apps/web/src/components/MessageStreaming.tsx` - Token streaming display
-   `apps/web/src/hooks/useChat.ts` - Chat state management hook
-   `apps/web/src/lib/api/chat.ts` - Chat API client
-   `apps/api/app/api/routes/chat.py` - Chat query endpoints
-   `apps/api/app/services/chat_service.py` - Chat business logic
-   `apps/web/__tests__/ChatWindow.test.tsx` - Component tests
-   `apps/api/tests/test_chat.py` - API tests

**Modified:**

-   `apps/web/next.config.ts` - Add SSE headers if needed
-   `apps/api/app/main.py` - Register chat router

**Deleted:**

-   None
