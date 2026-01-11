# User Research & Domain Research Report: Veriply

**Date:** 2025-11-27  
**Prepared by:** Analyst Mary  
**Research Focus:** User Pain Points, Personas, Industry Standards, and Technology Deep Dive

---

## Part 1: User Research

### 1.1 Executive Summary

Our research reveals a critical "Service-Trust Gap" across Freelancers, SMEs, and Support Teams. Customers demand **instant, accurate responses** (90% expect <10 minute reply), yet businesses lack the tools to deliver. AI chatbots are widely distrusted due to hallucination risks. **Veriply's HITL model directly addresses this gap.**

---

### 1.2 Key Statistics That Validate Veriply

| Statistic | Source | Veriply Implication |
|-----------|--------|---------------------|
| **68%** of customers will pay more for better service | HelpScout | Premium pricing justified if we deliver verified answers |
| **90%** rate "immediate" response (<10 min) as essential | HelpScout | AI speed is mandatory, not optional |
| **69%** try self-service first | HelpScout | Knowledge base + AI is the first line of defense |
| **<33%** of companies offer knowledge bases | HelpScout | Massive gap = opportunity for Veriply |
| **78%** backed out of a purchase due to poor CX | HelpScout | Trust is literally money on the table |
| **45%** call center turnover rate | HelpScout | Humans are expensive and leave. AI doesn't. |
| **77%** say loyalty is tied to service quality | Zendesk | CX is not a cost center—it's a profit center |
| **+219%** messaging channel growth (WhatsApp) | Zendesk | Omnichannel is coming fast |
| **+81%** chatbot interaction growth | Zendesk | Customers accept AI, but demand accuracy |
| **75%** of customers use multiple channels | McKinsey | API-first, channel-agnostic design is critical |

---

### 1.3 User Personas

#### Persona 1: **Freelancer "Fiona"**
- **Profile:** Solo consultant, 5-10 clients, uses email + WhatsApp
- **Pain Points:**
  - Spends 2-3 hours/day on repetitive client questions
  - Can't afford VA or support tool (>€50/month is a stretch)
  - Fears losing clients to slow response times
- **Needs from Veriply:**
  - €0-15/month tier (or free with limits)
  - WhatsApp/email integration
  - "Draft response" mode (she reviews before sending)
- **Quote (Persona):** *"I need a clone of myself that knows my pricing and policies."*

#### Persona 2: **SME Owner "Oscar"**
- **Profile:** E-commerce owner, 3 employees, 50-200 tickets/day
- **Pain Points:**
  - Hired a part-time support agent, but turnover is 45%
  - Competitors have chatbots, but customers hate them
  - Lost sales due to "no answer within 24 hours"
- **Needs from Veriply:**
  - Shopify/WooCommerce integration
  - Verified answers for product availability, shipping, returns
  - Dashboard to monitor AI accuracy
- **Quote (Persona):** *"I don't want a chatbot that makes stuff up. I need one that asks me if it's unsure."*

#### Persona 3: **Support Lead "Sara"**
- **Profile:** IT company, 5-agent team, 500+ tickets/week
- **Pain Points:**
  - Agents waste time on L1 tickets (password resets, FAQs)
  - Knowledge base is outdated, agents don't update it
  - SLA pressure: 4-hour response time, 24-hour resolution
- **Needs from Veriply:**
  - Ticket triage (auto-categorize by priority)
  - "Agent Co-pilot" mode (AI drafts, human sends)
  - Sync with Zendesk/Freshdesk
- **Quote (Persona):** *"My agents should handle complex issues, not copy-paste FAQ answers."*

---

### 1.4 Jobs To Be Done (JTBD) Framework

| Job | Current Solution | Veriply Value |
|-----|------------------|---------------|
| "Help me respond to routine questions instantly" | Manual email, canned responses | AI-drafted, human-verified answers |
| "Help me maintain accuracy across all responses" | Agent training, QA reviews | HITL verification loop |
| "Help me scale support without scaling headcount" | Hiring contractors, outsourcing | AI handles 60-80% of L1 |
| "Help me track what questions we can't answer" | Spreadsheets, gut feel | Uncertainty flagging dashboard |
| "Help me reduce after-hours response gaps" | Out-of-office replies | 24/7 AI with human escalation |

---

### 1.5 User Journey Friction Points

| Stage | Friction | Veriply Solution |
|-------|----------|------------------|
| **Onboarding** | "Setting up AI takes weeks" | 1-click knowledge base import (CSV, URL scrape) |
| **First Query** | "The AI answered wrong immediately" | Uncertainty threshold: "I'm not sure, let me check" |
| **Scaling** | "Works for simple questions, fails on complex" | Human handoff with full context preservation |
| **Trust Building** | "How do I know if the AI is reliable?" | Accuracy dashboard, verified answer count |
| **Long-term** | "Knowledge gets stale" | Auto-flag outdated answers, suggest updates |

---

## Part 2: Technical Deep Dive — Vector Database Comparison

### 2.1 Executive Summary

PostgreSQL + **pgvector + pgvectorscale** now matches or exceeds Pinecone/Qdrant at **75% lower cost**. For Veriply's use case (<1M vectors initially), pgvector is the clear winner due to:
- No additional infrastructure (already using PostgreSQL)
- 28x lower latency than Pinecone s1
- Open source, no vendor lock-in

---

### 2.2 Benchmark Results (50M Vectors, 768 Dimensions)

| Configuration | p95 Latency | Throughput (RPS) | Recall | Monthly Cost |
|---------------|-------------|------------------|--------|--------------|
| **PostgreSQL + pgvectorscale** | 3.5ms | 1,238 | 99% | **~$835** (self-hosted) |
| Pinecone s1 (storage-optimized) | 98ms (28x slower) | 78 | 99% | $3,241 |
| Pinecone p2 (performance-optimized) | 4.9ms | 825 | 90% | $3,889 |
| **Qdrant** | 3.5ms | 1,238 | 99% | ~$800 (self-hosted) |
| Weaviate | 13.9ms | 1,142 | 97% | ~$800 (self-hosted) |
| Milvus | 393ms | 219 | 99% | ~$800 (self-hosted) |
| Elasticsearch | 19.2ms | 717 | 98% | ~$800 (self-hosted) |

**Source:** Timescale Benchmarks (June 2024), Qdrant Benchmarks (January 2024)

---

### 2.3 Key Innovations in pgvectorscale

1. **StreamingDiskANN Index**
   - Stores index on SSD instead of RAM (massively cheaper)
   - Based on Microsoft DiskANN research
   - Same algorithm used by Pinecone internally

2. **Statistical Binary Quantization (SBQ)**
   - Novel compression technique by Timescale
   - Better accuracy than standard Binary Quantization
   - Reduces storage without sacrificing recall

3. **Streaming Filtering**
   - Solves the "HNSW filtering problem" (where filters break accuracy)
   - Critical for Veriply's tag-based search (e.g., "search only in returns policy")

---

### 2.4 Quick Start for Veriply

```sql
-- Enable extensions
CREATE EXTENSION vector;
CREATE EXTENSION vectorscale;

-- Create embeddings table
CREATE TABLE document_embeddings (
    id SERIAL PRIMARY KEY,
    tenant_id UUID NOT NULL,
    document_id UUID REFERENCES documents(id),
    content TEXT,
    embedding vector(1024), -- bge-m3 outputs 1024 dims
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create StreamingDiskANN index (new in pgvectorscale)
CREATE INDEX doc_embedding_idx 
ON document_embeddings 
USING diskann(embedding);

-- Multi-tenant similarity search with metadata filter
SELECT content, metadata, 1 - (embedding <=> $1) AS similarity
FROM document_embeddings
WHERE tenant_id = $2
  AND metadata->>'category' = 'returns'
ORDER BY embedding <=> $1
LIMIT 5;
```

---

### 2.5 When to Consider Alternatives

| Scenario | Recommendation |
|----------|---------------|
| <1M vectors, PostgreSQL already in stack | **pgvector (clear winner)** |
| 1M-10M vectors, need advanced filtering | pgvector + pgvectorscale or Qdrant |
| >100M vectors, multi-region | Pinecone (managed) or Qdrant Cloud |
| Need hybrid search (dense + sparse) | bge-m3 + pgvector (or Qdrant with FastEmbed) |

**For Veriply:** Stick with PostgreSQL + pgvector. Revisit only if we hit 10M+ vectors (which would mean ~10,000 paying customers with large knowledge bases).

---

## Part 3: Domain Research — AI Customer Service Industry Standards

### 3.1 AI Maturity Model (McKinsey)

McKinsey defines 5 levels of AI-driven customer service maturity:

| Level | Description | AI Usage | Example |
|-------|-------------|----------|---------|
| **1** | Manual, paper-based, high-touch | 0% | Traditional call center |
| **2** | Digital channels, basic IVR | 10-20% | Email + phone routing |
| **3** | Self-service portals, chatbots | 40-60% | FAQ bots, ticket forms |
| **4** | AI-assisted agents, proactive outreach | 70-80% | Agent co-pilots, sentiment analysis |
| **5** | Fully proactive, 95%+ AI/digital | 95%+ | E-commerce leaders (Amazon) |

**Veriply Target:** Help customers reach **Level 4** (AI-assisted human agents). Level 5 is achievable for transactional queries only.

---

### 3.2 Industry Transformation Results (McKinsey Case Study)

An Asian bank achieved the following after AI-enabled customer service transformation:

| Metric | Before | After | Change |
|--------|--------|-------|--------|
| Self-service channel usage | Baseline | 2-3x | +100-200% |
| Service interactions | Baseline | -40-50% | -40-50% |
| Cost-to-serve | Baseline | -20%+ | -20%+ |
| Incidence on assisted channels | Baseline | -20-30% | -20-30% |

**Key Enablers:**
1. API-driven tech stack (Veriply's architecture)
2. Speech and sentiment analytics (future roadmap)
3. Real-time SLA tracking (dashboard feature)
4. Integrated operating model (service + business + product alignment)

---

### 3.3 Customer Expectations by Channel (Zendesk 2025 Trends)

| Channel | Growth (2023-2024) | Customer Expectation |
|---------|-------------------|----------------------|
| WhatsApp | **+219%** | Instant, conversational |
| Other Messaging | +21% | 15-min response |
| Chat/Bots | +81% | Immediate, 24/7 |
| Email | Flat | 4-24 hour response |
| Phone | -8% | Still preferred for complex issues |

**Veriply Priority:** WhatsApp/Telegram > Webchat > Email. Phone is out of scope for MVP.

---

### 3.4 SLA Best Practices

Industry-standard SLAs for B2B SaaS support:

| Priority | First Response | Resolution | Example |
|----------|---------------|------------|---------|
| P1 (Critical) | 15 min | 4 hours | System down |
| P2 (High) | 1 hour | 8 hours | Feature broken |
| P3 (Medium) | 4 hours | 24 hours | Bug, workaround exists |
| P4 (Low) | 24 hours | 72 hours | Feature request |

**Veriply Value Prop:** AI handles P3/P4 instantly (verified from knowledge base). P1/P2 escalate to human with full context.

---

### 3.5 Compliance and Trust Considerations

| Regulation | Requirement | Veriply Approach |
|------------|-------------|------------------|
| **GDPR (EU)** | Data minimization, right to deletion | Multi-tenant isolation, data retention controls |
| **AI Act (EU 2025)** | Transparency for AI systems | Clearly label AI-generated responses |
| **HIPAA (US Healthcare)** | PHI protection | Future: Encrypted embeddings, audit logs |
| **SOC 2 Type II** | Security controls | Future: Enterprise tier requirement |

**Key Insight:** The EU AI Act (effective 2025-2026) will require transparency about AI usage. Veriply's HITL model is inherently compliant ("This response was verified by a human").

---

## Part 4: Strategic Recommendations

### 4.1 Product Roadmap Priorities (Research-Driven)

| Priority | Feature | Research Justification |
|----------|---------|------------------------|
| 1 | WhatsApp integration | +219% channel growth, 90% expect <10 min |
| 2 | Uncertainty dashboard | 78% abandon due to poor CX, trust is revenue |
| 3 | pgvector-based RAG | 75% cheaper than Pinecone, same performance |
| 4 | Freelancer tier (<€15/month) | Massive underserved market, <33% have KB |
| 5 | Zendesk/Freshdesk sync | Support teams need existing workflow integration |

### 4.2 Competitive Positioning

| Competitor | Weakness | Veriply Differentiator |
|------------|----------|------------------------|
| Intercom Fin | $0.99/resolution, no verification | Flat-rate, verified answers |
| Zendesk AI | Enterprise-only, complex setup | SME-friendly, 1-click import |
| Chatbase | No HITL, hallucination risk | Every answer is verifiable |
| Dante AI | No uncertainty detection | "I'm not sure" fallback |

### 4.3 Go-to-Market Implications

1. **Lead with Trust:** Marketing should emphasize "Verified Intelligence" over "AI-powered"
2. **Target Freelancers First:** Low CAC, viral potential, validate messaging
3. **Case Study Goal:** "Veriply reduced support response time by 80% with 0 incorrect answers"
4. **Avoid:** Generic chatbot positioning, per-resolution pricing, "replace your team" messaging

---

## Appendix: Data Sources

1. **HelpScout Customer Service Statistics (2024-2025)** - 107 statistics on CX, ROI, and channel preferences
2. **Zendesk CX Trends Report (2025)** - 7 key trends including +219% WhatsApp growth
3. **McKinsey: AI-Enabled Customer Service (2023)** - 5-level maturity model, Asian bank case study
4. **Timescale: pgvector vs Pinecone Benchmarks (June 2024)** - 50M vector performance comparison
5. **Qdrant Vector Database Benchmarks (January 2024)** - Multi-database comparison at various precision levels

---

*This research document should be referenced during architecture decisions, product roadmap planning, and marketing strategy development.*
