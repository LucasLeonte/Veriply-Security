# Product Brief: Veriply

**Date:** 2025-11-27  
**Author:** Dario  
**Context:** IT Project / Business Venture

---

## Executive Summary

Veriply is an AI-powered customer service and knowledge automation platform that bridges the critical "Service-Trust Gap" in the market. While customers demand instant, accurate responses (90% expect <10 minute replies), businesses — from solo entrepreneurs to enterprise sales teams — lack affordable, trustworthy tools to deliver.

Unlike existing chatbots that "hallucinate" and erode trust, Veriply implements a **Human-in-the-Loop (HITL) verification system** where low-confidence answers are routed to humans for validation, then fed back into the AI's knowledge base. This creates a self-improving system that gets smarter with every interaction while guaranteeing accuracy.

The platform serves three core use cases: (1) RAG-based Q&A from company documentation, (2) automated email draft generation matching the user's writing style, and (3) internal knowledge retrieval for sales/support teams. Targeting a $12B → $44.7B market (20%+ CAGR), Veriply positions itself as "Verified Intelligence" — not just another AI chatbot, but a trust layer for business communication.

---

## Core Vision

### Problem Statement

**The Service-Trust Gap is costing businesses money and time.**

Two real-world scenarios sparked this vision:

1. **The Solo Entrepreneur Trap:** A candy store owner on YouTube does his own customer service because outsourcing is too expensive. He's stuck answering the same questions repeatedly, burning hours that could go into his business.

2. **The Overpromise Problem:** A sales team at a multinational sells products that aren't technically possible, leaving engineers frustrated and customers disappointed. Non-technical people have no way to quickly verify what's feasible without waiting for technical review.

The common thread: **Knowledge is trapped** — in people's heads, in scattered documents, in past emails — and accessing it is either too slow, too expensive, or too unreliable.

### Problem Impact

**For Solo Entrepreneurs & SMEs:**
- 2-3 hours/day lost answering repetitive questions (that's 500+ hours/year)
- 78% of customers abandon purchases due to slow/poor service responses
- Outsourcing support costs €1,500-5,000+/month — unaffordable for small businesses
- 45% turnover rate means constant retraining of support staff

**For Enterprise Teams:**
- Sales teams "guess" when technical verification takes too long → wrong promises made
- Engineers waste time fixing impossible commitments instead of building
- Knowledge lives in people's heads → when they leave, knowledge leaves
- Delayed internal responses slow down the entire sales cycle

**Market Validation:**
- 90% of customers expect responses in <10 minutes
- <33% of companies have knowledge bases — massive gap
- $12B market today → $44.7B by 2028 (20%+ CAGR)

### Why Existing Solutions Fall Short

| Competitor | What They Do | Why They Fail |
|------------|--------------|---------------|
| **Zendesk AI** | Enterprise-grade support platform with AI add-on | ~€155/agent/month, complex setup, overkill for SMEs. AI is a "layer" not the core. |
| **Intercom Fin** | AI chatbot with per-resolution pricing | $0.99/resolution = unpredictable costs. No verification — AI can hallucinate without human check. |
| **Chatbase** | Quick chatbot builder from documents | "Train and pray" approach. No HITL, no uncertainty detection, no email integration. |
| **Dante AI** | Low-cost AI chatbot ($8/month) | Same problem: no confidence scoring, no "I'm not sure" fallback, customers don't trust it. |

**The Gap Veriply Fills:**
- Existing tools are either **too expensive** (Zendesk) or **too risky** (Chatbase/Dante)
- None offer **Human-in-the-Loop verification** as a core feature
- None provide **"I'm not sure, let me check"** — they all guess and hope
- None focus on **email draft generation** matching the user's writing style

### Proposed Solution

**Veriply: Verified Intelligence for Customer Communication**

A platform that combines AI speed with human accuracy:

1. **Knowledge Ingestion Layer**
   - Upload documents (PDF, Word, CSV)
   - Import past emails/chats to learn your communication style
   - Connect to data sources (databases, URLs, OneDrive/SharePoint)
   - AI processes and indexes everything into a searchable knowledge base

2. **RAG-Powered Q&A Engine**
   - User (or customer) asks a question
   - AI searches the knowledge base for relevant information
   - Generates answer with **confidence score** and **source citations**
   - Every answer traceable to specific documents

3. **Human-in-the-Loop Verification**
   - If confidence ≥ threshold → Answer delivered (or drafted for review)
   - If confidence < threshold → "I'm not sure, let me check with the team"
   - Human reviews, corrects if needed, and approves
   - **Correction feeds back into the knowledge base** → AI learns

4. **Multi-Channel Delivery**
   - **Email Integration:** Drafts responses matching your writing style
   - **Chat Widget:** Embed on website for customer self-service
   - **WhatsApp/Messenger:** Meet customers where they are (+219% growth)
   - **Internal Chat:** For sales/support teams to query internal knowledge

5. **Trust & Transparency Dashboard**
   - See how many questions AI answered vs escalated
   - Track confidence score distribution over time
   - Identify knowledge gaps ("These topics have low confidence")
   - Audit trail for compliance (GDPR, EU AI Act)

### Key Differentiators

| Feature | Competitors | Veriply |
|---------|-------------|---------|
| **Accuracy Guarantee** | Hope the AI is right | HITL ensures every answer is verifiable |
| **Uncertainty Handling** | Guess confidently | "I'm not sure" → escalate to human |
| **Pricing Model** | Per-resolution ($0.99 each) or per-agent (€155/mo) | Flat monthly fee with fair usage limits |
| **Email Integration** | Basic or enterprise-only | Core feature with style matching |
| **Learning Loop** | Retrain on better docs (reactive) | Every human correction improves AI (proactive) |
| **Target Market** | Enterprise or generic | **SMEs & Freelancers first**, enterprise later |
| **Transparency** | Black box | Source citations, confidence scores, audit logs |

---

## Target Users

### Primary Users

**Persona 1: Solo Entrepreneur / Freelancer ("The Candy Store Owner")**
- **Who:** Self-employed professionals, small shop owners, consultants (5-10 clients)
- **Channels:** Primarily email, some WhatsApp
- **Pain:** Spends 2-3 hours/day on repetitive questions. Can't afford €50+/month tools.
- **Need:** Draft email responses that match their voice. Review before sending.
- **Budget:** €0-15/month (freemium entry point)
- **Quote:** *"I need a clone of myself that knows my pricing and policies."*

**Persona 2: SME Owner / E-commerce ("Oscar the Shop Owner")**
- **Who:** Small business owners with 1-5 employees, 50-200 customer tickets/day
- **Channels:** Email, website chat, potentially Shopify/WooCommerce integration
- **Pain:** Hired part-time support but 45% turnover. Competitors have chatbots customers hate.
- **Need:** Verified answers about products, shipping, returns. Dashboard to monitor accuracy.
- **Budget:** €40-150/month
- **Quote:** *"I don't want a chatbot that makes stuff up. I need one that asks me if it's unsure."*

### Secondary Users

**Persona 3: Internal Knowledge Access ("The Sales Team")**
- **Who:** Sales representatives at companies with technical products
- **Channels:** Internal chat, Slack integration
- **Pain:** Waiting for engineering to verify feasibility takes too long → salespeople guess → wrong promises
- **Need:** Chat interface to ask "Can we do X?" and get instant, verified answers from technical docs
- **Budget:** Enterprise pricing (future tier)
- **Quote:** *"I just need to know if this is possible before I promise the customer."*

**Persona 4: Support Team Lead ("Sara the Support Manager")**
- **Who:** Manages 3-10 support agents, 500+ tickets/week
- **Channels:** Zendesk/Freshdesk integration, internal dashboard
- **Pain:** Agents waste time on L1 tickets. Knowledge base is always outdated.
- **Need:** Agent co-pilot (AI drafts, human sends), auto-triage, HITL workflow
- **Budget:** €150-500/month per team
- **Quote:** *"My agents should handle complex issues, not copy-paste FAQ answers."*

### User Journey

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           VERIPLY USER JOURNEY                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  1. ONBOARDING (Day 1)                                                       │
│     ┌──────────────────┐                                                     │
│     │ Upload documents │ → PDFs, past emails, FAQs                          │
│     │ Connect email    │ → Gmail/Outlook OAuth                              │
│     │ Set confidence   │ → "Send if >80% confident"                         │
│     └──────────────────┘                                                     │
│            ↓                                                                 │
│  2. FIRST INTERACTION (Day 1-7)                                              │
│     ┌──────────────────┐                                                     │
│     │ Customer emails  │ → "What are your opening hours?"                   │
│     │ AI generates     │ → Draft with 92% confidence                        │
│     │ User reviews     │ → Looks good! Click "Send"                         │
│     └──────────────────┘                                                     │
│            ↓                                                                 │
│  3. LEARNING LOOP (Week 2+)                                                  │
│     ┌──────────────────┐                                                     │
│     │ Low confidence   │ → "I'm not sure about bulk pricing..."             │
│     │ User corrects    │ → Types correct answer                             │
│     │ AI learns        │ → Next time, answers correctly!                    │
│     └──────────────────┘                                                     │
│            ↓                                                                 │
│  4. TRUST BUILDING (Month 1+)                                                │
│     ┌──────────────────┐                                                     │
│     │ Dashboard shows  │ → 85% auto-answered, 15% human-reviewed            │
│     │ User enables     │ → Auto-send for >90% confidence                    │
│     │ Time saved       │ → 2 hours/day → 15 minutes/day                     │
│     └──────────────────┘                                                     │
│            ↓                                                                 │
│  5. EXPANSION (Month 3+)                                                     │
│     ┌──────────────────┐                                                     │
│     │ Add WhatsApp     │ → Same knowledge, new channel                      │
│     │ Invite team      │ → Share bot with employees                         │
│     │ Upgrade tier     │ → More bots, more integrations                     │
│     └──────────────────┘                                                     │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Success Metrics

**North Star Metric:** Time saved per user per week while maintaining 0 incorrect (unverified) answers.

### Business Objectives

| Objective | Target | Rationale |
|-----------|--------|-----------|
| **Validate Product-Market Fit** | 50 active users in first 3 months | Proof that the problem is real and solution works |
| **Prove Trust Differentiator** | 0 hallucination complaints | HITL must work — this is our core value prop |
| **Demonstrate Value** | Users save 5+ hours/week | Quantifiable ROI for marketing |
| **Sustainable Unit Economics** | CAC < 3-month revenue per user | Path to commercial viability |

### Key Performance Indicators

**User Engagement:**
- Daily Active Users (DAU) / Monthly Active Users (MAU)
- Queries per user per day
- Documents uploaded per account
- Retention rate (30-day, 90-day)

**AI Performance:**
- Confidence score distribution (target: >70% above threshold)
- HITL intervention rate (target: <20% after 30 days)
- First Response Resolution rate
- Average response time

**Quality & Trust:**
- User satisfaction (thumbs up/down ratio)
- Accuracy rate (% of AI answers confirmed correct)
- Knowledge gap identification (topics with low confidence)
- Zero tolerance: incorrect answers sent without human review

**Business Health:**
- Conversion rate (free → paid)
- Monthly Recurring Revenue (MRR)
- Churn rate
- Net Promoter Score (NPS)

---

## MVP Scope

### Core Features

**1. Knowledge Ingestion & Management**
- Upload documents (PDF, DOCX, TXT) — max 25MB per file
- Automatic chunking, embedding generation (bge-m3), vector storage (pgvector)
- Version control for documents (latest version used for answers)
- Multi-bot support: users can create multiple bots with separate knowledge bases

**2. RAG-Powered Q&A Chat**
- Chat interface for asking questions
- Semantic search across knowledge base
- Answer generation with confidence score (0-100%)
- Source citations: "Based on [Document Name, Page X]"
- Conversation memory (context-aware follow-ups)

**3. Human-in-the-Loop Dashboard**
- Queue of low-confidence questions awaiting human review
- Side-by-side view: question + retrieved chunks + AI draft
- Approve, edit, or rewrite answers
- Approved answers automatically added to knowledge base (learning loop)

**4. Email Draft Automation**
- OAuth integration with Gmail and Outlook
- Incoming email → AI generates draft response
- Style matching based on user's historical emails
- User reviews draft → edits if needed → sends
- Confidence threshold: auto-draft vs "needs attention" queue

**5. User & Access Management**
- User authentication (email/password + OAuth)
- Bot-level permissions: Owner, Admin, Editor, Viewer
- Invite system: share bots with team members
- Multi-tenant isolation (Row-Level Security in PostgreSQL)

### Out of Scope for MVP

| Feature | Why Deferred | When to Add |
|---------|--------------|-------------|
| WhatsApp/Messenger integration | Requires business API setup, compliance | Phase 2 (after email works) |
| Voice/Phone automation | High complexity, different tech stack | Phase 3 (if demand) |
| Task automation (booking, CRM updates) | Requires deep integrations | Phase 3 (enterprise tier) |
| Shopify/WooCommerce integration | Specific to e-commerce segment | Phase 2 |
| Zendesk/Freshdesk sync | Requires partnership/API work | Phase 2 (support team tier) |
| On-premise deployment | Enterprise requirement | Phase 3 |
| Fine-tuning on customer data | Complex, expensive, risky | Only if RAG proves insufficient |

### MVP Success Criteria

| Criteria | Measurement | Target |
|----------|-------------|--------|
| **Functional** | Core user journey works end-to-end | Upload doc → Ask question → Get answer with source |
| **Performance** | Response latency | <3 seconds for chat, <30 seconds for email draft |
| **Accuracy** | No unverified incorrect answers | 100% of low-confidence → HITL queue |
| **Usability** | Users complete onboarding without support | >80% success rate |
| **Stability** | Uptime | >99% during demo/testing period |

### Future Vision

**Phase 2: Channel Expansion**
- WhatsApp Business API integration
- Website chat widget (embeddable)
- Slack/Teams integration for internal use

**Phase 3: Enterprise & Automation**
- Zendesk/Freshdesk two-way sync
- Task automation (calendar booking, CRM updates)
- Advanced analytics and reporting
- SOC 2 compliance, enterprise SSO

**Phase 4: Intelligence**
- Proactive suggestions ("3 customers asked this today — add to FAQ?")
- Sentiment analysis
- Multi-language support (auto-detect and respond in customer's language)
- Voice integration

---

## Market Context

**Total Addressable Market (TAM):** $12.06 Billion (2024) → $44.7 Billion (2028)  
**Growth Rate:** 20%+ CAGR  
**Geographic Focus:** Europe (GDPR-compliant from day one), expansion to US later

### Market Segmentation

| Segment | Size | Veriply Fit | Priority |
|---------|------|-------------|----------|
| **Freelancers & Solopreneurs** | Millions globally | Perfect fit — price-sensitive, need simple solution | 🥇 Launch |
| **SMEs (1-50 employees)** | 25M+ in Europe alone | Strong fit — need affordable, reliable support automation | 🥇 Launch |
| **Mid-Market (50-500 employees)** | Growing segment | Good fit — need integrations, team features | 🥈 Phase 2 |
| **Enterprise (500+ employees)** | High revenue potential | Future fit — need compliance, SSO, on-prem options | 🥉 Phase 3 |

### Competitive Landscape

| Player | Position | Pricing | Veriply Opportunity |
|--------|----------|---------|---------------------|
| **Zendesk** | Legacy incumbent | €155+/agent/month | Too expensive & complex for SMEs |
| **Intercom** | Modern incumbent | $0.99/resolution | Unpredictable costs, no HITL |
| **Chatbase** | AI-native challenger | $40-150/month | No verification, hallucination risk |
| **Dante AI** | Budget AI chatbot | $8-50/month | Same hallucination problem |
| **Help Scout** | SME-focused support | Contact-based tiers | Less AI capabilities |

**Veriply's Positioning:** "Verified Intelligence" — the accuracy of human support at the speed of AI, with pricing SMEs can afford.

---

## Technical Preferences

### Chosen Stack (Validated in Technical Research)

| Layer | Technology | Rationale |
|-------|------------|-----------|
| **Frontend** | Next.js (React) | Fast development, great DX, SSR for SEO |
| **Backend API** | FastAPI (Python) | Async-first, perfect for AI/ML workloads, automatic docs |
| **AI Orchestration** | LangChain | Industry standard for RAG, easy LLM switching |
| **LLM (MVP)** | OpenAI GPT-4o-mini | Fast, cheap, reliable. Switch to Qwen later for cost. |
| **LLM (Scale)** | Qwen 2.5 14B via Ollama | Self-hosted, 256K context, multilingual, zero API cost |
| **Embeddings** | bge-m3 (1024 dims) | Best multilingual, hybrid search support |
| **Database** | PostgreSQL + pgvector | 75% cheaper than Pinecone, same performance, ACID |
| **Email Integration** | Gmail API + Microsoft Graph | Direct integration, OAuth2 |
| **Hosting** | Docker + Cloud (TBD) | Containerized for portability |

### Architecture Principles

1. **Multi-tenant from Day 1:** Row-Level Security in PostgreSQL
2. **API-First:** Everything accessible via REST API for future integrations
3. **Channel-Agnostic:** Same RAG engine serves chat, email, WhatsApp (when added)
4. **Privacy by Design:** Data minimization, encryption at rest, GDPR compliance
5. **Observable:** Logging, audit trails, monitoring from the start

---

## Risks and Assumptions

### Key Assumptions

| Assumption | Validation Plan |
|------------|-----------------|
| SMEs will pay €15-150/month for verified AI support | Early user interviews, beta pricing tests |
| HITL workflow is acceptable (users will review low-confidence) | User testing during MVP |
| Email draft generation matches user expectations | A/B test different styles, collect feedback |
| pgvector performance is sufficient for MVP scale | Load testing, benchmark validation |
| Users will upload enough documents to make AI useful | Onboarding optimization, templates |

### Key Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| **AI hallucination gets through** | Destroys trust, bad reviews | Strict confidence thresholds, never auto-send without human approval initially |
| **OAuth token security breach** | Legal liability, data exposure | Encrypt tokens, regular security audits, penetration testing |
| **HITL creates too much work** | Users abandon platform | Smart thresholds, learning loop, gamification of "time saved" |
| **Competitor copies HITL feature** | Differentiation erodes | Move fast, build brand, add features |
| **LLM API costs exceed budget** | Unsustainable unit economics | Switch to self-hosted Qwen earlier, aggressive caching |
| **GDPR/AI Act non-compliance** | Fines, shutdown in EU | Legal review before launch, transparency features built-in |

---

## Supporting Materials

### Research Documents Incorporated

1. **Market Research Report** (`research-market-2025-11-27.md`)
   - TAM/SAM analysis, competitor pricing, market gaps
   
2. **Technical Research Report** (`research-technical-2025-11-27.md`)
   - LLM comparison (Qwen 2.5 recommended), embedding models, hosting strategy
   
3. **User & Domain Research Report** (`research-user-domain-2025-11-27.md`)
   - User personas, JTBD framework, industry standards, pgvector benchmarks
   
4. **Brainstorming Session Results** (`brainstorming-session-results-2025-11-27.md`)
   - Trust-first approach validated, HITL as core differentiator, rejected community verification

### Design Artifacts

- Figma Design Board: https://www.figma.com/board/85rRoXk7IT8YoR6pNDzUv2/Veriply-Design
- Database Schema: Mermaid diagram in design thinking doc
- User Flowcharts: Included in design thinking documentation

### Project Management

- Trello Board: https://trello.com/invite/b/691c4dcb977bf3ddf09f1e8a/

---

_This Product Brief captures the vision and requirements for Veriply._

_It was created through collaborative discovery with Dario, incorporating extensive market research, technical analysis, and user research conducted on 2025-11-27._

_Next: The PRD workflow will transform this brief into detailed product requirements, followed by technical architecture and epic/story creation._
