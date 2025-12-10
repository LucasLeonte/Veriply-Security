# Story 3.1: Semantic Vector Search

**Epic:** 3. RAG Q&A Engine  
**Status:** ready-for-dev  
**Assigned to:** TBD  
**Blocked by:** 2-4-document-processing-pipeline
**Context:** docs/sprint-artifacts/epic-3/story-3-1.context.xml

## Story

As a System,  
I want to retrieve relevant document chunks for a user query,  
so that the LLM has accurate context to generate answers.

## Acceptance Criteria

### Vector Search Functionality

- [ ] User query is embedded using bge-m3 model (same model as documents)
- [ ] pgvector cosine similarity search retrieves top-K chunks (K=5 default)
- [ ] Results are filtered by tenant_id AND bot_id (RLS enforcement)
- [ ] Search results include:
  - [ ] Chunk text content
  - [ ] Document name (source)
  - [ ] Section/page reference (if available)
  - [ ] Similarity score (0-1 scale)
  - [ ] Chunk metadata (document_id, chunk_id, position)

### Search Performance

- [ ] Search latency is <200ms (p95) for typical knowledge bases
- [ ] pgvector HNSW index is created for fast approximate search
- [ ] Index includes tenant_id and bot_id for query filtering

### No Results Handling

- [ ] When no relevant chunks exist (all similarity < 0.5):
  - [ ] Empty result set is returned
  - [ ] No error is thrown
  - [ ] Downstream RAG pipeline handles gracefully

### Edge Cases

- [ ] Very short queries (1-2 words) still produce meaningful embeddings
- [ ] Very long queries (>500 tokens) are truncated before embedding
- [ ] Special characters and non-ASCII text are handled correctly
- [ ] Identical queries return identical results (deterministic)

## Technical Specifications

### Architecture

**Query Processing Pipeline:**
1. Input: User query string
2. Embed query using bge-m3 (1024 dimensions)
3. Normalize embedding vector
4. Compute cosine similarity with pgvector
5. Apply tenant/bot filtering (WHERE bot_id = $1 AND tenant_id = $2)
6. Sort by similarity DESC
7. Return top K results

**Database Schema:**
```sql
-- Chunks table with vector column
CREATE TABLE chunks (
  id UUID PRIMARY KEY,
  document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
  bot_id UUID NOT NULL,
  tenant_id UUID NOT NULL,
  position INT,
  text TEXT NOT NULL,
  embedding vector(1024),
  metadata JSONB,
  created_at TIMESTAMP,
  CONSTRAINT fk_bot FOREIGN KEY (bot_id) REFERENCES bots(id),
  CONSTRAINT fk_tenant FOREIGN KEY (tenant_id) REFERENCES tenants(id)
);

-- Index for fast search
CREATE INDEX idx_chunks_embedding_hnsw ON chunks 
USING hnsw (embedding vector_cosine_ops) 
WITH (m = 16, ef_construction = 64);

-- Filter index
CREATE INDEX idx_chunks_bot_tenant ON chunks(bot_id, tenant_id);
```

### Similarity Search Query

```python
# Pseudocode: SQLAlchemy async query
results = await session.execute(
  select(Chunk).
  where(
    (Chunk.bot_id == bot_id) &
    (Chunk.tenant_id == tenant_id)
  ).
  order_by(Chunk.embedding.cosine_distance(query_embedding)).
  limit(k)
)

# Results include similarity score as computed column
for chunk in results:
  similarity = 1 - chunk.embedding.cosine_distance(query_embedding)
  yield {
    'text': chunk.text,
    'document_name': chunk.document.name,
    'similarity': similarity,
    'chunk_id': chunk.id,
    'document_id': chunk.document_id,
    'section': chunk.metadata.get('section')
  }
```

### Embedding Model

- **Model:** bge-m3 (by BAAI)
- **Dimensions:** 1024
- **Endpoint:** Ollama local service (http://localhost:11434)
- **Fallback:** OpenAI Embedding API if Ollama unavailable
- **Latency:** ~20ms per embedding (local Ollama)

### Tuning Parameters

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| K (top chunks) | 5 | Balance: enough context without noise |
| Similarity threshold | 0.5 | Filter very weak matches |
| HNSW m | 16 | Good recall/speed tradeoff |
| HNSW ef_construction | 64 | ~15% recall loss for 2x speed |
| HNSW ef_search | 40 | Runtime search parameter |

## API Contract

### Endpoint
```
POST /api/bots/{bot_id}/search
```

### Request
```json
{
  "query": "What is the refund policy?",
  "k": 5,
  "similarity_threshold": 0.5
}
```

### Response
```json
{
  "query": "What is the refund policy?",
  "results": [
    {
      "chunk_id": "uuid",
      "document_id": "uuid",
      "document_name": "Company Policies.pdf",
      "section": "Returns & Refunds",
      "text": "We offer a 30-day money-back guarantee...",
      "similarity": 0.89,
      "position": 3
    },
    {
      "chunk_id": "uuid",
      "document_id": "uuid",
      "document_name": "FAQ.md",
      "section": "Customer Support",
      "text": "Refund requests must be submitted within 30 days...",
      "similarity": 0.82,
      "position": 1
    }
  ],
  "search_latency_ms": 45
}
```

### Error Handling
```json
{
  "error": "Bot not found",
  "status": 404
}
```

## Implementation Tasks

### Backend (FastAPI + SQLAlchemy)

1. **Create vector search service:**
   - Load bge-m3 model from Ollama
   - Implement embedding function
   - Implement search function with RLS enforcement
   - Handle embedding errors gracefully

2. **Database setup:**
   - Create Alembic migration for chunks table
   - Create HNSW index on embedding column
   - Add composite index on (bot_id, tenant_id)

3. **API endpoint:**
   - POST /api/bots/{bot_id}/search
   - Input validation (query length, k value)
   - RLS enforcement (user must own bot)
   - Response formatting with latency timing

4. **Testing:**
   - Unit tests: embedding generation
   - Unit tests: vector search with mock data
   - Integration tests: search with RLS
   - Performance tests: <200ms p95 latency

### Frontend (Next.js)

1. **API client method:**
   - `searchDocuments(botId, query, k)` hook
   - Loading and error states
   - Cache results (optional)

2. **UI components:**
   - Search form (if needed for testing)
   - Results display (used by RAG flow)
   - Loading spinner
   - Error message

## Dependencies

### Required
- Story 2.4 (Document Processing Pipeline): Embeddings must exist
- Ollama service running with bge-m3 model

### Optional
- OpenAI API key (fallback for embeddings)
- Monitoring/tracing for performance tracking

## Acceptance Test Plan

### Test Scenarios

**Scenario 1: Basic Vector Search**
- Given: Knowledge base with 10 chunks across 2 documents
- When: Search for "refund policy"
- Then: Return 5 most similar chunks, all with similarity > 0.7

**Scenario 2: RLS Enforcement**
- Given: Two bots in same organization
- When: Search bot A
- Then: Results only include bot A chunks (never bot B)

**Scenario 3: No Results**
- Given: Query with no relevant chunks
- When: Search for "xyz123 gibberish"
- Then: Return empty results array (not error)

**Scenario 4: Performance**
- Given: Knowledge base with 1000 chunks
- When: Execute 10 concurrent searches
- Then: All complete in <200ms p95

**Scenario 5: Large Knowledge Base**
- Given: Bot with 10,000 chunks (100 documents)
- When: Search for common term
- Then: Return top 5 with correct scoring

## Definition of Done

- [ ] Search latency consistently <200ms p95
- [ ] All acceptance criteria tested and passing
- [ ] RLS enforcement verified in tests
- [ ] HNSW index created and tuned
- [ ] Error handling for edge cases
- [ ] API documentation updated
- [ ] Code reviewed and merged to main

## Functional Requirements Covered

- **FR20:** System retrieves relevant context using semantic vector search ✓

## Technical Notes

### Performance Considerations

1. **Embedding Cache:** Consider caching embeddings for frequently searched queries (rare in practice)
2. **Batch Embedding:** For bulk operations, batch embed multiple queries
3. **Index Maintenance:** HNSW index is self-tuning; monitor query latency over time
4. **Scaling:** For 100K+ chunks, consider approximate search or indexing strategy

### pgvector Setup

Ensure PostgreSQL has pgvector extension:
```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

### Fallback Strategy

If Ollama embedding fails:
1. Retry with exponential backoff (3 times)
2. Fallback to OpenAI Embedding API if available
3. Fallback to keyword search as last resort
4. Log error for monitoring

## Risk & Mitigation

| Risk | Mitigation |
|------|-----------|
| Embedding model outage | Fallback to OpenAI API |
| Slow index builds | Pre-build on document import |
| Vector dimension mismatch | Enforce 1024 dim in all code paths |
| Memory exhaustion (large KB) | Monitor vector DB memory, paginate results |

## Dev Agent Record

### Context Reference

<!-- Story context XML will be added by context workflow -->

### Agent Model Used

Claude Haiku 4.5

### Completion Notes List

- Story 3.1 drafted with comprehensive vector search specification
- Tuning parameters provided based on bge-m3 model characteristics
- API contract defined for integration with downstream RAG pipeline
- Performance targets set (200ms p95, <50ms per embedding)
- RLS enforcement integrated throughout architecture
- Fallback strategy for embedding model unavailability

### Debug Log References

### File List

<!-- Will be updated by dev agent during implementation -->

## Change Log

- 2025-12-04: Initial draft created by SM
  - Epic 3 story breakdown from docs/epics.md
  - Complete vector search pipeline specification
  - API contract and tuning parameters included
  - pgvector setup and HNSW index configuration
  - Integration points with document processing and RAG engine

