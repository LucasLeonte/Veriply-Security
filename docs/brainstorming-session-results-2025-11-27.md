# Brainstorming Session Results

**Session Date:** 2025-11-27
**Facilitator:** Analyst Mary
**Participant:** Dario
**Topic:** Veriply - AI Customer Service & Knowledge Automation Platform

## Session Start

**Session Context:**
The user provided a comprehensive project definition for "Veriply", an AI-driven customer service platform.
Key features include:
- **RAG-based Q&A:** Using company documentation (PDFs, etc.) to answer questions.
- **Human-in-the-Loop (HITL):** Low-confidence answers are routed to humans for correction/training.
- **Email Automation:** Draft generation based on history and style.
- **Tech Stack:** React, FastAPI, LangChain, PostgreSQL + pgvector, Qwen/OpenAI.
- **Target Audience:** Freelancers, SMEs, Support Teams.

**Stated Goals:**
- Validate and refine the existing MVP definition.
- Explore differentiation against competitors like Zendesk/Intercom.
- Flesh out future features (Voice, Task Automation).
- Ensure security and trust (Confidence scores, Citations).

## Executive Summary

**Topic:** Veriply - AI Customer Service & Knowledge Automation Platform

**Session Goals:** Validate MVP, explore differentiators, and refine advanced features (HITL/Email).

**Techniques Used:** AI-Recommended (Assumption Reversal, Chaos Engineering, Future Self Interview)

**Total Ideas Generated:** (To be determined)

### Key Themes Identified:

(To be determined)

## Technique Sessions

### Technique 1: Assumption Reversal

_Challenging core beliefs to find new angles_

**Core Assumption:** "Customers want AI to draft emails for them to save time."
**Reversal:** "What if customers DON'T want AI to draft emails? What if they want AI to STOP emails from happening?"
**Idea:** Instead of drafting replies, the AI proactively updates the website/FAQ so the question isn't asked again. Or it creates a "status page" for that specific customer.
**Refinement:** The AI *suggests* FAQ updates to the user based on recurring questions ("3 people asked this today - add to FAQ?"), but does not update automatically.

**Core Assumption:** "We need a Human-in-the-Loop (HITL) dashboard for support staff."
**Reversal:** "What if there is NO support staff to check the dashboard?"
**Idea:** Community-based HITL (trusted customers verify answers for rewards) or "Crowdsourced Confidence" where the user who asked the question verifies the answer for the next person.
**Refinement:** Rejected. End-users cannot be trusted with quality control. HITL must remain internal.

**Core Assumption:** "Knowledge must be uploaded as documents (PDFs)."
**Reversal:** "What if knowledge is NEVER uploaded?"
**Idea:** The AI "lives" in the browser/OS and learns by watching the expert work (screen recording/action observation) rather than reading static docs. "Veriply Watch" mode.
**Refinement:** Instead of "watching" live, simply ingest *historical* chats/emails. It's easier and achieves the same goal of learning from "done" work without manual upload.

### Technique 2: Chaos Engineering

### Technique 2: Chaos Engineering

_Stress-testing the concept against worst-case scenarios_

**Scenario 1: The "Hallucination" Disaster**
*   **Chaos:** AI promises a refund or feature it shouldn't.
*   **Idea:** "Guardrails" - a separate AI layer checks outgoing messages against a policy.
*   **Refinement:** Requires precise user configuration. To simplify, we can offer "Pre-set Guardrails" (e.g., "E-commerce Safe Mode", "Support Safe Mode") that users can toggle, rather than writing complex rules from scratch.

**Scenario 2: The "Data Leak" Nightmare**
*   **Chaos:** AI reveals PII (addresses, names) from uploaded docs.
*   **Idea:** "PII Redaction Layer" - automatically detect and mask PII *before* embedding.
*   **Refinement:** Essential feature. Must happen at the *ingestion* stage. Also strict Row Level Security (RLS) in Postgres to ensure Bot A never touches Bot B's data.

**Scenario 3: The "Flood" Attack**
*   **Chaos:** Competitor spams the bot to drain API credits.
*   **Idea:** "Smart Rate Limiting" based on *Compute Cost*, not just request count.
*   **Refinement:** If a user asks 5 expensive questions in a row, trigger CAPTCHA or throttle. This protects the business model.

### Technique 3: Future Self Interview

_Gaining long-term perspective on the product vision_

**Question:** "What was the biggest mistake we avoided in the early days?"
**Answer:** "Allowing hallucinations."
**Insight:** Trust is the currency. If Veriply had been 'creative' instead of 'accurate' in the beginning, we would have lost the enterprise market immediately.
**Strategic Implication:** The "Confidence Score" and "Source Citation" features are not just nice-to-haves; they are the *core* of the brand. We must prioritize accuracy over feature bloat.

## Idea Categorization

### Immediate Opportunities

_Ideas ready to implement now_

1.  **RAG Q&A Core:** The foundation. Ingest PDFs, answer questions with citations.
2.  **Internal HITL Dashboard:** The quality control layer. Staff verifies low-confidence answers.
3.  **Historical Ingestion:** Jumpstart knowledge by reading past support tickets/emails.
4.  **Smart Rate Limiting:** Protect the business from API abuse via cost-based throttling.

### Future Innovations

_Ideas requiring development/research_

1.  **Proactive FAQ Suggestions:** AI prompts admins to publish recurring answers to the public site.
2.  **Pre-set Guardrails:** "Safe Mode" toggles for easy security configuration.
3.  **Email Draft Automation:** Generating replies based on historical style (requires high trust first).

### Moonshots

_Ambitious, transformative concepts_

1.  **Veriply Voice:** Full telephony integration for automated phone support.
2.  **Task Automation:** AI that can *do* things (book appointments, update CRMs) not just answer.

### Insights and Learnings

_Key realizations from the session_

1.  **Trust is the Product:** The biggest risk is hallucination. Features that build trust (citations, confidence scores, HITL) are more important than "flashy" AI features.
2.  **Internal Control is Key:** We rejected "Community HITL" in favor of strict internal verification to maintain quality.
3.  **Security is a Feature:** PII redaction and rate limiting are not just backend tasks; they are selling points for the enterprise.

## Action Planning

### Top 3 Priority Ideas

#### #1 Priority: Trust-First RAG Core

- Rationale: Without accurate, cited answers, the product fails. This addresses the "Hallucination" risk directly.
- Next steps: Build Ingestion Pipeline with PII redaction + RAG Engine with Citation logic.
- Resources needed: FastAPI, LangChain, Postgres/pgvector.
- Timeline: Sprint 1-2.

#### #2 Priority: Internal HITL Workflow

- Rationale: AI will fail initially. The human safety net is critical for early adoption and training.
- Next steps: Build "Pending Questions" dashboard and "Answer Editor" for support staff.
- Resources needed: React Dashboard, Feedback Loop API.
- Timeline: Sprint 3.

#### #3 Priority: Historical Knowledge Ingestion

- Rationale: Solves the "Cold Start" problem. Users get value immediately without manually uploading 100 PDFs.
- Next steps: Build connectors for Email/Ticket export formats (CSV/JSON) to feed the vector DB.
- Resources needed: Data parsers, Bulk embedding worker.
- Timeline: Sprint 4.

## Reflection and Follow-up

### What Worked Well

The "Assumption Reversal" helped us pivot from "Community HITL" (risky) to "Internal HITL" (safe) and clarified the "Proactive FAQ" feature. "Chaos Engineering" solidified the security requirements.

### Areas for Further Exploration

We need to define the specific "Guardrails" for the Pre-set Safe Modes. What exactly does "E-commerce Safe Mode" block?

### Recommended Follow-up Techniques

**Pre-Mortem:** Before launch, do a session on "Why did Veriply fail in 2026?" to catch any remaining blind spots.

### Questions That Emerged

- How do we handle "conflicting" information in historical data? (e.g., old emails vs. new PDFs).
- What is the exact pricing model for the "Compute Cost" rate limiting?

### Next Session Planning

- **Suggested topics:** Detailed Architecture Design, Guardrail Definitions.
- **Recommended timeframe:** Before starting the PRD.
- **Preparation needed:** Review API costs for rate limiting strategy.

---

_Session facilitated using the BMAD CIS brainstorming framework_
