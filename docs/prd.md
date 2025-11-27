# Veriply - Product Requirements Document

**Author:** Dario
**Date:** 2025-11-27
**Version:** 1.0

---

## Executive Summary

Veriply is a **Trust-First AI Customer Service & Knowledge Automation Platform** designed to solve the problem of unreliable AI support. Unlike generic chatbots that prioritize speed and conversational fluency, Veriply prioritizes **accuracy and safety**. It empowers support teams to automate responses with confidence by integrating an **Internal Human-in-the-Loop (HITL)** verification layer, ensuring that the AI never hallucinates on critical queries.

### What Makes This Special

**Trust-First RAG Architecture:** The core differentiator is the "Internal HITL" workflow. Instead of unleashing the AI directly on customers with a risk of error, Veriply acts as a "Junior Support Agent" that drafts responses for human review (initially) and learns from every approval, building a "Verified Knowledge Base" that can eventually answer autonomously with 100% certainty.

---

## Project Classification

**Technical Type:** SaaS B2B Platform
**Domain:** Customer Service Automation (AI)
**Complexity:** High (Due to AI Trust, Safety, and PII requirements)

### Domain Context

The Customer Service domain requires handling sensitive user data and providing accurate information. The "AI Trust" aspect adds complexity, requiring strict guardrails against hallucinations (making up facts) and data leakage. Compliance with GDPR (Right to be Forgotten, PII protection) is mandatory.

---

## Success Criteria

1.  **Zero Hallucinations on Verified Answers:** The system must never serve an unverified answer as "truth" without a disclaimer or human check.
2.  **40% Reduction in Ticket Volume:** By automating repetitive queries with high confidence.
3.  **< 2 Second Response Time:** For queries matched against the Verified KB.
4.  **Agent Efficiency:** Support agents should spend < 30 seconds reviewing an AI draft vs. 3-5 minutes writing a response.

### Business Metrics

*   **Customer Churn Rate:** < 5% (Trust is the retention driver).
*   **Deflection Rate:** Percentage of queries resolved without human intervention (post-verification).
*   **MRR Growth:** Driven by "Pro" and "Enterprise" tiers.

---

## Product Scope

### MVP - Minimum Viable Product

1.  **RAG Q&A Engine:** Core retrieval-augmented generation using vector search (PostgreSQL + pgvector).
2.  **Multi-Bot Architecture:** Users can create multiple Bots (e.g., "HR Bot", "Sales Bot") with isolated knowledge bases.
3.  **Internal HITL Dashboard:** A dedicated interface for support agents to review, edit, and approve AI-generated answers.
4.  **Verified Knowledge Base:** A separate, high-trust index of approved Q&A pairs.
5.  **Email Automation:** OAuth2 integration (Gmail/Outlook) to generate drafts for incoming emails.
6.  **Document Versioning:** Automatic version control for uploaded files to ensure freshness.
7.  **PII Redaction:** Automatic detection and masking of sensitive data.
8.  **Basic Analytics:** Dashboard showing query volume, deflection rate, and agent correction actions.

### Growth Features (Post-MVP)

1.  **Proactive FAQ Generation:** AI analyzes chat history to suggest new FAQ articles.
2.  **Multi-Channel Support:** WhatsApp, Messenger, Slack integrations.
3.  **Voice Interface:** Telephony integration for AI voice support.
4.  **Advanced Task Automation:** AI executing actions (e.g., booking appointments).

### Vision (Future)

1.  **Fully Autonomous Agent (Level 5):** AI handles 90% of support with human-level accuracy.
2.  **Predictive Support:** Detecting and resolving user issues before they even report them.

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
