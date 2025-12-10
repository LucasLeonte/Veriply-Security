# Story 4.2: Conversation Context

**Epic:** 4. Chat Experience  
**Status:** ready-for-dev  
**Assigned to:** Unassigned  
**Blocked by:** 4-1-web-chat-interface

## Story

As an End-user,  
I want the chat to remember our conversation,  
so that I can ask follow-up questions naturally.

## Acceptance Criteria

### Context Awareness

1. **Given** I asked "What is your refund policy?"  
   **And** the system responded with information about 30-day refunds  
   **When** I ask "What about after 30 days?"  
   **Then** the AI understands this refers to the refund policy (not a generic question)  
   **And** provides context-aware answer about extended refund terms  
   **And** I don't have to repeat the topic

### Context Window Management

2. **Given** I'm in an active chat conversation  
   **When** new messages arrive  
   **Then** the system maintains context from the last 10 messages  
   **And** older messages are progressively de-emphasized (not deleted)  
   **And** context window size is configurable per bot (default: 10)

3. **Given** the conversation has more than 10 messages  
   **When** a new query is submitted  
   **Then** the system summarizes older messages into a brief context paragraph  
   **And** passes both the summary + last 10 messages to the LLM  
   **And** the user doesn't see the summarization process

### Context Reset & Management

4. **Given** I click "Start New Conversation"  
   **When** the action is confirmed  
   **Then** the conversation history is cleared  
   **And** a new empty chat window appears  
   **And** the next message is treated as a fresh query (no prior context)

5. **Given** I close and reopen the chat window  
   **When** I return to the same bot  
   **Then** the previous conversation context is NOT retained (session-based)  
   **And** I start fresh in a new session  
   **And** conversation history is cleared from storage

### LLM Integration

6. **Given** I submit a follow-up question  
   **When** the query is sent to the LLM  
   **Then** the system prepends previous messages to the prompt:

    ```
    ## Conversation Context
    User: What is your refund policy?
    Assistant: [previous response]

    ## Current Question
    User: What about after 30 days?
    ```

    **And** the LLM uses this structure to generate contextual responses

7. **Given** context is being used for a query  
   **When** the response is generated  
   **Then** citations reference the current query context (not prior context)  
   **And** the user sees citations relevant to their latest question

### Performance & Limits

8. **Given** a conversation has accumulated 50+ messages  
   **When** a new query is processed  
   **Then** the system efficiently summarizes without delays  
   **And** LLM response time is not degraded (< 3s for streaming start)

9. **Given** a message contains a file attachment or image (future feature)  
   **When** context is summarized  
   **Then** file references are preserved in the summary  
   **And** the LLM can reference them

### Error Handling

10. **Given** the context retrieval fails  
    **When** the user sends a message  
    **Then** the system falls back to treating it as a standalone query  
    **And** a warning is logged (not shown to user)  
    **And** the chat continues normally

## Tasks / Subtasks

### 1) Frontend - Context State Management

-   [ ] Update `useChat` hook to maintain conversation history:
    -   [ ] Store array of all messages (user + assistant)
    -   [ ] Each message includes: id, role, content, timestamp, citations
    -   [ ] Implement `addMessage()` function to append new messages
    -   [ ] Implement `clearContext()` to reset conversation
-   [ ] Compute context window:
    -   [ ] Determine context_window_size from bot settings (configurable, default 10)
    -   [ ] Filter last N messages for inclusion in next query
-   [ ] Store full history in localStorage:
    -   [ ] Key: `chat_history_${botId}_${sessionId}`
    -   [ ] Periodically save on each message addition
    -   [ ] Clear on session end (page unload)

### 2) Frontend - Context Display

-   [ ] Add visual indicator in chat:
    -   [ ] Show "Context: 5 messages" above message input
    -   [ ] Optional: Collapsible "View Context" to see summarized history
-   [ ] Implement "Start New Conversation" button:
    -   [ ] Appears in chat header
    -   [ ] On click: show confirmation dialog
    -   [ ] On confirm: call `clearContext()` and refresh UI

### 3) Frontend - Context Summary Display

-   [ ] Create ContextSummary component:
    -   [ ] Displays summarized version of older messages (if > 10)
    -   [ ] Format: "Previous messages: You asked about X, assistant explained Y..."
    -   [ ] Collapsible (hidden by default in compact mode)
    -   [ ] Optional toggle to show/hide

### 4) API - Context Injection Endpoint

-   [ ] Create endpoint: `POST /api/v1/bots/:bot_id/chat/query-with-context`
    -   [ ] Accept: `{ query: string, context: ChatMessage[], context_window: int }`
    -   [ ] Validate context contains only messages from current session
    -   [ ] Validate context_window > 0 and < 100
-   [ ] Or update existing endpoint:
    -   [ ] `POST /api/v1/bots/:bot_id/chat/query` with optional `context` array
    -   [ ] If context provided, use it; otherwise treat as standalone query

### 5) Backend - Context Preparation Service

-   [ ] Create `ContextService.prepare_context()`:

    ```python
    async def prepare_context(messages: List[ChatMessage], context_window: int) -> str:
        """
        Prepare context string for LLM prompt injection.
        If > context_window: summarize older messages.
        """
        recent_messages = messages[-context_window:]
        older_messages = messages[:-context_window]

        if older_messages:
            # Call LLM to summarize (or use simple summary)
            summary = await summarize_messages(older_messages)
            return f"## Previous Context\n{summary}\n\n## Recent Messages\n{format_messages(recent_messages)}"
        else:
            return format_messages(recent_messages)
    ```

    -   [ ] Format messages as role-based pairs for clarity
    -   [ ] Include assistant citations in context
    -   [ ] Preserve message order

### 6) Backend - Summarization Logic

-   [ ] Implement message summarization:
    -   [ ] Option A (Simple): Extract unique topics and counts from message history
        ```python
        "User asked about refunds (2 times), assistant explained 30-day policy and exceptions"
        ```
    -   [ ] Option B (Smart): Use a small LLM call to generate summary (more expensive)
-   [ ] Cache summaries:
    -   [ ] Store in session memory (not persistent)
    -   [ ] Recompute on new messages
-   [ ] Test edge cases:
    -   [ ] Single message (no summary needed)
    -   [ ] Exactly context_window messages (no summarization)
    -   [ ] More than 2x context_window (aggressive summarization)

### 7) Backend - LLM Prompt Structuring

-   [ ] Update `chat_service.py`:

    -   [ ] New function: `build_prompt_with_context(query: str, context: str) -> str`
    -   [ ] Structure:

        ```
        # System Prompt
        You are a helpful customer service AI...

        # Conversation Context (if provided)
        [previous messages summary or full messages]

        # Current Question
        [user query]
        ```

    -   [ ] Pass to Ollama API for response generation
    -   [ ] Test that context improves response relevance

### 8) Backend - Session Isolation

-   [ ] Ensure conversation context is NOT persisted across sessions:
    -   [ ] Context stored only in-flight (not in database)
    -   [ ] Each session gets fresh context window
    -   [ ] No user tracking across sessions (privacy-friendly)

### 9) Testing - Component Tests

-   [ ] Test `useChat` hook:
    -   [ ] `addMessage()` appends to history
    -   [ ] History persists in localStorage
    -   [ ] `clearContext()` empties history
    -   [ ] Context window size respected
-   [ ] Test ContextSummary component:
    -   [ ] Displays only if > context_window messages
    -   [ ] Shows friendly summary text
    -   [ ] Collapsible toggle works
-   [ ] Use Vitest + React Testing Library

### 10) Testing - API Tests

-   [ ] Test context injection:
    -   [ ] Query with context produces contextual response
    -   [ ] Query without context treated as standalone
    -   [ ] Summarization doesn't break response
    -   [ ] Large context (100 messages) handled gracefully
-   [ ] Test context validation:
    -   [ ] Rejects context_window > 100
    -   [ ] Rejects context with wrong bot_id
-   [ ] Use pytest + TestClient

### 11) Testing - Integration Tests

-   [ ] E2E test with Playwright:
    -   [ ] Send initial question
    -   [ ] Send follow-up that requires context
    -   [ ] Verify response uses context (check content relevance)
    -   [ ] Click "Start New Conversation"
    -   [ ] Send same follow-up → verify it's treated as standalone
    -   [ ] Test on slow network (ensure no timeout)

### 12) Performance Optimization

-   [ ] Benchmark context preparation:
    -   [ ] Measure time for 50, 100, 200 message context
    -   [ ] Target: < 500ms for preparation
    -   [ ] Optimize summarization if too slow
-   [ ] Implement lazy summarization:
    -   [ ] Only summarize when needed (on query submission)
    -   [ ] Cache summary for reuse in same session
-   [ ] Monitor LLM response time:
    -   [ ] Ensure context injection doesn't increase latency
    -   [ ] Target: streaming start within 2s (same as no context)

## Dev Notes

### Architecture Patterns

-   **Session-Based Context**: No persistent storage, only in-memory + localStorage
-   **Lazy Summarization**: Only summarize when context > threshold
-   **Prompt Injection**: Context prepended to LLM prompt in structured format
-   **Privacy-First**: No tracking across sessions, fresh context per chat instance

### Component Reuse

-   **From Story 4.1**: Reuse ChatWindow, MessageInput, useChat hook (extending hooks)
-   **From Epic 3**: Leverage LLM integration patterns (Ollama streaming)
-   **From Epic 2**: Bot isolation patterns apply to context (scoped per bot)

### Security Considerations

-   **Context Isolation**: Ensure context is never shared across users or bots
-   **Injection Prevention**: Sanitize context before passing to LLM (escape special chars)
-   **Session Isolation**: Clear context on session end (no cross-session leakage)
-   **Rate Limiting**: Per-user rate limit applies (same as Story 4.1)

### Learnings from Previous Story

From Story 4.1 (Web Chat Interface) [Source: epic-4/story-4-1-web-chat-interface.md]:

-   **Streaming Integration**: SSE endpoint works well for token-by-token display
    -   **Apply**: Reuse same streaming pattern for contextual queries
-   **Optimistic Updates**: User message appears immediately before server confirmation
    -   **Extend**: Show "Context loaded (5 messages)" while computing context
-   **Error Handling**: Fallback to friendly user message when API fails
    -   **Apply**: If context retrieval fails, fall back to standalone query

### Dependencies & Blockers

-   **Requires**: Story 4.1 (Chat interface) must be complete
-   **Optional**: Story 5.1 (HITL) could provide low-confidence context queries
-   **Future**: Story 4.2 extended with memory persistence (cross-session) as premium feature

### References

-   Context-aware conversational AI: [Source: docs/epics.md#Story-4.2]
-   RAG pipeline integration: [Source: docs/sprint-artifacts/epic-3/story-3-2-context-only-answer-generation.md]
-   Chat interface: [Source: epic-4/story-4-1-web-chat-interface.md]
-   Architecture: [Source: docs/architecture.md]
-   Test standards: [Source: .bmad/bmm/testarch/knowledge/test-quality.md#Deterministic-Test-Pattern]

## Dev Agent Record

### Context Reference

-   docs/sprint-artifacts/epic-4/story-4-2.context.xml

### Agent Model Used

Claude Haiku 3.5

### Debug Log References

-   Implement message summarization algorithm
-   Test context window boundaries
-   Verify LLM receives context properly formatted

### Completion Notes List

-   [ ] Message history stored and persists in session
-   [ ] Context window size configurable
-   [ ] Summarization logic works for large histories
-   [ ] LLM receives context-aware prompts
-   [ ] Follow-up questions generate contextual responses
-   [ ] "Start New Conversation" clears history
-   [ ] No context leakage across sessions
-   [ ] All unit tests passing
-   [ ] All integration tests passing

### File List

**Created (NEW):**

-   `apps/web/src/components/ContextSummary.tsx` - Summary display component
-   `apps/api/app/services/context_service.py` - Context preparation logic
-   `apps/api/app/services/summary_service.py` - Message summarization
-   `apps/web/__tests__/ChatWindow.context.test.tsx` - Context tests

**Modified:**

-   `apps/web/src/hooks/useChat.ts` - Add context management functions
-   `apps/web/src/app/chat/[botId]/page.tsx` - Pass context to queries
-   `apps/web/src/components/ChatWindow.tsx` - Add "Start New Conversation" button
-   `apps/api/app/services/chat_service.py` - Update query endpoint to accept context

**Deleted:**

-   None
