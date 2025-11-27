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

**AI Trust & Safety:**
*   **Strict Guardrails:** System must refuse to answer out-of-domain questions.
*   **Citation:** Every AI answer must cite the source document.
*   **Confidence Scores:** Every answer must have a confidence score; low-confidence answers trigger HITL.

**Compliance:**
*   **GDPR/CCPA:** System must support "Right to be Forgotten" (deleting user data from vector stores).
*   **Malware Scanning:** All uploads must be scanned before processing.
*   **Audit Logs:** All AI actions and Human approvals must be logged.

---

## Innovation & Novel Patterns

**Internal HITL as a Feature:**
Turning the "bug" of AI hallucination into a feature by making the verification process the core value proposition.

**Hybrid Tech Stack Strategy:**
*   **Embeddings:** Open-Source (`all-MiniLM-L6-v2`) for cost efficiency and privacy.
*   **LLM:** Hybrid approach—OpenAI (GPT-4o-mini) for MVP speed, migrating to Self-Hosted (Qwen-2.5 14B) for scale and privacy.

---

## SaaS B2B Specific Requirements

### Multi-Tenancy Architecture
*   **Logical Separation:** Row-level security (RLS) in PostgreSQL.
*   **Bot Isolation:** Tenants can have multiple Bots; Documents are assigned to specific Bots or Groups.

### Permissions & Roles (RBAC)
*   **Admin:** Manage billing, integrations, users.
*   **Knowledge Manager:** Can approve/reject AI answers, manage documents.
*   **Support Agent:** Can use the HITL dashboard, review drafts.
*   **Viewer:** Read-only access to analytics.

### Subscription Tiers
*   **Starter:** Shared infrastructure, basic RAG, limited documents.
*   **Pro:** Higher limits, advanced analytics, priority support.
*   **Enterprise:** Dedicated vector isolation, SLA, custom integrations.

### Integrations
*   **Sources:** PDF, Email, Sharepoint/OneDrive, GoogleDrive, Notion, Web Scraper.
*   **Destinations:** Zendesk, Intercom, Email (SMTP/IMAP).

---

## User Experience Principles

*   **Trust-First Design:** Internal UI (for Agents/Admins) must clearly distinguish between "AI Generated" (Unverified) and "Human Verified" content using color coding (e.g., Amber vs. Green). End-users see a seamless experience.
*   **Agent-Centric:** The HITL Dashboard is a productivity tool, not a chat toy. Keyboard shortcuts for Approve/Reject/Edit.
*   **Transparency:** Always show *why* the AI gave an answer (citations).

### Key Interactions
*   **One-Click Verification:** Agent sees AI draft -> Clicks "Approve" -> Answer is sent AND saved to Verified KB.
*   **Diff View:** When an agent edits an AI draft, show the "Diff" to learn *what* was changed (tone? fact? formatting?).

---

## Functional Requirements

**User & Tenant Management**
*   FR1: Users can register and create a new tenant organization.
*   FR2: Admins can invite team members and assign roles (Admin, Manager, Agent).
*   FR3: System must enforce strict data isolation between tenants.

**Knowledge Ingestion**
*   FR4: Users can upload documents (PDF, Markdown, TXT) for indexing.
*   FR5: Users can connect external data sources (Notion, Web URL) for periodic syncing.
*   FR6: Users can import historical email archives (via IMAP or file upload) to populate the knowledge base.
*   FR7: System must automatically chunk and embed ingested content into the vector store.
*   FR8: Users can manually delete or update specific documents.
*   FR21: System must support document versioning (v1, v2) and rollback.
*   FR22: System must scan all uploads for malware.

**RAG & Q&A Engine**
*   FR9: System can retrieve relevant context for a user query using semantic search.
*   FR10: System can generate a natural language answer based *only* on retrieved context.
*   FR11: System must provide citations (source document + page/section) for every answer.
*   FR12: System must redact PII from queries before sending to the LLM.

**HITL Dashboard (Agent Workflow)**
*   FR13: Agents can view a queue of "Pending Review" AI drafts (for emails or low-confidence chats).
*   FR14: Agents can edit the AI draft before approving.
*   FR15: Agents can "Approve" a draft, which sends it to the user and adds it to the Verified KB.
*   FR16: Agents can "Reject" a draft, providing a reason (e.g., "Hallucination", "Wrong Tone").
*   FR23: System must support OAuth2 for Gmail/Outlook integration.
*   FR24: System must generate email drafts matching the user's historical style/tone.

**Verified Knowledge Base**
*   FR17: System maintains a separate index of "Verified Q&A Pairs" (Golden Dataset).
*   FR18: Incoming queries are checked against the Verified KB *first* (Exact/Semantic match) before generating a new answer.

**Analytics**
*   FR19: Admins can view dashboard metrics: Total Queries, Deflection Rate, Average Response Time.
*   FR20: Admins can view "Hallucination Rate" (based on Agent Rejections).

---

## Non-Functional Requirements

### Performance
*   **Latency:** Vector search < 200ms. LLM Generation < 3s (Streamed).
*   **Throughput:** Support 100 concurrent queries per tenant (Pro tier).

### Security
*   **Encryption:** AES-256 for data at rest (DB + Vector Store). TLS 1.3 for data in transit.
*   **PII:** Automatic redaction of sensitive entities.
*   **Access Control:** MFA support for Admin accounts.

### Scalability
*   **Vector Store:** Must scale to millions of vectors (pgvector with IVFFlat/HNSW indexing).
*   **Stateless API:** Backend services must be stateless to allow horizontal scaling.

### Integration
*   **API First:** All functionality exposed via REST API.
*   **Webhooks:** Support webhooks for "New Answer Ready" or "Review Needed" events.

---

_This PRD captures the essence of Veriply - A Trust-First Knowledge Platform._

_Created through collaborative discovery between Dario and AI facilitator._
