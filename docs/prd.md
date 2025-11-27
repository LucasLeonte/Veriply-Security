# Veriply - Product Requirements Document

**Author:** Dario  
**Date:** 2025-11-27  
**Version:** 1.0

---

## Executive Summary

Veriply is a **Trust-First AI Customer Service & Knowledge Automation Platform** that bridges the critical "Service-Trust Gap" in the market. While 90% of customers expect responses in under 10 minutes and 68% will pay more for better service, businesses—from solo entrepreneurs to enterprise sales teams—lack affordable, trustworthy tools to deliver both speed and accuracy.

Unlike existing chatbots that "hallucinate" and erode trust (Chatbase, Dante AI) or enterprise solutions that are prohibitively expensive (Zendesk at €155/agent/month), Veriply implements a **Human-in-the-Loop (HITL) verification system** where low-confidence answers are routed to humans for validation, then fed back into the AI's knowledge base. This creates a self-improving system that gets smarter with every interaction while guaranteeing accuracy.

The platform serves three core use cases:
1. **RAG-based Q&A** from company documentation with source citations
2. **Email draft automation** matching the user's writing style
3. **Internal knowledge retrieval** for sales/support teams needing instant verified answers

Targeting a $12B → $44.7B market (20%+ CAGR), Veriply positions itself as **"Verified Intelligence"**—not just another AI chatbot, but a trust layer for business communication.

### What Makes This Special

**Verified Intelligence:** The core differentiator is turning AI's greatest weakness (hallucination) into a strength. Every uncertain answer triggers *"I'm not sure, let me check"* instead of confident guessing. Human corrections feed back into a **Verified Knowledge Base** that grows more reliable over time.

**The Trust Loop:**
1. AI drafts response with confidence score (0-100%)
2. Low confidence → Human reviews, corrects, approves
3. Correction feeds back → AI learns from every interaction
4. Eventually: High-confidence answers auto-send with 100% accuracy guarantee

The result: customers trust the bot because they know it won't make things up.

---

## Project Classification

**Technical Type:** SaaS B2B Platform  
**Domain:** Customer Service Automation (AI/ML)  
**Complexity:** High

### Why High Complexity

| Factor | Complexity Driver |
|--------|-------------------|
| **Multi-Tenancy** | Row-level security, bot isolation, data sovereignty |
| **RAG Pipeline** | Vector search, confidence scoring, HITL workflow |
| **Email Integration** | OAuth2, style matching, draft queue management |
| **Compliance** | GDPR (Right to be Forgotten), EU AI Act (transparency), PII handling |
| **Real-time Scale** | Sub-200ms vector search, streaming LLM responses |

### Domain Context

The Customer Service AI domain requires handling sensitive user data while providing accurate information. The "AI Trust" aspect adds complexity:
- **Hallucination Risk:** AI making up facts damages customer relationships (78% abandon due to poor service)
- **Data Leakage:** Multi-tenant systems must prevent cross-contamination
- **Compliance:** GDPR mandates Right to be Forgotten (deleting from vector stores), EU AI Act requires AI response transparency

---

## Success Criteria

### North Star Metric
**Time saved per user per week while maintaining 0 incorrect verified answers.**

### Product Success Metrics

| Criteria | Target | Rationale |
|----------|--------|-----------|
| **Trust Guarantee** | 0 incorrect verified answers | Core value prop—if HITL fails, Veriply fails |
| **Time Liberation** | 5+ hours saved/week per user | Quantifiable ROI for marketing |
| **Learning Velocity** | <20% HITL intervention after 30 days | Proves AI actually learns from corrections |
| **Response Speed** | <3s chat, <30s email draft | Meets "instant" expectation (90% want <10min) |
| **Agent Productivity** | 10x faster review than writing | 30 seconds vs 5 minutes = competitive edge |

### Business Metrics

| Metric | Target | Why It Matters |
|--------|--------|----------------|
| **Activation Rate** | >80% complete onboarding | Upload doc → Ask question → Get answer with source |
| **90-Day Retention** | >60% | Proves ongoing value beyond novelty |
| **Trust Score** | >95% thumbs-up ratio | Users trust AI answers |
| **Free → Paid Conversion** | >5% | Sustainable unit economics |
| **Customer Churn** | <5% monthly | Trust is the retention driver |
| **Deflection Rate** | 40%+ queries auto-resolved | ROI justification for customers |

---

## Product Scope

### MVP - Minimum Viable Product

**Core Value Delivery:**

| # | Feature | Description | Why Essential |
|---|---------|-------------|---------------|
| 1 | **RAG Q&A Engine** | Retrieval-augmented generation using PostgreSQL + pgvector | Core functionality—answer questions from docs |
| 2 | **Multi-Bot Architecture** | Users create multiple bots with isolated knowledge bases | Enables "HR Bot" vs "Sales Bot" separation |
| 3 | **HITL Dashboard** | Agent interface to review, edit, approve AI drafts | Core differentiator—the trust layer |
| 4 | **Verified Knowledge Base** | High-trust index of approved Q&A pairs | Learning loop—AI improves from corrections |
| 5 | **Email Automation** | OAuth2 Gmail/Outlook integration for draft generation | Primary use case for SME personas |
| 6 | **PII Redaction** | Auto-detect and mask sensitive data before LLM | Safety requirement—prevents data leakage |
| 7 | **Basic Analytics** | Query volume, deflection rate, correction metrics | Prove ROI to customers |
| 8 | **Multi-Tenant Auth** | User registration, org creation, RBAC, data isolation | SaaS foundation |

**MVP User Journey:**
```
Upload docs → Create bot → Ask question → Get answer with citation
                                              ↓
                              Low confidence? → HITL review → Approve → Verified KB
                                              ↓
                              High confidence? → Auto-respond (with user consent)
```

### Post-MVP (v1.1)

| Feature | Description | Why Deferred |
|---------|-------------|--------------|
| **Document Versioning** | Version control with rollback | Nice-to-have, not blocking core value |
| **Malware Scanning** | Scan uploads before processing | Can use basic file validation initially |
| **External Data Sources** | Notion, SharePoint, Google Drive sync | Complex integrations, web upload works |
| **Web Scraping** | Import from URLs | Can manually upload content initially |

### Growth Features (v2.0)

| Feature | Description | Market Signal |
|---------|-------------|---------------|
| **WhatsApp/Messenger** | Multi-channel support | +219% messaging growth (Zendesk) |
| **Proactive FAQ Generation** | AI suggests new articles from chat history | Reduces knowledge gaps |
| **Slack Integration** | Internal team knowledge access | Support team persona (Sara) |
| **Advanced Task Automation** | AI executes actions (booking, CRM updates) | Enterprise tier feature |

### Vision (Future)

| Feature | Description | Maturity Level |
|---------|-------------|----------------|
| **Fully Autonomous Agent** | 90%+ queries auto-resolved with human accuracy | McKinsey Level 5 |
| **Predictive Support** | Detect and resolve issues before users report | Proactive AI |
| **Voice Interface** | Telephony integration | Different tech stack, low priority |
| **On-Premise Deployment** | Self-hosted option for enterprise | Data sovereignty requirement |

---

## Domain-Specific Requirements

### AI Trust & Safety

| Requirement | Implementation | Why Critical |
|-------------|----------------|--------------|
| **Strict Guardrails** | System refuses out-of-domain questions with "I don't have information about that" | Prevents hallucination on unknown topics |
| **Mandatory Citations** | Every AI answer includes source document + section reference | Users can verify accuracy themselves |
| **Confidence Scoring** | 0-100% score on every response; threshold triggers HITL | Core mechanism for trust guarantee |
| **"I'm Not Sure" Response** | Low confidence → explicit uncertainty message | Differentiator vs competitors who guess |
| **Context-Only Generation** | LLM generates answers *only* from retrieved context, never general knowledge | Eliminates fabrication risk |

### Compliance Requirements

| Regulation | Requirement | Implementation |
|------------|-------------|----------------|
| **GDPR (EU)** | Right to be Forgotten | Delete user data from PostgreSQL AND vector embeddings |
| **GDPR (EU)** | Data Minimization | Only store necessary PII; redact before LLM |
| **EU AI Act (2025)** | Transparency | Clearly label AI-generated content; disclose AI usage |
| **GDPR (EU)** | Data Portability | Export user's knowledge base and Q&A history |
| **General** | Audit Trail | Log all AI actions, human approvals, and data access |

### Data Safety

- **PII Redaction:** Auto-detect and mask emails, phone numbers, addresses before sending to LLM
- **Tenant Isolation:** Row-Level Security (RLS) in PostgreSQL; no cross-tenant data leakage
- **Upload Validation:** File type validation, size limits (25MB), basic safety checks

---

## Innovation & Novel Patterns

### Internal HITL as Core Feature

Traditional approach: AI answers → User complains → Retrain model (reactive)

**Veriply approach:** AI drafts → Human verifies → Approved answer stored → AI learns (proactive)

```
┌─────────────────────────────────────────────────────────────┐
│                    THE TRUST LOOP                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   Query → Semantic Search → Check Verified KB first         │
│                    ↓                                        │
│            ┌──────┴──────┐                                  │
│            │ Match found │ → Return verified answer (100%)  │
│            └──────┬──────┘                                  │
│                   │ No match                                │
│                   ↓                                        │
│         Generate from RAG → Confidence score               │
│                    ↓                                        │
│            ┌──────┴──────┐                                  │
│            │ High (>80%) │ → Auto-respond (user consent)   │
│            └──────┬──────┘                                  │
│                   │ Low (<80%)                             │
│                   ↓                                        │
│         Route to HITL → Human reviews → Approves/Edits     │
│                    ↓                                        │
│         Add to Verified KB → Future queries use this       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Hybrid Tech Stack Strategy

| Component | MVP Choice | Scale Choice | Rationale |
|-----------|------------|--------------|-----------|
| **Embeddings** | bge-m3 (via Ollama) | bge-m3 (self-hosted) | Multilingual, 1024 dims, open source |
| **LLM** | Qwen 2.5 14B (Ollama) | Qwen 2.5 14B or DeepSeek V3 | Privacy, cost, EU data sovereignty |
| **Vector DB** | PostgreSQL + pgvector | pgvector + pgvectorscale | 75% cheaper than Pinecone, same performance |
| **Fallback LLM** | OpenAI GPT-4o-mini | DeepSeek V3 API | Reliability for complex queries |

**Why Self-Hosted First:**
- Zero per-token API costs
- Data never leaves infrastructure (GDPR selling point)
- EU customers concerned about US cloud providers
- Technical research shows Qwen 2.5 matches GPT-4o-mini quality

---

## SaaS B2B Specific Requirements

### Multi-Tenancy Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    TENANT ISOLATION                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   Tenant A                    Tenant B                      │
│   ┌─────────────────┐        ┌─────────────────┐           │
│   │ Organization    │        │ Organization    │           │
│   │   ├── Bot 1     │        │   ├── Bot 1     │           │
│   │   │   └── Docs  │        │   └── Docs      │           │
│   │   └── Bot 2     │        │                 │           │
│   │       └── Docs  │        │                 │           │
│   └─────────────────┘        └─────────────────┘           │
│          ↓                          ↓                       │
│   RLS Policy: tenant_id = current_tenant()                 │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

- **Logical Separation:** Row-level security (RLS) in PostgreSQL on all tables
- **Bot Isolation:** Documents belong to specific Bots; Bots belong to Organizations
- **Query Scoping:** All vector searches filtered by tenant_id AND bot_id

### Permissions & Roles (RBAC)

| Role | Permissions | Use Case |
|------|-------------|----------|
| **Owner** | Full access, billing, delete org | Account creator |
| **Admin** | Manage users, integrations, settings | IT administrator |
| **Knowledge Manager** | Approve/reject answers, manage docs, view analytics | Content lead |
| **Support Agent** | Use HITL dashboard, review drafts | Daily operator |
| **Viewer** | Read-only analytics access | Stakeholder reporting |

### Subscription Tiers

| Tier | Target Persona | Key Limits | Price Point |
|------|----------------|------------|-------------|
| **Free** | Fiona (Freelancer) | 1 bot, 50 docs, 100 queries/mo | €0 |
| **Starter** | Oscar (SME) | 3 bots, 500 docs, 1K queries/mo | €29/mo |
| **Pro** | Sara (Support Team) | 10 bots, 2K docs, 10K queries/mo, team seats | €99/mo |
| **Enterprise** | Large orgs | Unlimited, dedicated infra, SLA, SSO | Custom |

---

## User Experience Principles

### Trust-First Design

| Principle | Implementation |
|-----------|----------------|
| **Visual Trust Signals** | Amber badge = "AI Generated (Unverified)" / Green badge = "Human Verified" |
| **Source Transparency** | Every answer shows: "Based on [Document Name, Section X]" |
| **Confidence Display** | Show confidence % to agents (not end-users) |
| **Uncertainty Honesty** | "I'm not sure about this—let me check" instead of guessing |

### Agent-Centric HITL Dashboard

The HITL Dashboard is a **productivity tool**, not a chat interface:

| Feature | Purpose |
|---------|---------|
| **Keyboard Shortcuts** | `A` = Approve, `R` = Reject, `E` = Edit, `N` = Next |
| **Side-by-Side View** | Query + Retrieved Chunks + AI Draft in one screen |
| **Diff View on Edit** | When agent edits, show what changed (tone? fact? formatting?) |
| **Bulk Actions** | Select multiple similar drafts, approve/reject together |
| **Queue Prioritization** | Oldest first, or by customer tier |

### Key Interactions

1. **One-Click Verification:** Agent sees AI draft → Clicks "Approve" → Answer sent AND saved to Verified KB
2. **Quick Edit Flow:** Agent tweaks draft → System learns the correction pattern
3. **Rejection with Reason:** Agent rejects → Selects reason (Hallucination, Wrong Tone, Outdated) → Feeds analytics
4. **Confidence Threshold Setting:** User configures "Auto-send if >X% confidence"

---

## Functional Requirements

### User & Tenant Management

| ID | Requirement | MVP |
|----|-------------|-----|
| FR1 | Users can register with email/password or OAuth (Google, Microsoft) | ✅ |
| FR2 | Users can create a new tenant organization during registration | ✅ |
| FR3 | Admins can invite team members via email and assign roles (Owner, Admin, Manager, Agent, Viewer) | ✅ |
| FR4 | Users can update their profile information and notification preferences | ✅ |
| FR5 | System enforces strict data isolation between tenants using Row-Level Security | ✅ |
| FR6 | Admins can remove team members from the organization | ✅ |

### Bot Management

| ID | Requirement | MVP |
|----|-------------|-----|
| FR7 | Users can create multiple bots within their organization | ✅ |
| FR8 | Users can configure bot settings: name, description, confidence threshold | ✅ |
| FR9 | Users can set the auto-respond confidence threshold (e.g., "Auto-send if >80%") | ✅ |
| FR10 | Users can delete a bot and all associated documents/embeddings | ✅ |
| FR11 | Users can duplicate a bot configuration (without documents) | ✅ |
| FR12 | Bots are isolated: documents and queries are scoped to their assigned bot | ✅ |

### Knowledge Ingestion

| ID | Requirement | MVP |
|----|-------------|-----|
| FR13 | Users can upload documents (PDF, DOCX, TXT, MD, CSV) up to 25MB per file | ✅ |
| FR14 | System automatically chunks documents into semantic segments | ✅ |
| FR15 | System generates embeddings for each chunk using bge-m3 model | ✅ |
| FR16 | System stores embeddings in PostgreSQL + pgvector with tenant/bot scoping | ✅ |
| FR17 | Users can view list of uploaded documents with status (processing, ready, failed) | ✅ |
| FR18 | Users can delete specific documents and their associated embeddings | ✅ |
| FR19 | Users can re-process a document to update embeddings after edits | ✅ |

### RAG & Q&A Engine

| ID | Requirement | MVP |
|----|-------------|-----|
| FR20 | System retrieves relevant context using semantic vector search | ✅ |
| FR21 | System generates natural language answers based *only* on retrieved context | ✅ |
| FR22 | System provides citations (source document + section) for every answer | ✅ |
| FR23 | System calculates and returns a confidence score (0-100%) for each answer | ✅ |
| FR24 | System checks Verified KB first before generating new answers | ✅ |
| FR25 | System refuses to answer out-of-domain questions with "I don't have information about that" | ✅ |
| FR26 | System redacts detected PII from queries before sending to LLM | ✅ |

### Chat Interface (End-User Facing)

| ID | Requirement | MVP |
|----|-------------|-----|
| FR27 | End-users can interact with bots via a web-based chat interface | ✅ |
| FR28 | Chat displays AI responses with source citations | ✅ |
| FR29 | Chat maintains conversation context for follow-up questions | ✅ |
| FR30 | End-users can provide feedback (thumbs up/down) on answers | ✅ |
| FR31 | Low-confidence responses display "I'm checking with the team" message | ✅ |
| FR32 | Chat interface displays "Verified" badge for answers from Verified KB | ✅ |

### Embeddable Widget

| ID | Requirement | MVP |
|----|-------------|-----|
| FR33 | Users can generate an embeddable JavaScript snippet for their bot | ✅ |
| FR34 | Widget can be customized: colors, position, welcome message | ✅ |
| FR35 | Widget supports domain whitelisting for security | ✅ |
| FR36 | Widget works on desktop and mobile browsers | ✅ |

### HITL Dashboard (Agent Workflow)

| ID | Requirement | MVP |
|----|-------------|-----|
| FR37 | Agents can view a queue of pending review items (low-confidence answers, email drafts) | ✅ |
| FR38 | Queue displays: query, retrieved context, AI draft, confidence score | ✅ |
| FR39 | Agents can approve a draft (sends response, adds to Verified KB) | ✅ |
| FR40 | Agents can edit a draft before approving | ✅ |
| FR41 | Agents can reject a draft with a reason (Hallucination, Wrong Tone, Outdated, Other) | ✅ |
| FR42 | Dashboard supports keyboard shortcuts: A=Approve, R=Reject, E=Edit, N=Next | ✅ |
| FR43 | Agents can filter queue by bot, date, or status | ✅ |

### Email Automation

| ID | Requirement | MVP |
|----|-------------|-----|
| FR44 | Users can connect Gmail accounts via OAuth2 | ✅ |
| FR45 | Users can connect Outlook accounts via OAuth2 | ✅ |
| FR46 | System monitors inbox for new emails matching configured rules | ✅ |
| FR47 | System generates email draft responses based on knowledge base | ✅ |
| FR48 | System matches user's historical writing style/tone in drafts | ✅ |
| FR49 | Email drafts appear in HITL queue for review before sending | ✅ |
| FR50 | Users can configure which email labels/folders to monitor | ✅ |

### Verified Knowledge Base

| ID | Requirement | MVP |
|----|-------------|-----|
| FR51 | System maintains a separate index of verified Q&A pairs (Golden Dataset) | ✅ |
| FR52 | Approved HITL responses automatically add to Verified KB | ✅ |
| FR53 | Users can manually add Q&A pairs to Verified KB | ✅ |
| FR54 | Users can edit or remove entries from Verified KB | ✅ |
| FR55 | Verified KB entries take priority over RAG-generated answers | ✅ |

### Analytics & Reporting

| ID | Requirement | MVP |
|----|-------------|-----|
| FR56 | Dashboard displays: total queries, deflection rate, average response time | ✅ |
| FR57 | Dashboard displays: HITL intervention rate over time | ✅ |
| FR58 | Dashboard displays: rejection reasons breakdown (hallucination vs tone vs outdated) | ✅ |
| FR59 | Dashboard displays: most common unanswered questions (knowledge gaps) | ✅ |
| FR60 | Users can export analytics data as CSV | ✅ |

### Compliance & Data Management

| ID | Requirement | MVP |
|----|-------------|-----|
| FR61 | Users can delete all their data (GDPR Right to be Forgotten) | ✅ |
| FR62 | Users can export their knowledge base and Q&A history (GDPR Data Portability) | ✅ |
| FR63 | System logs all AI actions and human approvals for audit trail | ✅ |
| FR64 | All AI-generated responses are clearly labeled as AI-generated | ✅ |

---

## Non-Functional Requirements

### Performance

| Requirement | Target | Rationale |
|-------------|--------|-----------|
| Vector search latency | <200ms (p95) | Real-time user experience |
| LLM response time | <3s (streamed) | "Instant" expectation threshold |
| Email draft generation | <30s | Background process, less urgent |
| Document processing | <60s for 25MB file | Async, user can continue working |
| Concurrent queries | 100 per tenant (Pro) | Burst handling for busy periods |
| API response time | <500ms (p95) | Responsive dashboard |

### Security

| Requirement | Implementation | Priority |
|-------------|----------------|----------|
| Data at rest encryption | AES-256 for DB + Vector Store | Must-have |
| Data in transit encryption | TLS 1.3 for all connections | Must-have |
| Authentication | JWT tokens, OAuth2 for email | Must-have |
| Password policy | Min 8 chars, complexity requirements | Must-have |
| Session management | Secure cookies, token expiry | Must-have |
| MFA support | TOTP for Admin accounts | Should-have |
| API rate limiting | Per-tenant, per-endpoint limits | Must-have |

### Scalability

| Requirement | Target | Approach |
|-------------|--------|----------|
| Vector store capacity | Millions of vectors per tenant | pgvector with HNSW indexing |
| Horizontal scaling | Stateless API services | Kubernetes-ready containers |
| Database scaling | Read replicas for analytics | PostgreSQL replication |
| File storage | 10TB+ capacity | Object storage (S3-compatible) |

### Reliability

| Requirement | Target | Implementation |
|-------------|--------|----------------|
| Uptime SLA | 99.5% (Pro), 99.9% (Enterprise) | Health checks, auto-recovery |
| Data durability | 99.999999% | Database backups, replication |
| Graceful degradation | Fallback to queue if LLM unavailable | Circuit breaker pattern |
| Error handling | User-friendly error messages | Never expose stack traces |

### Integration

| Requirement | Implementation |
|-------------|----------------|
| API-First design | All functionality via REST API |
| OpenAPI documentation | Auto-generated Swagger docs |
| Webhook support | Events: new_query, review_needed, answer_sent |
| Rate limiting | Tiered by subscription plan |
| CORS support | Configurable allowed origins |

### Observability

| Requirement | Implementation |
|-------------|----------------|
| Application logging | Structured JSON logs |
| Error tracking | Sentry or equivalent |
| Metrics collection | Prometheus-compatible endpoints |
| Tracing | Distributed tracing for RAG pipeline |
| Alerting | Configurable thresholds, PagerDuty/Slack |

---

## Summary

**Total Functional Requirements:** 64  
**MVP Scope:** All 64 FRs marked as MVP ✅

### FR Coverage by Capability Area

| Area | FR Count | IDs |
|------|----------|-----|
| User & Tenant Management | 6 | FR1-FR6 |
| Bot Management | 6 | FR7-FR12 |
| Knowledge Ingestion | 7 | FR13-FR19 |
| RAG & Q&A Engine | 7 | FR20-FR26 |
| Chat Interface | 6 | FR27-FR32 |
| Embeddable Widget | 4 | FR33-FR36 |
| HITL Dashboard | 7 | FR37-FR43 |
| Email Automation | 7 | FR44-FR50 |
| Verified Knowledge Base | 5 | FR51-FR55 |
| Analytics & Reporting | 5 | FR56-FR60 |
| Compliance & Data Management | 4 | FR61-FR64 |

---

_This PRD captures the essence of Veriply - A Trust-First AI Knowledge Platform that turns AI's weakness (hallucination) into a strength through Human-in-the-Loop verification._

_Created through collaborative discovery between Dario and AI facilitator._
