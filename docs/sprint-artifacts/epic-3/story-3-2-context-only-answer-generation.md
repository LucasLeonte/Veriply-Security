# Story 3.2: Context-Only Answer Generation

**Epic:** 3. RAG Q&A Engine  
**Status:** ready-for-dev  
**Assigned to:** TBD  
**Blocked by:** 3-1-semantic-vector-search
**Context:** docs/sprint-artifacts/epic-3/story-3-2.context.xml

## Story

As a System,  
I want to generate answers based ONLY on retrieved context,  
so that the AI never hallucinates from general knowledge.

## Acceptance Criteria

### Context-Only Generation

- [ ] LLM receives a structured prompt that enforces context-only behavior
- [ ] Prompt contains sections:
  - [ ] Instructions to answer only from context
  - [ ] Retrieved context chunks with clear boundaries
  - [ ] Original user query
  - [ ] Example format for responses
- [ ] LLM never references outside knowledge or general facts
- [ ] Response stays within the scope of provided documents

### Insufficient Context Handling

- [ ] When context chunks don't answer the query:
  - [ ] LLM responds: "I don't have information about that in the knowledge base."
  - [ ] No error is thrown
  - [ ] Query is marked for HITL review (low confidence)
- [ ] LLM never makes up facts when uncertain

### Response Quality

- [ ] Response is clear, concise, and well-structured
- [ ] Response includes relevant details from context
- [ ] Response is streamed token-by-token (Server-Sent Events)
- [ ] First token appears within 500ms
- [ ] Full response completes within 3 seconds
- [ ] Response length is reasonable (50-500 words typical)

### Edge Cases

- [ ] Empty context (no search results) is handled gracefully
- [ ] Contradictory context chunks don't break generation
- [ ] Context with code samples is formatted correctly
- [ ] Context with tables is presented readably
- [ ] Context with special characters is handled properly

## Technical Specifications

### Prompt Engineering

**System Prompt:**
```
You are a helpful assistant for Veriply, an AI-powered customer support platform.
Your role is to answer questions based ONLY on the provided context.

CRITICAL RULES:
1. Answer ONLY using the provided context
2. If the context doesn't contain the answer, say "I don't have information about that in the knowledge base."
3. NEVER make up facts
4. NEVER use outside knowledge
5. NEVER hallucinate details
6. Be clear and concise

When answering:
- Cite the source for important facts: "According to [Source]..."
- If multiple sources support your answer, mention all of them
- Keep responses conversational but professional
- Use the same tone as the source documents
```

**User Prompt Template:**
```
Context from our knowledge base:

{CONTEXT_CHUNKS_WITH_SEPARATORS}

---

Question: {USER_QUERY}

Answer (based ONLY on the context above):
```

**Context Formatting:**
```
[Source: Document Name - Section Title]
{chunk_text}
---
[Source: Document Name - Section Title]
{chunk_text}
---
```

### LLM Configuration

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| Model | Qwen 2.5 14B | Open source, good instruction-following |
| Temperature | 0.1 | Low for determinism, reduced hallucination |
| Top-p | 0.95 | Nucleus sampling for coherent responses |
| Max tokens | 512 | Reasonable response length limit |
| Frequency penalty | 0.0 | Allow repetition if necessary for accuracy |
| Presence penalty | 0.0 | Focus on accuracy over variety |

### Streaming Implementation

**Server-Sent Events (SSE) Flow:**
1. Client sends POST /api/query with query and context
2. Server validates inputs and prepares prompt
3. Server streams response via SSE:
   ```
   data: "The\n"
   data: " refund\n"
   data: " policy\n"
   data: " allows\n"
   ...
   ```
4. Client displays tokens as they arrive
5. Connection closes when generation complete

**Streaming Latency Targets:**
- First token: <500ms
- Full response (avg 200 tokens): <3s
- Per-token latency: ~10-15ms

### Temperature and Determinism

- **Temperature 0.1** ensures responses are predictable and consistent
- Same query + context = same answer (beneficial for reproducibility)
- Reduced hallucination risk compared to higher temperatures
- Trade-off: Slightly less creative, but maximizes accuracy

## API Contract

### Endpoint
```
POST /api/bots/{bot_id}/query
```

### Request
```json
{
  "query": "What is the refund policy?",
  "context_chunks": [
    {
      "text": "We offer a 30-day money-back guarantee...",
      "document_name": "Company Policies.pdf",
      "section": "Returns & Refunds",
      "similarity": 0.89
    },
    {
      "text": "Refund requests must be submitted within 30 days...",
      "document_name": "FAQ.md",
      "section": "Customer Support",
      "similarity": 0.82
    }
  ],
  "conversation_history": [
    {
      "role": "user",
      "content": "Previous question"
    },
    {
      "role": "assistant",
      "content": "Previous answer"
    }
  ],
  "stream": true
}
```

### Response (Streaming)
```
event: token
data: "The"

event: token
data: " refund"

event: token
data: " policy"

...

event: done
data: {"tokens": 45, "latency_ms": 1200}
```

### Response (Non-Streaming)
```json
{
  "answer": "The refund policy allows...",
  "tokens_generated": 45,
  "latency_ms": 1200,
  "model": "qwen2.5-14b",
  "temperature": 0.1
}
```

### Error Handling
```json
{
  "error": "No context provided",
  "status": 400
}
```

## Implementation Tasks

### Backend (FastAPI + Ollama)

1. **LLM Integration:**
   - Setup Ollama client library
   - Load Qwen 2.5 14B model
   - Implement streaming response generation
   - Implement fallback to OpenAI GPT-4o-mini

2. **Prompt Construction:**
   - Build system prompt with instructions
   - Format context chunks for clarity
   - Include conversation history (if available)
   - Ensure prompt < model's context window (8K tokens)

3. **Streaming Endpoint:**
   - FastAPI streaming response with SSE
   - Token-by-token yielding from LLM
   - Latency tracking (first token, total)
   - Graceful connection handling

4. **Testing:**
   - Unit tests: Prompt generation
   - Unit tests: Context formatting
   - Integration tests: End-to-end generation
   - Performance tests: <500ms first token, <3s total
   - Hallucination tests: Verify context-only responses
   - Edge case tests: Empty context, contradictions

### Frontend (Next.js)

1. **Streaming Client:**
   - EventSource API for SSE streaming
   - Render tokens as they arrive
   - Loading spinner while streaming
   - Stop button for long generations

2. **Response Display:**
   - Markdown rendering for answer
   - Display sources/citations inline
   - Loading indicator during generation
   - Error message display

3. **Conversation Context:**
   - Store conversation history in state
   - Pass to backend for context
   - Display conversation thread

## Dependencies

### Required
- Story 3.1 (Semantic Vector Search): Must provide context chunks
- Ollama service running with Qwen 2.5 14B model

### Optional
- OpenAI API key (fallback)
- Conversation history store (database or local storage)

## Acceptance Test Plan

### Test Scenarios

**Scenario 1: Basic Generation**
- Given: Query "What is refund policy?" with relevant context
- When: Generate answer
- Then: Answer is based on context, mentions refund terms

**Scenario 2: Insufficient Context**
- Given: Query with no relevant context
- When: Generate answer
- Then: Response is "I don't have information about that in the knowledge base."

**Scenario 3: Streaming Latency**
- Given: Generation request with streaming enabled
- When: Tokens are streamed
- Then: First token arrives <500ms, full response <3s

**Scenario 4: No Hallucination**
- Given: Query about topic outside knowledge base
- When: Generate answer
- Then: LLM refuses to answer from outside knowledge

**Scenario 5: Conversation Context**
- Given: Previous question about refunds, follow-up "What about exchanges?"
- When: Generate answer with conversation history
- Then: Answer understands "exchanges" in refund context

**Scenario 6: Complex Context**
- Given: Multiple conflicting chunks in context
- When: Generate answer
- Then: Response synthesizes information carefully, acknowledges complexity

## Definition of Done

- [ ] Context-only prompt template working and tested
- [ ] Streaming response generation <500ms first token
- [ ] No hallucinations detected in testing
- [ ] Insufficient context handled gracefully
- [ ] Edge cases tested (empty context, contradictions)
- [ ] Conversation history integration (if applicable)
- [ ] API documented and tested
- [ ] Frontend streaming display working
- [ ] Code reviewed and merged to main

## Functional Requirements Covered

- **FR21:** System generates answers based only on retrieved context ✓
- **FR25:** System refuses out-of-domain questions ✓

## Technical Notes

### Prompt Length Constraint

Total prompt tokens must be < model context window:
- Qwen 2.5 14B: 8K context window
- System prompt: ~200 tokens
- Context chunks: ~2000 tokens (5 chunks × 400 tokens each)
- Conversation history: ~1000 tokens (10 messages)
- User query: ~50 tokens
- **Total: ~3250 tokens, well within 8K limit**

If context exceeds available space, truncate oldest conversation history or highest similarity chunks.

### Temperature Tuning

- **Current: 0.1** (very low, deterministic)
- Trade-off: Accuracy over creativity
- Alternative: 0.3 for slightly more varied responses
- Do NOT exceed 0.5 (risk of hallucination increases significantly)

### Fallback Strategy

If Ollama Qwen model unavailable:
1. Check OpenAI API key
2. Fallback to GPT-4o-mini (higher latency, higher cost)
3. Last resort: Return error to user with retry message

### Monitoring

Metrics to track:
- Generation latency (first token, total)
- Response length distribution
- Rejection rate (queries with no context)
- User feedback (thumbs up/down)
- Hallucination detection (manual QA spot checks)

## Risk & Mitigation

| Risk | Mitigation |
|------|-----------|
| LLM generates hallucinations | Low temperature (0.1), strong prompt, test samples |
| Slow generation | Monitor latency, tune inference params |
| Out of memory (long context) | Truncate context, limit conversation history |
| Model unavailable | Fallback to OpenAI or queue for retry |
| Inaccurate citations | Implement citation post-processing (Story 3.3) |

## Dev Agent Record

### Context Reference

<!-- Story context XML will be added by context workflow -->

### Agent Model Used

Claude Haiku 4.5

### Completion Notes List

- Story 3.2 drafted with comprehensive prompt engineering strategy
- Temperature and parameter tuning documented for determinism
- Streaming implementation with SSE for token-by-token responses
- Context-only enforcement embedded in system prompt
- Hallucination mitigation strategies defined
- Fallback to OpenAI GPT-4o-mini if Ollama unavailable
- Conversation context integration for follow-up questions

### Debug Log References

### File List

<!-- Will be updated by dev agent during implementation -->

## Change Log

- 2025-12-04: Initial draft created by SM
  - Comprehensive prompt engineering strategy
  - Temperature tuning for context-only behavior
  - Streaming endpoint design (SSE)
  - Hallucination prevention tactics
  - Insufficient context handling
  - Conversation history integration
  - Fallback LLM strategies documented

