# Epic 3: RAG Q&A Engine - Complete Story Set

**Created:** 2025-12-04  
**Scope:** 5 stories covering semantic search, answer generation, citations, confidence scoring, and PII redaction  
**Status:** All stories drafted and ready-for-dev  
**Location:** `/docs/sprint-artifacts/epic-3/`

## Overview

Epic 3 implements the core RAG (Retrieval-Augmented Generation) engine that powers Veriply's AI responses. This epic transforms raw user queries into accurate, cited, and confidence-scored answers based on organization knowledge bases.

## Stories Created

### Story 3.1: Semantic Vector Search
**Status:** ready-for-dev | **Blocked by:** 2-4-document-processing-pipeline

Retrieves relevant document chunks for user queries using pgvector similarity search.

**Key Features:**
- bge-m3 embeddings (1024 dimensions)
- pgvector HNSW index for fast search
- RLS enforcement (tenant/bot isolation)
- <200ms p95 latency target
- Top-K retrieval (K=5 default)

**Technical:** PostgreSQL + pgvector, SQLAlchemy, async architecture

---

### Story 3.2: Context-Only Answer Generation
**Status:** ready-for-dev | **Blocked by:** 3-1-semantic-vector-search

Generates AI answers using ONLY retrieved context, preventing hallucinations.

**Key Features:**
- Low temperature (0.1) for determinism
- Qwen 2.5 14B via Ollama (fallback to OpenAI GPT-4o-mini)
- Streaming responses (SSE, Server-Sent Events)
- <500ms first token, <3s total response
- Graceful handling of insufficient context

**Technical:** Ollama integration, FastAPI streaming, prompt engineering

---

### Story 3.3: Citation Generation
**Status:** ready-for-dev | **Blocked by:** 3-2-context-only-answer-generation

Adds source citations to every answer for verification and trust.

**Key Features:**
- Sentence-level citation matching
- Inline and footnote formats
- Clickable citations linking to source chunks
- Confidence levels for citation quality
- Detection of missing/unsupported statements

**Technical:** Semantic matching, spacy NLP, HTML markup generation

---

### Story 3.4: Confidence Scoring & Routing
**Status:** ready-for-dev | **Blocked by:** 3-3-citation-generation

Calculates confidence for each answer to determine if it needs HITL review.

**Key Features:**
- Three-component formula (retrieval, generation, context coverage)
- 40/30/30 weighting
- Auto-send threshold (configurable, default 80%)
- Low-confidence → HITL queue routing
- Verified KB answers always high confidence (95%)

**Technical:** Confidence calculation service, database logging, HITL integration

---

### Story 3.5: PII Redaction
**Status:** ready-for-dev | **Blocked by:** 3-2-context-only-answer-generation

Detects and redacts sensitive information before LLM processing.

**Key Features:**
- Two-tier detection (regex + Microsoft Presidio NER)
- Supports: emails, phones, SSN, credit cards, IPs, URLs, names
- AES-256-GCM encryption for original queries
- Audit logging for support access
- <100ms redaction latency

**Technical:** Microsoft Presidio, cryptography, encryption key management

---

## Story Interdependencies

```
3-1: Semantic Vector Search
    ↓
3-2: Context-Only Answer Generation  ← 3-5: PII Redaction (parallel)
    ↓
3-3: Citation Generation
    ↓
3-4: Confidence Scoring & Routing
```

**Implementation Sequence:**
1. Start: 3-1 (Vector Search) - depends on Story 2.4 (embeddings)
2. Start: 3-5 (PII Redaction) - independent, can run in parallel
3. Then: 3-2 (Answer Generation) - requires 3-1 and 3-5
4. Then: 3-3 (Citations) - requires 3-2
5. Then: 3-4 (Confidence) - requires 3-3

**Parallel Work Possible:**
- 3-1 and 3-5 can be developed simultaneously by different devs
- 3-2 and 3-3 can start once 3-1 is complete
- All integrate through 3-4 (confidence routing)

## File Structure

```
docs/sprint-artifacts/epic-3/
├── story-3-1-semantic-vector-search.md
├── story-3-2-context-only-answer-generation.md
├── story-3-3-citation-generation.md
├── story-3-4-confidence-scoring-routing.md
└── story-3-5-pii-redaction.md
```

## Functional Requirements Coverage

| Requirement | Story | Details |
|-------------|-------|---------|
| FR20 | 3-1 | Semantic vector search retrieval |
| FR21 | 3-2 | Context-only answer generation |
| FR22 | 3-3 | Citation generation |
| FR23 | 3-4 | Confidence scoring (0-100%) |
| FR24 | 3-4 | Verified KB priority |
| FR25 | 3-2 | Refuse out-of-domain questions |
| FR26 | 3-5 | PII redaction before LLM |

**Total Coverage:** 7/7 FR requirements (100% of Epic 3)

## Key Technologies

- **Vector DB:** PostgreSQL + pgvector
- **Search:** HNSW index for approximate nearest neighbor search
- **Embeddings:** bge-m3 (1024 dims) via Ollama
- **LLM:** Qwen 2.5 14B (local) with OpenAI fallback
- **Streaming:** Server-Sent Events (SSE)
- **NLP:** spacy for sentence segmentation
- **PII Detection:** Microsoft Presidio + regex patterns
- **Encryption:** AES-256-GCM for sensitive data

## Development Milestones

**Phase 1: Vector Infrastructure** (Story 3-1)
- pgvector setup and index creation
- Embedding model integration
- Search API endpoint

**Phase 2: AI Foundation** (Story 3-2, 3-5)
- LLM integration (Ollama/OpenAI)
- Streaming response generation
- PII detection and encryption

**Phase 3: Trust & Transparency** (Story 3-3, 3-4)
- Citation post-processing
- Confidence scoring algorithm
- HITL routing integration

## Success Criteria

✅ All 5 story files created with comprehensive specifications  
✅ Stories marked "ready-for-dev" in sprint-status.yaml  
✅ Epic marked "contexted" in sprint-status.yaml  
✅ All FRs (FR20-FR26) mapped to stories  
✅ Technical specifications detailed for each story  
✅ API contracts defined  
✅ Database schemas specified  
✅ Implementation tasks outlined  
✅ Acceptance test plans included  
✅ Risk mitigation documented  

## Next Steps

1. **Assign Stories:**
   - 3-1 (Vector Search) → Backend engineer
   - 3-5 (PII Redaction) → Backend engineer (parallel)
   - 3-2 (Answer Gen) → Backend/ML engineer
   - 3-3 (Citations) → Backend engineer
   - 3-4 (Confidence) → Backend engineer

2. **Unblock Dependencies:**
   - Ensure Story 2-4 (Document Processing) is progressing
   - 3-1 can start once 2-4 embeddings are available

3. **Start Development:**
   - Recommend starting 3-1 and 3-5 first (independent)
   - Then 3-2 once 3-1 complete
   - Then 3-3 → 3-4 in sequence

4. **Technical Setup:**
   - Verify pgvector extension in PostgreSQL
   - Setup Ollama with bge-m3 and Qwen models
   - Microsoft Presidio installation
   - Encryption key management system

## Document Statistics

| File | Lines | Sections | Specs |
|------|-------|----------|-------|
| 3-1 | ~400 | 12 | Vector search, HNSW, API |
| 3-2 | ~380 | 11 | Prompt eng, streaming, LLM config |
| 3-3 | ~350 | 10 | Citation matching, HTML, UI |
| 3-4 | ~380 | 12 | Confidence formula, routing, DB |
| 3-5 | ~420 | 12 | PII detection, encryption, audit |
| **Total** | **~1,930** | **57** | **All specs included** |

## Contact & Questions

- **Epic Owner:** TBD (recommended: Lucas or Soulaymane for RAG)
- **SM/Reviewer:** Dario
- **Location:** `docs/sprint-artifacts/epic-3/`
- **Status:** Ready for team review and story assignment

---

## Appendix: Specification Highlights

### Architecture Pattern (All Stories)
- **Input Validation:** RLS enforcement (tenant/bot scoping)
- **Processing:** Async where applicable
- **Output:** Structured responses with metadata
- **Error Handling:** Graceful degradation, fallbacks

### Performance Targets
- Vector search: <200ms p95
- Embedding: ~20ms (local)
- Answer gen first token: <500ms
- Full answer: <3s
- PII redaction: <100ms
- Confidence calc: <50ms

### Quality Standards
- No hallucinations (temperature 0.1)
- High citation accuracy (>95%)
- Calibrated confidence (80% = correct)
- PII detection: High precision
- Latency targets met in 95% of requests

### Security & Privacy
- RLS enforcement throughout
- Encryption for sensitive queries
- No PII to external LLMs
- Audit logging for compliance
- Data isolation per tenant/bot

