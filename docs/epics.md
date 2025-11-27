# Veriply - Epic Breakdown

**Author:** Dario
**Date:** 2025-11-27
**Project Level:** SaaS B2B Platform
**Target Scale:** High Complexity

---

## Overview

This document provides the complete epic and story breakdown for Veriply, decomposing the requirements from the [PRD](./prd.md) into implementable stories.

**Living Document Notice:** This is the initial version. It will be updated after UX Design and Architecture workflows add interaction and technical details to stories.

### Proposed Epic Structure

1.  **Epic 1: Foundation & App Shell**
    *   **Goal:** Establish the secure, multi-tenant infrastructure AND the frontend application shell (Sidebar, Layout).
    *   **Value:** Users can securely sign up, log in, and see the "Deep Ocean" interface immediately.
    *   **FR Coverage:** FR1, FR2, FR3 + (UI Shell foundation)

2.  **Epic 2: Secure Ingestion Pipeline**
    *   **Goal:** Build the pipeline to ingest, **redact PII**, chunk, and embed various data sources (Files, Web, Email).
    *   **Value:** Users can safely upload data, knowing PII is handled *before* storage, populating the AI's brain.
    *   **FR Coverage:** FR4, FR5, FR6, FR7, FR8, FR12 (PII Redaction)

3.  **Epic 3: Trust-First RAG & Eval**
    *   **Goal:** Implement the core retrieval logic, citation, and a **Quality Evaluation Framework** (Automated testing).
    *   **Value:** The system generates accurate, cited answers, and we can mathematically prove accuracy via the Eval framework.
    *   **FR Coverage:** FR9, FR10, FR11, FR17, FR18

4.  **Epic 4: HITL Workflow**
    *   **Goal:** Implement the specific "Draft Review" interactions and "Trust Gap" UI components within the existing shell.
    *   **Value:** Support agents can efficiently verify AI work, turning drafts into trusted answers with minimal effort.
    *   **FR Coverage:** FR13, FR14, FR15, FR16

5.  **Epic 5: Analytics & Insights**
    *   **Goal:** Provide visibility into system performance, agent efficiency, and AI accuracy.
    *   **Value:** Admins can measure ROI (deflection rate) and trust (hallucination rate).
    *   **FR Coverage:** FR19, FR20

---

## Functional Requirements Inventory

*   **FR1:** Users can register and create a new tenant organization.
*   **FR2:** Admins can invite team members and assign roles (Admin, Manager, Agent).
*   **FR3:** System must enforce strict data isolation between tenants.
*   **FR4:** Users can upload documents (PDF, Markdown, TXT) for indexing.
*   **FR5:** Users can connect external data sources (Notion, Web URL) for periodic syncing.
*   **FR6:** Users can import historical email archives (via IMAP or file upload) to populate the knowledge base.
*   **FR7:** System must automatically chunk and embed ingested content into the vector store.
*   **FR8:** Users can manually delete or update specific documents.
*   **FR9:** System can retrieve relevant context for a user query using semantic search.
*   **FR10:** System can generate a natural language answer based *only* on retrieved context.
*   **FR11:** System must provide citations (source document + page/section) for every answer.
*   **FR12:** System must redact PII from queries before sending to the LLM.
*   **FR13:** Agents can view a queue of "Pending Review" AI drafts (for emails or low-confidence chats).
*   **FR14:** Agents can edit the AI draft before approving.
*   **FR15:** Agents can "Approve" a draft, which sends it to the user and adds it to the Verified KB.
*   **FR16:** Agents can "Reject" a draft, providing a reason (e.g., "Hallucination", "Wrong Tone").
*   **FR17:** System maintains a separate index of "Verified Q&A Pairs" (Golden Dataset).
*   **FR18:** Incoming queries are checked against the Verified KB *first* (Exact/Semantic match) before generating a new answer.
*   **FR19:** Admins can view dashboard metrics: Total Queries, Deflection Rate, Average Response Time.
*   **FR20:** Admins can view "Hallucination Rate" (based on Agent Rejections).

---

## FR Coverage Map

*   **Epic 1:** FR1, FR2, FR3
*   **Epic 2:** FR4, FR5, FR6, FR7, FR8, FR12
*   **Epic 3:** FR9, FR10, FR11, FR17, FR18
*   **Epic 4:** FR13, FR14, FR15, FR16
*   **Epic 5:** FR19, FR20

---

## Epic 1: Foundation & App Shell

**Goal:** Establish the secure, multi-tenant infrastructure AND the frontend application shell (Sidebar, Layout).
**Value:** Users can securely sign up, log in, and see the "Deep Ocean" interface immediately.

### Story 1.1: Project Initialization & Monorepo Setup
**As a** Developer,
**I want** a configured monorepo with Next.js (Frontend) and FastAPI (Backend),
**So that** I have a stable foundation for building the application.

**Acceptance Criteria:**
**Given** a fresh clone of the repository
**When** I run `npm install` and `npm run dev`
**Then** the Next.js frontend should load on localhost:3000
**And** the FastAPI backend should load on localhost:8000/docs
**And** a shared `types` package should be available for TypeScript interfaces
**And** Docker Compose should spin up a local PostgreSQL instance

**Technical Notes:**
*   Use Turborepo or simple npm workspaces.
*   Frontend: Next.js 14 (App Router), Tailwind CSS, shadcn/ui.
*   Backend: FastAPI, Pydantic, SQLAlchemy (Async).
*   Database: PostgreSQL 16 with pgvector extension enabled.

### Story 1.2: Database Schema & Multi-Tenancy Foundation
**As a** System Architect,
**I want** a PostgreSQL database with Row-Level Security (RLS) enabled,
**So that** tenant data is strictly isolated at the database layer.

**Acceptance Criteria:**
**Given** a connected database
**When** I apply the migration scripts
**Then** tables for `tenants`, `users`, and `documents` should exist
**And** every table should have a `tenant_id` column (except `tenants` itself)
**And** RLS policies should be active, preventing cross-tenant data access
**And** a "System Admin" tenant should be seeded

**Technical Notes:**
*   Use Alembic for migrations.
*   Implement a `get_current_tenant` dependency in FastAPI.
*   Ensure `pgvector` extension is active.

### Story 1.3: Authentication & User Session Management
**As a** User,
**I want** to sign up and log in using my email,
**So that** I can access the platform securely.

**Acceptance Criteria:**
**Given** a guest user on the login page
**When** I enter valid credentials
**Then** I should receive a secure HTTP-only cookie (JWT)
**And** I should be redirected to the dashboard
**And** the backend should validate the token on every protected request

**Technical Notes:**
*   Use Supabase Auth or NextAuth.js (with custom backend validation).
*   Token payload must include `tenant_id` and `role`.
*   Implement a "Login" page with the "Deep Ocean" branding (Slate 900 background).

### Story 1.4: Frontend App Shell Implementation (Deep Ocean Theme)
**As a** User,
**I want** to see the "Deep Ocean" navigation sidebar and layout,
**So that** I can navigate between the Dashboard, Inbox, and Settings.

**Acceptance Criteria:**
**Given** I am logged in
**When** I view the dashboard
**Then** I should see the dark sidebar (Slate 900) on the left
**And** the main content area should be light (Slate 50)
**And** the navigation links (Dashboard, Inbox, Analytics) should be clickable
**And** the layout should be responsive (collapsible sidebar on mobile)

**Technical Notes:**
*   Implement the layout from `docs/mockups/agent-dashboard.html`.
*   Use `shadcn/ui` components: `Button` (ghost), `Avatar`, `ScrollArea`.
*   Ensure the "Deep Ocean" color palette is configured in `tailwind.config.js`.

### Story 1.5: Tenant Onboarding Flow (Create Org)
**As a** New User,
**I want** to create a new Organization (Tenant) during signup,
**So that** I can start using the platform with my team.

**Acceptance Criteria:**
**Given** I am a new user
**When** I complete the signup form
**Then** a new `tenant` record should be created
**And** I should be assigned the "Admin" role for that tenant
**And** I should be redirected to the "Getting Started" page

**Technical Notes:**
*   Transactional integrity: User creation + Tenant creation must happen atomically.

## Epic 2: Secure Ingestion Pipeline

**Goal:** Build the pipeline to ingest, **redact PII**, chunk, and embed various data sources (Files, Web, Email).
**Value:** Users can safely upload data, knowing PII is handled *before* storage, populating the AI's brain.

### Story 2.1: Document Upload API & Storage
**As a** User,
**I want** to upload PDF, Markdown, and Text files via the API,
**So that** my documents are securely stored and ready for processing.

**Acceptance Criteria:**
**Given** an authenticated user with "Admin" or "Manager" role
**When** I POST a file to `/api/v1/documents/upload`
**Then** the file should be validated (size limit, allowed extensions)
**And** the file should be stored in the object storage (S3/MinIO) with a unique key
**And** a record should be created in the `documents` table with status "PENDING"

**Technical Notes:**
*   Allowed types: `.pdf`, `.md`, `.txt`.
*   Max size: 10MB.
*   Use `python-multipart` for file handling in FastAPI.
*   Store metadata: `filename`, `content_type`, `size`, `uploaded_by`.

### Story 2.2: Text Extraction Service
**As a** System,
**I want** to extract raw text from uploaded PDFs and other formats,
**So that** the content can be processed by the LLM pipeline.

**Acceptance Criteria:**
**Given** a document in "PENDING" status
**When** the background processing task runs
**Then** the text content should be extracted from the file
**And** the raw text should be stored temporarily for the next stage
**And** if extraction fails, the document status should update to "ERROR"

**Technical Notes:**
*   Use `pypdf` for PDFs.
*   Use standard libraries for text/markdown.
*   Implement as a background task (Celery or ARQ) to avoid blocking the API.

### Story 2.3: PII Redaction Layer (Security Core)
**As a** Security Officer,
**I want** the system to automatically detect and redact PII (Names, Emails, Phone Numbers) from extracted text,
**So that** sensitive customer data is never stored in the vector database or sent to the LLM.

**Acceptance Criteria:**
**Given** extracted text containing PII (e.g., "Contact John Doe at john@example.com")
**When** the text passes through the redaction pipeline
**Then** the output should replace PII with placeholders (e.g., "Contact <PERSON> at <EMAIL>")
**And** the original unredacted text should be discarded (or stored in a strictly access-controlled vault if required by policy - for this MVP, discard/encrypt).

**Technical Notes:**
*   Use Microsoft Presidio or a specialized NER model (e.g., HuggingFace `dslim/bert-base-NER`).
*   **Critical:** This step must happen *before* embedding.

### Story 2.4: Chunking & Vector Embedding
**As a** System,
**I want** to split the redacted text into semantic chunks and generate vector embeddings,
**So that** the content can be efficiently searched.

**Acceptance Criteria:**
**Given** redacted text
**When** the embedding pipeline runs
**Then** the text should be split into chunks (e.g., 512 tokens with overlap)
**And** each chunk should be sent to the Embedding Model (e.g., OpenAI `text-embedding-3-small`)
**And** the resulting vectors should be stored in the `document_chunks` table in PostgreSQL
**And** the document status should update to "INDEXED"

**Technical Notes:**
*   Use `langchain` or `llama-index` for chunking strategies (RecursiveCharacterTextSplitter).
*   Database: `pgvector` column for embeddings.
*   Ensure chunks are linked to the parent `document_id`.

### Story 2.5: Knowledge Base Management UI
**As a** User,
**I want** to view a list of uploaded documents and their status,
**So that** I can manage the knowledge base.

**Acceptance Criteria:**
**Given** I am on the "Knowledge Base" page
**When** the page loads
**Then** I should see a table of documents with columns: Name, Type, Upload Date, Status (Pending, Indexed, Error)
**And** I should be able to delete a document (which removes its chunks)
**And** I should see an "Upload" button to add new files

**Technical Notes:**
*   Frontend: `shadcn/ui` Table component.
*   Real-time updates: Poll status or use WebSocket/SSE for "Indexing..." progress.

## Epic 3: Trust-First RAG & Eval

**Goal:** Implement the core retrieval logic, citation, and a **Quality Evaluation Framework** (Automated testing).
**Value:** The system generates accurate, cited answers, and we can mathematically prove accuracy via the Eval framework.

### Story 3.1: Semantic Search & Retrieval Service
**As a** System,
**I want** to retrieve the most relevant document chunks for a user query,
**So that** the LLM has the correct context to answer the question.

**Acceptance Criteria:**
**Given** a user query (e.g., "How do I reset my password?")
**When** the retrieval service runs
**Then** the query should be embedded using the same model as ingestion
**And** the system should query `pgvector` for the top K (e.g., 5) most similar chunks
**And** the results should be filtered by the user's `tenant_id` (Strict Isolation)

**Technical Notes:**
*   Use `pgvector` cosine distance operator (`<=>`).
*   Implement a "Hybrid Search" if possible (Keyword + Semantic), but start with Semantic for MVP.

### Story 3.2: RAG Generation with Strict Citations
**As a** User,
**I want** the AI to answer my question using only the provided company data and cite its sources,
**So that** I can trust the answer is not a hallucination.

**Acceptance Criteria:**
**Given** a set of retrieved context chunks
**When** the LLM generates an answer
**Then** the answer must be grounded *only* in the context
**And** the answer must include inline citations (e.g., `[Source: Policy.pdf, Page 2]`)
**And** if the context is insufficient, the AI should state "I cannot answer this based on the available information."

**Technical Notes:**
*   Prompt Engineering: "You are a helpful assistant. Answer ONLY using the provided context..."
*   Use a low temperature (0.0 or 0.1) for determinism.

### Story 3.3: Verified Q&A Cache (Golden Dataset)
**As a** System,
**I want** to check a "Verified Q&A" index before generating a new answer,
**So that** approved, human-verified answers are always prioritized.

**Acceptance Criteria:**
**Given** a user query
**When** the system processes the request
**Then** it should first search the `verified_qa` table for a semantic match (threshold > 0.95)
**And** if a match is found, return the stored "Verified Answer" immediately (bypassing generation)
**And** if no match is found, proceed to the standard RAG flow

**Technical Notes:**
*   This implements the "Trust-First" architecture.
*   The `verified_qa` table is populated by the HITL workflow (Epic 4).

### Story 3.4: Automated Evaluation Pipeline (The "Trust Score")
**As a** Product Owner,
**I want** to run automated evaluations on a test set of questions,
**So that** I can measure the system's accuracy (Faithfulness, Relevance) before releasing updates.

**Acceptance Criteria:**
**Given** a dataset of Questions and Ground Truth Answers
**When** the Eval pipeline runs
**Then** it should generate answers using the current RAG pipeline
**And** it should calculate metrics: Faithfulness (Did it stick to context?), Answer Relevance, and Context Precision
**And** the results should be logged for analysis

**Technical Notes:**
*   Use `Ragas` or `DeepEval` framework.
*   This is a backend script/pipeline, not necessarily a UI feature yet.

### Story 3.5: Chat Interface with Streaming
**As a** User,
**I want** a chat interface where I can ask questions and see the answer stream in real-time,
**So that** the experience feels responsive.

**Acceptance Criteria:**
**Given** I am on the Dashboard
**When** I type a question and hit Enter
**Then** the answer should stream token-by-token
**And** citations should appear as clickable links/tooltips
**And** the "Thinking..." state should be visible while retrieving context

**Technical Notes:**
*   Frontend: `useChat` hook (Vercel AI SDK or custom).
*   Backend: Server-Sent Events (SSE) or StreamingResponse in FastAPI.

## Epic 4: HITL Workflow

**Goal:** Implement the specific "Draft Review" interactions and "Trust Gap" UI components within the existing shell.
**Value:** Support agents can efficiently verify AI work, turning drafts into trusted answers with minimal effort.

### Story 4.1: Agent Inbox & Queue Management
**As a** Support Agent,
**I want** to see a unified inbox of "Pending Review" items (Emails, Low-confidence Chat queries),
**So that** I know what tasks require my attention.

**Acceptance Criteria:**
**Given** I am on the "Inbox" page
**When** the page loads
**Then** I should see a list of pending items sorted by priority/date
**And** each item should show a summary (Subject/Query, AI Confidence Score)
**And** I should be able to filter by "Source" (Email vs. Chat)

**Technical Notes:**
*   Frontend: `shadcn/ui` Data Table.
*   Backend: Query `interactions` table where `status = 'PENDING_REVIEW'`.

### Story 4.2: Draft Review Interface (The "Trust Gap" UI)
**As a** Support Agent,
**I want** to see the AI's proposed draft alongside the original query and retrieved context,
**So that** I can verify its accuracy before sending.

**Acceptance Criteria:**
**Given** I select an item from the Inbox
**When** the detail view opens
**Then** I should see the "Trust Gap" layout:
    *   Left: Original Query + Retrieved Context (Citations)
    *   Right: AI Draft (Editable Text Area)
**And** the AI Draft should have a "Confidence Badge" (Green/Amber/Red)
**And** I should be able to edit the text of the draft directly

**Technical Notes:**
*   Implement the "AI Draft Card" from `docs/ux-color-themes.html`.
*   Use the "Caution Amber" theme for unverified drafts.

### Story 4.3: Approval & Publishing Workflow
**As a** Support Agent,
**I want** to approve a corrected draft,
**So that** the answer is sent to the user and saved as a "Verified Answer" for future use.

**Acceptance Criteria:**
**Given** I have reviewed/edited a draft
**When** I click "Approve & Send"
**Then** the system should:
    1. Send the response to the user (via Email or Chat WebSocket)
    2. Save the Q&A pair to the `verified_qa` table (Golden Dataset)
    3. Mark the interaction status as "COMPLETED"
    4. Remove the item from my Inbox

**Technical Notes:**
*   This is the key "Loop Closure" step.
*   The `verified_qa` entry ensures the system learns from this interaction (Story 3.3).

### Story 4.4: Rejection & Feedback Loop
**As a** Support Agent,
**I want** to reject a bad AI draft and categorize the error,
**So that** the system metrics reflect the failure and we can improve the model.

**Acceptance Criteria:**
**Given** a poor AI draft
**When** I click "Reject"
**Then** a modal should appear asking for a "Rejection Reason" (e.g., Hallucination, Irrelevant, Toxic)
**And** upon submission, the interaction status should update to "REJECTED" (or "MANUAL_OVERRIDE")
**And** I should be presented with a blank text box to write the correct answer manually

**Technical Notes:**
*   Store rejection reasons for the Analytics Dashboard (Epic 5).

### Story 4.5: Email Integration (Ingestion & Reply)
**As a** System,
**I want** to ingest incoming support emails and send approved replies via SMTP,
**So that** the platform works seamlessly with our existing email support channel.

**Acceptance Criteria:**
**Given** an incoming email to `support@veriply.com`
**When** the system receives it (via Webhook or IMAP polling)
**Then** it should create a new interaction record
**And** trigger the RAG pipeline to generate a draft
**And** place the draft in the "Pending Review" queue
**And** (on Approval) send the reply via the configured SMTP server

**Technical Notes:**
*   Use `mailgun` or `sendgrid` for reliable delivery, or standard SMTP for MVP.
*   Parse email threads to extract the latest message body.

## Epic 5: Analytics & Insights

**Goal:** Provide visibility into system performance, agent efficiency, and AI accuracy.
**Value:** Admins can measure ROI (deflection rate) and trust (hallucination rate).

### Story 5.1: Analytics Dashboard UI
**As a** Tenant Admin,
**I want** to see a high-level dashboard of my organization's AI performance,
**So that** I can understand the value the platform is delivering.

**Acceptance Criteria:**
**Given** I am on the "Analytics" page
**When** the page loads
**Then** I should see key metric cards: Total Queries, Deflection Rate, Avg. Response Time
**And** I should see a chart showing query volume over time (Last 7/30 days)

**Technical Notes:**
*   Frontend: `recharts` or `visx` for charts.
*   Backend: Aggregation queries on the `interactions` table.

### Story 5.2: Deflection & ROI Tracking
**As a** Tenant Admin,
**I want** to know what percentage of queries were successfully handled by the AI (Verified Answers),
**So that** I can calculate the ROI of the system.

**Acceptance Criteria:**
**Given** the analytics dashboard
**When** I view the "Deflection Rate" metric
**Then** it should calculate: `(Verified Auto-Responses / Total Queries) * 100`
**And** it should show a trend line (up/down) compared to the previous period

**Technical Notes:**
*   "Verified Auto-Response" = A query answered directly from the `verified_qa` cache (Story 3.3).

### Story 5.3: Trust & Quality Metrics (Hallucination Rate)
**As a** Tenant Admin,
**I want** to see how often agents are rejecting AI drafts,
**So that** I can monitor the quality and safety of the model.

**Acceptance Criteria:**
**Given** the analytics dashboard
**When** I view the "Trust Score" section
**Then** I should see a breakdown of "Rejection Reasons" (e.g., 15% Hallucination, 5% Toxic)
**And** I should see a "Hallucination Rate" metric: `(Rejected Drafts / Total Drafts) * 100`

**Technical Notes:**
*   Data source: The rejection reasons captured in Story 4.4.

### Story 5.4: Agent Efficiency Reports
**As a** Team Manager,
**I want** to see how much time my agents are saving by using the AI drafts,
**So that** I can optimize team workflows.

**Acceptance Criteria:**
**Given** the "Team Performance" view
**When** I select a date range
**Then** I should see a table of agents with metrics:
    *   Drafts Reviewed
    *   Avg. Review Time (Time from open to approve)
    *   Approval Rate (%)
