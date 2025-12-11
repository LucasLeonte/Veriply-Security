# Veriply - Epic Breakdown

**Author:** Dario  
**Date:** 2025-11-27  
**Project Level:** SaaS B2B Platform  
**Complexity:** High

---

## Overview

This document provides the complete epic and story breakdown for Veriply, decomposing the 64 functional requirements from the [PRD](./prd.md) into implementable stories.

**Living Document Notice:** This is the initial version created from PRD requirements. It will be updated after UX Design and Architecture workflows add interaction and technical details to stories.

### Epic Summary

| Epic | Title                      | FR Coverage            | Stories |
| ---- | -------------------------- | ---------------------- | ------- |
| 1    | Foundation & Auth + Groups | FR1-FR6                | 8       |
| 2    | Bot & Knowledge Management | FR7-FR19               | 5       |
| 3    | RAG Q&A Engine             | FR20-FR26              | 5       |
| 4    | Chat Experience            | FR27-FR36              | 6       |
| 5    | HITL Verification          | FR37-FR43              | 5       |
| 6    | Email Automation           | FR44-FR50              | 5       |
| 7    | Verified Knowledge Base    | FR51-FR55              | 4       |
| 8    | Analytics & Compliance     | FR56-FR64              | 5       |
| 9    | Testing & QA               | Provenance & Isolation | 5       |

**Total:** 9 Epics, 48 Stories covering 64 FRs + cross-cutting test coverage

---

## Functional Requirements Inventory

### User & Tenant Management (FR1-FR6)

-   **FR1:** Users can register with email/password or OAuth (Google, Microsoft)
-   **FR2:** Users can create a new tenant organization during registration
-   **FR3:** Admins can invite team members via email and assign roles
-   **FR4:** Users can update their profile information and notification preferences
-   **FR5:** System enforces strict data isolation between tenants using RLS
-   **FR6:** Admins can remove team members from the organization

### Bot Management (FR7-FR12)

-   **FR7:** Users can create multiple bots within their organization
-   **FR8:** Users can configure bot settings: name, description, confidence threshold
-   **FR9:** Users can set the auto-respond confidence threshold
-   **FR10:** Users can delete a bot and all associated documents/embeddings
-   **FR11:** Users can duplicate a bot configuration (without documents)
-   **FR12:** Bots are isolated: documents and queries scoped to assigned bot

### Knowledge Ingestion (FR13-FR19)

-   **FR13:** Users can upload documents (PDF, DOCX, TXT, MD, CSV) up to 25MB
-   **FR14:** System automatically chunks documents into semantic segments
-   **FR15:** System generates embeddings using bge-m3 model
-   **FR16:** System stores embeddings in PostgreSQL + pgvector with scoping
-   **FR17:** Users can view list of uploaded documents with status
-   **FR18:** Users can delete specific documents and embeddings
-   **FR19:** Users can re-process a document to update embeddings

### RAG & Q&A Engine (FR20-FR26)

-   **FR20:** System retrieves relevant context using semantic vector search
-   **FR21:** System generates answers based _only_ on retrieved context
-   **FR22:** System provides citations (source + section) for every answer
-   **FR23:** System calculates and returns confidence score (0-100%)
-   **FR24:** System checks Verified KB first before generating
-   **FR25:** System refuses out-of-domain questions
-   **FR26:** System redacts PII from queries before sending to LLM

### Chat Interface (FR27-FR32)

-   **FR27:** End-users can interact via web-based chat interface
-   **FR28:** Chat displays AI responses with source citations
-   **FR29:** Chat maintains conversation context for follow-ups
-   **FR30:** End-users can provide feedback (thumbs up/down)
-   **FR31:** Low-confidence responses display "I'm checking with the team"
-   **FR32:** Chat displays "Verified" badge for Verified KB answers

### Embeddable Widget (FR33-FR36)

-   **FR33:** Users can generate embeddable JavaScript snippet
-   **FR34:** Widget customizable: colors, position, welcome message
-   **FR35:** Widget supports domain whitelisting
-   **FR36:** Widget works on desktop and mobile browsers

### HITL Dashboard (FR37-FR43)

-   **FR37:** Agents view queue of pending review items
-   **FR38:** Queue displays: query, context, AI draft, confidence score
-   **FR39:** Agents can approve a draft (sends + adds to Verified KB)
-   **FR40:** Agents can edit a draft before approving
-   **FR41:** Agents can reject with reason
-   **FR42:** Dashboard supports keyboard shortcuts: A/R/E/N
-   **FR43:** Agents can filter queue by bot, date, or status

### Email Automation (FR44-FR50)

-   **FR44:** Users can connect Gmail accounts via OAuth2
-   **FR45:** Users can connect Outlook accounts via OAuth2
-   **FR46:** System monitors inbox for emails matching rules
-   **FR47:** System generates email draft responses from KB
-   **FR48:** System matches user's historical writing style/tone
-   **FR49:** Email drafts appear in HITL queue for review
-   **FR50:** Users can configure which labels/folders to monitor

### Verified Knowledge Base (FR51-FR55)

-   **FR51:** System maintains separate index of verified Q&A pairs
-   **FR52:** Approved HITL responses auto-add to Verified KB
-   **FR53:** Users can manually add Q&A pairs
-   **FR54:** Users can edit or remove Verified KB entries
-   **FR55:** Verified KB entries take priority over RAG answers

### Analytics & Reporting (FR56-FR60)

-   **FR56:** Dashboard: total queries, deflection rate, response time
-   **FR57:** Dashboard: HITL intervention rate over time
-   **FR58:** Dashboard: rejection reasons breakdown
-   **FR59:** Dashboard: most common unanswered questions
-   **FR60:** Users can export analytics as CSV

### Compliance & Data Management (FR61-FR64)

-   **FR61:** Users can delete all data (GDPR Right to be Forgotten)
-   **FR62:** Users can export KB and Q&A history (GDPR Portability)
-   **FR63:** System logs all AI actions and human approvals
-   **FR64:** All AI responses clearly labeled as AI-generated

---

## FR Coverage Map

| Epic                               | FRs Covered                                                                                                          |
| ---------------------------------- | -------------------------------------------------------------------------------------------------------------------- |
| Epic 1: Foundation & Auth + Groups | FR1, FR2, FR3, FR4, FR5, FR6 (group management, invites, RBAC)                                                       |
| Epic 2: Bot & Knowledge Management | FR7, FR8, FR9, FR10, FR11, FR12, FR13, FR14, FR15, FR16, FR17, FR18, FR19 (group-scoped bots, shared KB, provenance) |
| Epic 3: RAG Q&A Engine             | FR20, FR21, FR22, FR23, FR24, FR25, FR26                                                                             |
| Epic 4: Chat Experience            | FR27, FR28, FR29, FR30, FR31, FR32, FR33, FR34, FR35, FR36                                                           |
| Epic 5: HITL Verification          | FR37, FR38, FR39, FR40, FR41, FR42, FR43                                                                             |
| Epic 6: Email Automation           | FR44, FR45, FR46, FR47, FR48, FR49, FR50                                                                             |
| Epic 7: Verified Knowledge Base    | FR51, FR52, FR53, FR54, FR55                                                                                         |
| Epic 8: Analytics & Compliance     | FR56, FR57, FR58, FR59, FR60, FR61, FR62, FR63, FR64                                                                 |
| Epic 9: Testing & QA               | Provenance tracking, group isolation, RBAC, RLS enforcement (cross-cutting)                                          |

---

## Epic 1: Foundation & Auth

**Goal:** Establish the secure, multi-tenant infrastructure and user authentication system.  
**Value:** Users can register, login, create organizations, and invite team members with proper role-based access.  
**FR Coverage:** FR1, FR2, FR3, FR4, FR5, FR6

---

### Story 1.1: Project Infrastructure Setup

**As a** Developer,  
**I want** a configured monorepo with Next.js frontend, FastAPI backend, and Docker services,  
**So that** I have a stable foundation for building the application.

**Acceptance Criteria:**

**Given** a fresh clone of the repository  
**When** I run `docker-compose up`  
**Then** the following services should start:

-   Next.js frontend on localhost:3000
-   FastAPI backend on localhost:8000/docs (Swagger UI)
-   PostgreSQL with pgvector extension on localhost:5432
-   Redis on localhost:6379
-   Ollama service on localhost:11434

**And** running `npm run dev` from apps/web starts the frontend in dev mode  
**And** running `uvicorn` from apps/api starts the backend in dev mode  
**And** environment variables are loaded from `.env` files  
**And** TypeScript and Python linting passes with zero errors

**Prerequisites:** None (first story)

**Technical Notes:**

-   Monorepo structure: apps/web (Next.js 14), apps/api (FastAPI)
-   Docker Compose for local development with hot-reload
-   PostgreSQL 16 with pgvector extension pre-installed
-   Ollama container with custom entrypoint to pull models on first run

---

### Story 1.2: Database Schema & Multi-Tenancy Foundation

**As a** System Architect,  
**I want** a PostgreSQL database with Row-Level Security (RLS) enabled on all tables,  
**So that** tenant data is strictly isolated at the database layer.

**Acceptance Criteria:**

**Given** a connected database  
**When** I apply the migration scripts  
**Then** the following tables should exist:

-   `tenants` (id, name, slug, plan, created_at)
-   `users` (id, tenant_id, email, password_hash, role, created_at)
-   `invitations` (id, tenant_id, email, role, token, expires_at)

**And** every table except `tenants` has a `tenant_id` column  
**And** RLS policies are active: `tenant_id = current_setting('app.current_tenant_id')::uuid`  
**And** a test proves cross-tenant data access is blocked  
**And** Alembic migrations are versioned and reversible

**Prerequisites:** Story 1.1

**Technical Notes:**

-   Use Alembic for Python migrations
-   RLS policies enforce isolation at DB level (defense in depth)
-   `set_config('app.current_tenant_id', ...)` called on each request
-   Covers FR5 (data isolation)

---

### Story 1.3: User Registration & Tenant Creation

**As a** New User,  
**I want** to register with email/password and create my organization,  
**So that** I can start using Veriply with my team.

**Acceptance Criteria:**

**Given** I am on the registration page  
**When** I enter:

-   Email (valid format, unique)
-   Password (min 8 chars, 1 uppercase, 1 number, 1 special)
-   Organization name (2-50 chars)

**Then** a new tenant record is created  
**And** I am assigned the "Owner" role for that tenant  
**And** I receive a verification email with a magic link  
**And** after email verification, I can log in  
**And** I am redirected to the onboarding/dashboard

**Given** I enter an email that already exists  
**When** I submit the form  
**Then** I see an error: "An account with this email already exists"

**And** password strength indicator shows: Weak/Medium/Strong  
**And** form validates in real-time (debounced)  
**And** CAPTCHA protection prevents bot registrations

**Prerequisites:** Story 1.2

**Technical Notes:**

-   Transaction: User + Tenant creation must be atomic
-   Password hashing: bcrypt with cost factor 12
-   Email verification token expires in 24 hours
-   Covers FR1, FR2

---

### Story 1.4: User Login & Session Management

**As a** Registered User,  
**I want** to log in securely with email/password or OAuth,  
**So that** I can access my organization's dashboard.

**Acceptance Criteria:**

**Given** I am on the login page  
**When** I enter valid credentials  
**Then** I receive a JWT access token (15 min expiry)  
**And** I receive a refresh token (7 day expiry) stored in HTTP-only cookie  
**And** I am redirected to the dashboard  
**And** the token payload includes: user_id, tenant_id, role

**Given** I click "Sign in with Google"  
**When** I complete the OAuth flow  
**Then** my account is linked to Google (or created if first time)  
**And** I am logged in with the same JWT flow

**Given** I enter invalid credentials 5 times  
**When** I try again  
**Then** I am rate-limited for 15 minutes  
**And** I see: "Too many login attempts. Please try again later."

**And** "Remember me" checkbox extends refresh token to 30 days  
**And** logout invalidates refresh token server-side

**Prerequisites:** Story 1.3

**Technical Notes:**

-   NextAuth.js for OAuth (Google, Microsoft)
-   JWT signed with RS256 (asymmetric for microservices)
-   Refresh token rotation on use
-   Covers FR1 (OAuth)

---

### Story 1.5: Team Invitation & Role Assignment

**As an** Admin,  
**I want** to invite team members via email and assign roles,  
**So that** my team can collaborate on Veriply.

**Acceptance Criteria:**

**Given** I am an Admin or Owner on the Team Settings page  
**When** I enter an email and select a role (Admin, Manager, Agent, Viewer)  
**Then** an invitation email is sent with a unique signup link  
**And** the invitation appears in "Pending Invitations" list  
**And** the invitation expires in 7 days

**Given** I received an invitation email  
**When** I click the link and complete registration  
**Then** I am added to the tenant with the assigned role  
**And** the invitation is marked as "Accepted"

**Given** an invitation is pending  
**When** the Admin clicks "Revoke"  
**Then** the invitation is cancelled  
**And** the link no longer works

**And** Owners can invite any role  
**And** Admins cannot invite Owners  
**And** duplicate invitations to same email show warning

**Prerequisites:** Story 1.4

**Technical Notes:**

-   Invitation token: cryptographically random, single-use
-   Role hierarchy: Owner > Admin > Manager > Agent > Viewer
-   Covers FR3

---

### Story 1.6: User Profile & Team Management

**As a** User,  
**I want** to update my profile and manage team members,  
**So that** I can maintain my account and team composition.

**Acceptance Criteria:**

**Given** I am on my Profile page  
**When** I update my name, avatar, or notification preferences  
**Then** changes are saved immediately  
**And** I see a success toast: "Profile updated"

**Given** I am an Admin on the Team page  
**When** I view the team member list  
**Then** I see: Name, Email, Role, Last Active, Actions

**Given** I am an Admin viewing a team member  
**When** I click "Remove"  
**Then** I see confirmation: "Remove [Name] from organization?"  
**And** on confirm, the user loses access immediately  
**And** their sessions are invalidated

**Given** I am an Owner  
**When** I change another user's role  
**Then** the role is updated  
**And** permissions take effect on next request

**And** users cannot remove themselves  
**And** last Owner cannot be removed

**Prerequisites:** Story 1.5

**Technical Notes:**

-   Avatar upload to S3-compatible storage
-   Notification preferences: email digest frequency
-   Covers FR4, FR6

---

### Story 1.7: Group Creation & Switching

**As a** User with Tenant Admin role,  
**I want** to create and switch between groups within my tenant,  
**So that** my team can organize bots and knowledge by department or project.

**Acceptance Criteria:**

**Given** I am on the Groups dashboard  
**When** I click "Create Group"  
**Then** I see a form with:

-   Group name (required, 2-50 chars, unique within tenant)
-   Group description (optional, max 500 chars)

**When** I submit a valid form  
**Then** a new group is created  
**And** I am automatically added as "Group Admin"  
**And** the group switcher shows the new group  
**And** I am redirected to the group's dashboard

**Given** I am a member of multiple groups  
**When** I click the group switcher dropdown  
**Then** I see all groups I'm a member of  
**And** I can click to switch to any group  
**And** the UI updates to show that group's data (bots, KB, etc.)  
**And** JWT claims are updated to reflect new group_id

**And** group names must be unique within the tenant  
**And** group creation timestamp is recorded

**Prerequisites:** Story 1.6

**Technical Notes:**

-   Database: `groups` table with tenant_id, group_id in JWT
-   RLS enforces tenant_id + group_id filtering on all group-scoped tables
-   Group switcher component in UI header
-   Session stores active group_id; injected into every request

---

### Story 1.8: Group Member Invitation & RBAC

**As a** Group Admin,  
**I want** to invite users to my group and assign roles (Group Admin, Manager, Operator),  
**So that** team members can collaborate on bots and knowledge in my group.

**Acceptance Criteria:**

**Given** I am a Group Admin on the Group Settings page  
**When** I enter an email and select a role (Group Admin, Manager, Operator)  
**Then** an invitation email is sent with a unique group-specific signup link  
**And** the invitation appears in "Pending Invitations" (group level)  
**And** the invitation expires in 7 days

**Given** I received a group invitation email  
**When** I click the link  
**Then** I am added to that group with the assigned role  
**And** the invitation is marked as "Accepted"

**Given** I am a Group Admin viewing group members  
**When** I click "Remove" on a member  
**Then** I see confirmation: "Remove [Name] from this group?"  
**And** on confirm, the user loses group access  
**And** the user's group sessions are invalidated  
**And** the user remains in the tenant (but not this group)

**Given** I am a Group Admin  
**When** I change a member's role  
**Then** the role is updated in group_members table  
**And** permissions take effect on next request

**And** role hierarchy (Group Admin > Manager > Operator) is enforced  
**And** cannot invite non-existent tenants users (MVP: users must join tenant first)

**Prerequisites:** Story 1.7

**Technical Notes:**

-   Database: `group_members` table (group_id, user_id, role)
-   RLS policy: users can see/manage groups they're members of
-   Group invitations use separate email template
-   Covers group-scoped RBAC (FR3 extended to groups)

---

## Epic 2: Bot & Knowledge Management

**Goal:** Enable users to create bots per group with isolated knowledge bases and upload documents for processing.  
**Value:** Users can create specialized bots per group (HR Bot, Sales Bot) and populate them with company knowledge; all bots in a group share the group's KB with provenance tracking.  
**FR Coverage:** FR7, FR8, FR9, FR10, FR11, FR12, FR13, FR14, FR15, FR16, FR17, FR18, FR19

---

### Story 2.1: Bot Creation & Configuration (Group-Scoped)

**As a** Manager or Group Admin,  
**I want** to create and configure multiple bots within my group,  
**So that** I can specialize bots by function (HR Bot, Sales Bot) and share a single Knowledge Base.

**Acceptance Criteria:**

**Given** I am on my group's Bots page  
**When** I click "Create Bot"  
**Then** I see a form with:

-   Bot name (required, 2-50 chars, unique within group)
-   Description (optional, max 500 chars)
-   Confidence threshold slider (0-100%, default 80%)

**When** I submit a valid form  
**Then** a new bot is created with status "Empty"  
**And** the bot is scoped to my current group (group_id stored in DB)  
**And** I am redirected to the bot's Group KB page  
**And** the bot appears in my group's bot list

**Given** I have an existing bot  
**When** I click "Settings"  
**Then** I can edit name, description, and confidence threshold  
**And** changes are saved on submit

**And** bot names must be unique within the group  
**And** Operators cannot create bots (Manager+ only)

**Prerequisites:** Story 1.8

**Technical Notes:**

-   Database: `bots` table with tenant_id + group_id + RLS
-   Confidence threshold determines auto-respond behavior (FR9)
-   All bots in a group read/write to the same KB
-   Covers FR7, FR8, FR9 (group-scoped)

---

### Story 2.2: Bot Update & Deletion (Group-Scoped)

**As a** Manager or Group Admin,  
**I want** to update bot settings and delete bots,  
**So that** I can refine bot configurations or remove outdated bots from my group.

**Acceptance Criteria:**

**Given** I have an existing bot in my group  
**When** I click "Edit"  
**Then** I can modify:

-   Name
-   Description
-   Confidence threshold

**When** I save changes  
**Then** the bot is updated  
**And** I see success message: "Bot updated"

**Given** I have an existing bot  
**When** I click "Delete"  
**Then** I see warning: "This will permanently delete the bot. The Group KB will be preserved (shared by other bots)."  
**And** I must type the bot name to confirm  
**And** on confirm:

-   Bot record is deleted
-   The Group KB remains (shared across group)
-   All chat sessions for this bot are deleted
-   Bot is removed from all UI lists

**And** only Manager+ can delete bots (not Operators)  
**And** deletion is async with progress indicator

**Prerequisites:** Story 2.1

**Technical Notes:**

-   Cascade delete: bot → chat_sessions only (NOT documents/chunks, as KB is group-scoped)
-   Documents remain in group KB for other bots to use
-   Covers FR10 (adapted to group model)

---

### Story 2.3: Group Knowledge Base View & Provenance

**As a** Group member,  
**I want** to view the shared Knowledge Base with document provenance (which bot uploaded what),  
**So that** I can understand the KB composition and track contributions.

**Acceptance Criteria:**

**Given** I am on the Group KB page  
**When** I view the documents list  
**Then** I see for each document:

-   File name
-   Upload date
-   Uploader name
-   Uploaded by bot(s) (may be multiple)
-   Status (Processing, Ready, Failed)
-   Chunk count
-   Actions (View, Delete)

**When** I click "View" on a document  
**Then** I see:

-   Document content preview
-   List of chunks with embeddings status
-   Which bots reference this document
-   Upload timestamp and uploader

**Given** I have Manager+ role  
**When** I click "Delete" on a document  
**Then** I see confirmation: "Delete this document from the Group KB? All bots will lose access."  
**And** on confirm, the document and its chunks are deleted  
**And** the KB is updated for all bots

**And** Operators can view KB but not delete  
**And** provenance metadata (bot_id, uploader_id) is recorded on upload

**Prerequisites:** Story 2.1

**Technical Notes:**

-   Database: documents.bot_id (nullable, allows multi-bot ownership)
-   RLS ensures only group members see group KB
-   Provenance tracked in documents table (bot_id, created_by_user_id, created_at)
-   Covers FR12, FR17 (group-scoped with provenance)

---

### Story 2.4: Document Upload to Group KB

**As a** Manager or Operator,  
**I want** to upload documents to my group's shared Knowledge Base,  
**So that** all bots in the group can access and answer questions from the content.

**Acceptance Criteria:**

**Given** I am on the Group KB page  
**When** I drag-and-drop or select files  
**Then** I can upload:

-   PDF (up to 25MB)
-   DOCX (up to 25MB)
-   TXT (up to 25MB)
-   MD (up to 25MB)
-   CSV (up to 25MB)

**When** upload completes  
**Then** document appears with status "Processing"  
**And** metadata is recorded:

-   tenant_id (for RLS)
-   group_id (group-scoped)
-   bot_id (which bot triggered upload, optional for multi-source)
-   uploader user_id
-   upload timestamp

**And** I see a progress indicator  
**And** I can continue uploading more files

**Given** I upload an unsupported file type  
**Then** I see error: "File type not supported. Allowed: PDF, DOCX, TXT, MD, CSV"

**Given** I upload a file over 25MB  
**Then** I see error: "File too large. Maximum size: 25MB"

**And** multiple files can be uploaded simultaneously  
**And** Operators can upload; Group Admin and Manager can upload

**Prerequisites:** Story 2.3

**Technical Notes:**

-   Files stored in S3-compatible object storage with tenant/group/bot path prefix
-   Database record with status: uploading → processing → ready → failed
-   Covers FR13 (group-scoped)

---

### Story 2.5: Document Processing Pipeline with Provenance

**As a** System,  
**I want** to extract, chunk, and embed uploaded documents with bot/uploader provenance,  
**So that** content is searchable and we can track which bot contributed to the KB.

**Acceptance Criteria:**

**Given** a document with status "Processing"  
**When** the background worker picks it up  
**Then** the following pipeline executes:

1. Extract raw text from file
2. Split into semantic chunks (512 tokens, 50 token overlap)
3. Generate embeddings using nomic-embed-text (1024 dimensions)
4. Store embeddings in pgvector with metadata:
    - tenant_id
    - group_id
    - bot_id (which bot the doc was uploaded for)
    - document_id
    - chunk_index
    - created_at

**When** pipeline completes successfully  
**Then** document status changes to "Ready"  
**And** chunk count is displayed  
**And** embeddings are indexed (IVFFlat) for fast retrieval

**When** pipeline fails  
**Then** document status changes to "Failed"  
**And** error message is logged  
**And** user can retry processing

**And** PDF extraction handles multi-column layouts  
**And** DOCX extraction preserves headings as metadata  
**And** CSV extraction treats each row as a chunk with column headers  
**And** all chunks include source metadata (filename, page/row)

**Prerequisites:** Story 2.4

**Technical Notes:**

-   Use pypdf for PDFs, python-docx for DOCX, csv module for CSVs
-   Chunking: RecursiveCharacterTextSplitter from LangChain
-   Embeddings table: document_chunks(id, document_id, embedding, bot_id, tenant_id, group_id, ...)
-   RLS policy: only users in tenant+group can see/query chunks
-   Covers FR14, FR15, FR16 (with group/bot provenance)
-   Embeddings: bge-m3 via Ollama API
-   Store: pgvector with HNSW index for fast retrieval
-   Covers FR14, FR15, FR16

---

### Story 2.5: Knowledge Base Management UI

**As a** User,  
**I want** to view and manage my bot's documents,  
**So that** I can maintain an accurate knowledge base.

**Acceptance Criteria:**

**Given** I am on a bot's Knowledge Base page  
**When** the page loads  
**Then** I see a table with:

-   Document name
-   Type (PDF/DOCX/TXT/MD/CSV)
-   Size
-   Status (Processing/Ready/Failed)
-   Chunk count
-   Upload date
-   Actions (View, Delete, Reprocess)

**Given** I click on a document  
**When** the detail view opens  
**Then** I see:

-   Full document metadata
-   List of chunks with preview
-   Processing logs (if failed)

**And** I can search/filter documents by name  
**And** I can sort by any column  
**And** status badges are color-coded (yellow=processing, green=ready, red=failed)

**Prerequisites:** Story 2.4

**Technical Notes:**

-   Paginated list (20 per page)
-   Real-time status updates via polling or WebSocket
-   Covers FR17

---

### Story 2.6: Document Deletion

**As a** User,  
**I want** to delete documents from my knowledge base,  
**So that** I can remove outdated or incorrect information.

**Acceptance Criteria:**

**Given** I am viewing my documents  
**When** I select one or more documents and click "Delete"  
**Then** I see confirmation: "Delete X document(s)? This will remove all chunks and embeddings."

**When** I confirm  
**Then** documents are marked as "Deleting"  
**And** background job removes:

-   File from object storage
-   Document record from database
-   All chunk records
-   All embeddings from vector store

**When** deletion completes  
**Then** documents disappear from the list  
**And** success toast appears

**And** bulk deletion supports up to 100 documents at once  
**And** in-progress deletions show spinner

**Prerequisites:** Story 2.5

**Technical Notes:**

-   Soft delete first, then background hard delete
-   Vector deletion: DELETE FROM chunks WHERE document_id = X
-   Covers FR18

---

### Story 2.7: Document Reprocessing

**As a** User,  
**I want** to reprocess a document to update its embeddings,  
**So that** I can refresh the AI's understanding after editing the source.

**Acceptance Criteria:**

**Given** I have a document with status "Ready" or "Failed"  
**When** I click "Reprocess"  
**Then** the document status changes to "Processing"  
**And** old chunks and embeddings are deleted  
**And** the file is re-extracted, chunked, and embedded  
**And** new chunks replace the old ones

**When** reprocessing completes  
**Then** status returns to "Ready"  
**And** new chunk count may differ from before

**And** I can reprocess multiple documents at once  
**And** reprocessing queue shows position if busy

**Prerequisites:** Story 2.6

**Technical Notes:**

-   Same pipeline as initial processing
-   Useful for embedding model updates
-   Covers FR19

---

### Story 2.8: Bot Isolation Enforcement

**As a** System,  
**I want** to ensure documents and queries are scoped to their assigned bot,  
**So that** HR Bot doesn't access Sales Bot's knowledge.

**Acceptance Criteria:**

**Given** I have two bots in my organization  
**When** I query Bot A  
**Then** only Bot A's documents are searched  
**And** Bot B's documents are never included

**Given** I am viewing Bot A's Knowledge Base  
**Then** I only see documents uploaded to Bot A

**Given** a direct API call with wrong bot_id  
**Then** request is rejected with 403 Forbidden

**And** vector search WHERE clause always includes bot_id  
**And** database queries always filter by bot_id

**Prerequisites:** Story 2.7

**Technical Notes:**

-   RLS policy: `bot_id = current_setting('app.current_bot_id')::uuid`
-   API middleware sets bot context from request
-   Covers FR12

---

## Epic 3: RAG Q&A Engine

**Goal:** Implement semantic search, answer generation with citations, confidence scoring, and PII redaction.  
**Value:** Users get accurate, cited answers from their documents with trust guarantees.  
**FR Coverage:** FR20, FR21, FR22, FR23, FR24, FR25, FR26

---

### Story 3.1: Semantic Vector Search

**As a** System,  
**I want** to retrieve relevant document chunks for a user query,  
**So that** the LLM has accurate context to generate answers.

**Acceptance Criteria:**

**Given** a user query (e.g., "What is the refund policy?")  
**When** the retrieval service runs  
**Then**:

1. Query is embedded using bge-m3 (same model as documents)
2. pgvector cosine similarity search finds top-K chunks (K=5 default)
3. Results are filtered by tenant_id AND bot_id
4. Chunks are returned with similarity scores

**And** search latency is <200ms (p95)  
**And** results include chunk text, document name, and section

**Given** no relevant chunks exist (all similarity < 0.5)  
**Then** empty result set is returned  
**And** downstream handles "no context" case

**Prerequisites:** Story 2.4 (embeddings exist)

**Technical Notes:**

-   pgvector operator: `<=>` for cosine distance
-   HNSW index for fast approximate search
-   Hybrid search (keyword + semantic) is v1.1
-   Covers FR20

---

### Story 3.2: Context-Only Answer Generation

**As a** System,  
**I want** to generate answers based ONLY on retrieved context,  
**So that** the AI never hallucinates from general knowledge.

**Acceptance Criteria:**

**Given** retrieved context chunks  
**When** the LLM generates an answer  
**Then** the prompt enforces:

```
You are a helpful assistant. Answer ONLY using the provided context.
If the context doesn't contain the answer, say "I don't have information about that."
Never make up facts. Never use outside knowledge.

Context:
{chunks}

Question: {query}
```

**And** temperature is set to 0.1 for determinism  
**And** response is streamed token-by-token for perceived speed  
**And** response time is <3s for first token

**Given** context is insufficient  
**Then** LLM responds: "I don't have information about that in the knowledge base."

**Prerequisites:** Story 3.1

**Technical Notes:**

-   LLM: Qwen 2.5 14B via Ollama
-   Fallback: OpenAI GPT-4o-mini if Ollama unavailable
-   Streaming via SSE (Server-Sent Events)
-   Covers FR21, FR25

---

### Story 3.3: Citation Generation

**As a** User,  
**I want** every AI answer to include source citations,  
**So that** I can verify the information myself.

**Acceptance Criteria:**

**Given** an AI-generated answer  
**Then** the response includes inline citations:

-   Format: "According to [Document Name, Section X]..."
-   Or footnote style: "...refund within 30 days.[1]" with "[1] Returns Policy.pdf, Page 3"

**And** citations are clickable links to the source chunk  
**And** citation UI shows: document name, section/page, relevance score  
**And** if multiple chunks support a statement, all are cited

**Given** an answer with no citations  
**Then** this is flagged as a system error (should never happen)

**Prerequisites:** Story 3.2

**Technical Notes:**

-   LLM prompt includes citation format instructions
-   Post-processing maps citations to actual chunks
-   Covers FR22

---

### Story 3.4: Confidence Scoring & Routing

**As a** System,  
**I want** to calculate a confidence score for each answer,  
**So that** low-confidence answers route to HITL review.

**Acceptance Criteria:**

**Given** an AI answer with retrieved context  
**When** confidence is calculated  
**Then** score is 0-100% based on:

-   Retrieval confidence: max similarity score of chunks (40% weight)
-   Answer confidence: LLM's self-reported confidence (30% weight)
-   Context coverage: % of answer supported by context (30% weight)

**And** score is returned with the answer  
**And** score is visible to agents (not end-users)

**Given** confidence >= bot's threshold (default 80%)  
**Then** answer can auto-send (if enabled)

**Given** confidence < threshold  
**Then** answer routes to HITL queue  
**And** end-user sees: "I'm checking with the team..."

**Prerequisites:** Story 3.3

**Technical Notes:**

-   Confidence heuristic can be refined over time
-   LLM prompt asks for self-confidence assessment
-   Covers FR23, FR24 (Verified KB check), FR31 (low-confidence message)

---

### Story 3.5: PII Redaction

**As a** System,  
**I want** to detect and redact PII from queries before sending to LLM,  
**So that** sensitive data is never processed by the AI.

**Acceptance Criteria:**

**Given** a user query containing PII  
**When** the query is processed  
**Then** the following are detected and redacted:

-   Email addresses → `<EMAIL>`
-   Phone numbers → `<PHONE>`
-   Credit card numbers → `<CREDIT_CARD>`
-   Social Security Numbers → `<SSN>`
-   Names (context-dependent) → `<PERSON>`

**And** redacted query is sent to LLM  
**And** original query is logged separately (encrypted) for debugging  
**And** answer is de-redacted before display (if applicable)

**Given** query: "Contact john@example.com for refunds"  
**Then** LLM sees: "Contact <EMAIL> for refunds"

**Prerequisites:** Story 3.2

**Technical Notes:**

-   Use Microsoft Presidio or regex patterns
-   Run BEFORE embedding for retrieval too
-   Log original with encryption for support cases
-   Covers FR26

---

## Epic 4: Chat Experience

**Goal:** Provide end-user chat interface and embeddable widget with conversation context and feedback.  
**Value:** End-users can interact with bots via chat, see verified answers, and provide feedback.  
**FR Coverage:** FR27, FR28, FR29, FR30, FR31, FR32, FR33, FR34, FR35, FR36

---

### Story 4.1: Web Chat Interface

**As an** End-user,  
**I want** to interact with a bot via a web-based chat interface,  
**So that** I can get answers to my questions.

**Acceptance Criteria:**

**Given** I navigate to a bot's chat URL  
**When** the page loads  
**Then** I see:

-   Chat window with welcome message
-   Input field with placeholder "Ask a question..."
-   Send button

**When** I type a question and press Enter/Send  
**Then** my message appears in the chat  
**And** a typing indicator shows  
**And** the AI response streams in token-by-token  
**And** response includes source citations

**And** chat is responsive (mobile-friendly)  
**And** chat history persists for the session  
**And** I can start a new conversation

**Prerequisites:** Epic 3 (RAG engine)

**Technical Notes:**

-   Next.js page with WebSocket/SSE for streaming
-   Session-based chat history (localStorage or server)
-   Covers FR27, FR28

---

### Story 4.2: Conversation Context

**As an** End-user,  
**I want** the chat to remember our conversation,  
**So that** I can ask follow-up questions naturally.

**Acceptance Criteria:**

**Given** I asked "What is your refund policy?"  
**And** the AI answered about 30-day refunds  
**When** I ask "What about after 30 days?"  
**Then** the AI understands the context  
**And** answers about the extended refund period

**And** conversation context is passed to RAG pipeline  
**And** context window is limited to last 10 messages  
**And** clearing conversation resets context

**Prerequisites:** Story 4.1

**Technical Notes:**

-   Prepend conversation history to LLM prompt
-   Summarize older messages if context too long
-   Covers FR29

---

### Story 4.3: User Feedback

**As an** End-user,  
**I want** to provide feedback on AI answers,  
**So that** the system can learn from my input.

**Acceptance Criteria:**

**Given** I received an AI answer  
**When** I click the thumbs-up icon  
**Then** positive feedback is recorded  
**And** icon changes to filled/selected state

**When** I click the thumbs-down icon  
**Then** negative feedback is recorded  
**And** I optionally see: "What was wrong?" with options:

-   Incorrect information
-   Not helpful
-   Other

**And** feedback is linked to the specific answer  
**And** feedback contributes to analytics  
**And** feedback is anonymous (no PII collected)

**Prerequisites:** Story 4.1

**Technical Notes:**

-   Database: `feedback` table with answer_id, type, reason
-   Aggregate for Trust Score metric
-   Covers FR30

---

### Story 4.4: Trust Signals Display

**As an** End-user,  
**I want** to see whether an answer is verified or AI-generated,  
**So that** I know how much to trust it.

**Acceptance Criteria:**

**Given** an answer from the Verified KB  
**Then** I see a green "✓ Verified" badge  
**And** tooltip: "This answer has been verified by a human expert"

**Given** an answer generated by RAG (not verified)  
**Then** I see an amber "AI Generated" badge  
**And** tooltip: "This answer was generated by AI from our knowledge base"

**Given** a low-confidence answer pending review  
**Then** I see: "I'm checking with the team. You'll receive a response shortly."  
**And** a notification when the verified answer arrives

**Prerequisites:** Story 4.1, Epic 5 (HITL)

**Technical Notes:**

-   Badge styling from UX design system
-   Covers FR31, FR32

---

### Story 4.5: Embeddable Widget Generation

**As a** User,  
**I want** to generate an embeddable widget for my bot,  
**So that** I can add the chat to my website.

**Acceptance Criteria:**

**Given** I am on a bot's Settings page  
**When** I click "Get Widget Code"  
**Then** I see a code snippet:

```html
<script
    src="https://veriply.io/widget.js"
    data-bot-id="xxx"
    data-position="bottom-right"
    data-primary-color="#3B82F6"
    data-welcome-message="Hi! How can I help?"
></script>
```

**And** I can customize:

-   Position: bottom-right, bottom-left
-   Primary color: color picker
-   Welcome message: text input
-   Auto-open: on/off

**And** I can preview the widget live  
**And** I can copy the code with one click

**Prerequisites:** Story 4.1

**Technical Notes:**

-   Widget is a separate bundled JS file
-   Loads in iframe for security isolation
-   Covers FR33, FR34

---

### Story 4.6: Widget Security & Responsiveness

**As a** User,  
**I want** to restrict which domains can use my widget,  
**So that** my bot isn't embedded on unauthorized sites.

**Acceptance Criteria:**

**Given** I am on widget settings  
**When** I add allowed domains (e.g., "example.com, \*.example.com")  
**Then** the widget only loads on those domains

**Given** the widget is loaded on an unauthorized domain  
**Then** it shows: "This widget is not authorized for this domain"  
**And** no queries are processed

**And** widget works on mobile browsers (responsive)  
**And** widget uses 44x44px touch targets  
**And** widget is WCAG 2.1 AA accessible

**Prerequisites:** Story 4.5

**Technical Notes:**

-   Server validates Origin/Referer header
-   Wildcard domain support
-   Covers FR35, FR36

---

## Epic 5: HITL Verification

**Goal:** Build the agent dashboard for reviewing, editing, and approving AI drafts.  
**Value:** Agents efficiently verify AI work, building the trust layer that makes Veriply unique.  
**FR Coverage:** FR37, FR38, FR39, FR40, FR41, FR42, FR43

---

### Story 5.1: HITL Queue View

**As an** Agent,  
**I want** to see a queue of pending review items,  
**So that** I know what needs my attention.

**Acceptance Criteria:**

**Given** I am on the HITL Dashboard  
**When** the page loads  
**Then** I see a queue with:

-   Item count badge
-   List of pending items sorted by date (oldest first)
-   Each item shows: Query preview, Bot name, Confidence %, Time waiting

**And** queue updates in real-time when new items arrive  
**And** I can see empty state: "No items pending review. Nice work!"

**Prerequisites:** Epic 3 (low-confidence routing)

**Technical Notes:**

-   WebSocket for real-time updates
-   Database: `review_queue` table with status
-   Covers FR37

---

### Story 5.2: Draft Review Interface

**As an** Agent,  
**I want** to see the AI draft alongside the query and context,  
**So that** I can verify accuracy before approving.

**Acceptance Criteria:**

**Given** I select an item from the queue  
**When** the review interface opens  
**Then** I see a split view:

-   **Left panel:** Original query + Retrieved context chunks with sources
-   **Right panel:** AI draft response (editable)
-   **Top bar:** Confidence score, Bot name, Time in queue

**And** context chunks are expandable/collapsible  
**And** source documents are clickable (opens in new tab)  
**And** draft has syntax highlighting for citations

**Prerequisites:** Story 5.1

**Technical Notes:**

-   Rich text editor for draft (Tiptap or similar)
-   Covers FR38

---

### Story 5.3: Approve & Edit Flow

**As an** Agent,  
**I want** to approve or edit a draft before sending,  
**So that** only accurate answers reach the user.

**Acceptance Criteria:**

**Given** I am reviewing a draft  
**When** I click "Approve" (or press `A`)  
**Then**:

1. Response is sent to the end-user
2. Q&A pair is added to Verified KB
3. Item is removed from queue
4. Next item auto-loads (if exists)

**Given** I edit the draft  
**When** I click "Approve"  
**Then** the EDITED version is sent and stored  
**And** the system records what changed (diff)

**And** approve button is disabled until I've reviewed for >3 seconds  
**And** success toast: "Response sent and verified!"

**Prerequisites:** Story 5.2

**Technical Notes:**

-   Atomic transaction: send + store + dequeue
-   Diff stored for analytics on correction patterns
-   Covers FR39, FR40

---

### Story 5.4: Rejection Flow

**As an** Agent,  
**I want** to reject bad drafts with a reason,  
**So that** the system learns from failures.

**Acceptance Criteria:**

**Given** I am reviewing a poor draft  
**When** I click "Reject" (or press `R`)  
**Then** a modal appears with rejection reasons:

-   Hallucination (made up facts)
-   Wrong Tone (too casual/formal)
-   Outdated Information
-   Irrelevant Answer
-   Other (with text input)

**When** I select a reason and confirm  
**Then**:

1. Item is removed from queue
2. Rejection reason is logged
3. I can optionally write a correct answer manually
4. Next item auto-loads

**And** rejection reasons feed into analytics  
**And** I can skip writing correct answer (item is discarded)

**Prerequisites:** Story 5.2

**Technical Notes:**

-   Database: `rejections` table with reason, notes
-   High rejection rate triggers alerts
-   Covers FR41

---

### Story 5.5: Keyboard Shortcuts & Filtering

**As an** Agent,  
**I want** keyboard shortcuts and filters,  
**So that** I can process the queue efficiently.

**Acceptance Criteria:**

**Given** I am on the HITL Dashboard  
**Then** the following shortcuts work:

-   `A` = Approve current draft
-   `R` = Reject current draft
-   `E` = Focus on edit field
-   `N` = Skip to next item
-   `←/→` = Navigate between items
-   `?` = Show shortcut help

**Given** I click "Filters"  
**Then** I can filter by:

-   Bot (dropdown)
-   Date range (picker)
-   Status (pending, in-progress)

**And** filter state persists in URL  
**And** filtered count shows in header

**Prerequisites:** Story 5.4

**Technical Notes:**

-   Keyboard event listeners with proper focus management
-   URL query params for filter state
-   Covers FR42, FR43

---

## Epic 6: Email Automation

**Goal:** Connect email accounts and generate AI drafts for incoming emails.  
**Value:** Users get AI-generated email drafts that match their writing style, reviewed before sending.  
**FR Coverage:** FR44, FR45, FR46, FR47, FR48, FR49, FR50

---

### Story 6.1: Gmail OAuth Integration

**As a** User,  
**I want** to connect my Gmail account via OAuth,  
**So that** Veriply can read emails and send drafts.

**Acceptance Criteria:**

**Given** I am on the Integrations page  
**When** I click "Connect Gmail"  
**Then** I am redirected to Google OAuth consent screen  
**And** I grant permissions: read emails, send emails

**When** I approve  
**Then** I am redirected back to Veriply  
**And** my Gmail is shown as "Connected"  
**And** refresh token is stored encrypted (AES-256)

**Given** I click "Disconnect"  
**Then** tokens are deleted  
**And** Gmail shows as "Not connected"

**And** connection status shows last sync time  
**And** errors show: "Unable to connect. Please reconnect."

**Prerequisites:** Story 1.4 (auth)

**Technical Notes:**

-   Scopes: `gmail.readonly`, `gmail.compose`, `gmail.modify`
-   Token encryption at rest
-   Covers FR44

---

### Story 6.2: Outlook OAuth Integration

**As a** User,  
**I want** to connect my Outlook account via OAuth,  
**So that** Veriply can read emails and send drafts.

**Acceptance Criteria:**

**Given** I am on the Integrations page  
**When** I click "Connect Outlook"  
**Then** I am redirected to Microsoft OAuth consent screen  
**And** I grant permissions: read emails, send emails

**When** I approve  
**Then** I am redirected back to Veriply  
**And** my Outlook is shown as "Connected"

**And** same UX patterns as Gmail  
**And** supports personal and work/school accounts

**Prerequisites:** Story 6.1

**Technical Notes:**

-   Microsoft Graph API
-   Scopes: `Mail.Read`, `Mail.Send`
-   Covers FR45

---

### Story 6.3: Email Monitoring & Rules

**As a** User,  
**I want** to configure which emails trigger draft generation,  
**So that** I only get drafts for relevant messages.

**Acceptance Criteria:**

**Given** I have a connected email account  
**When** I click "Configure Monitoring"  
**Then** I can set:

-   Monitored folders/labels (Inbox, Support, etc.)
-   Keywords to include (optional)
-   Keywords to exclude (optional)
-   Bot to use for each rule

**When** a new email matches my rules  
**Then** it is queued for draft generation

**And** rules can be tested with sample emails  
**And** I can pause/resume monitoring  
**And** polling frequency: every 5 minutes (configurable)

**Prerequisites:** Story 6.2

**Technical Notes:**

-   Background job polls for new emails
-   Webhook support if available (Gmail push notifications)
-   Covers FR46, FR50

---

### Story 6.4: Email Draft Generation

**As a** System,  
**I want** to generate email draft responses based on the knowledge base,  
**So that** users have a starting point for replies.

**Acceptance Criteria:**

**Given** a new email triggers a rule  
**When** the system processes it  
**Then**:

1. Email content is extracted
2. PII is redacted
3. RAG retrieves relevant context
4. LLM generates a draft reply
5. Draft is added to HITL queue

**And** draft includes:

-   Subject: "Re: [Original Subject]"
-   Body: AI-generated response
-   Citations as internal notes (not in final email)

**And** draft generation takes <30 seconds

**Prerequisites:** Story 6.3, Epic 3 (RAG)

**Technical Notes:**

-   Same RAG pipeline as chat
-   Email-specific prompt template
-   Covers FR47, FR49

---

### Story 6.5: Writing Style Matching

**As a** User,  
**I want** email drafts to match my writing style,  
**So that** responses sound like me, not a generic bot.

**Acceptance Criteria:**

**Given** I have sent emails previously  
**When** the system generates a draft  
**Then** it analyzes my historical emails for:

-   Tone (formal, casual, friendly)
-   Greeting style ("Hi [Name]," vs "Hello,")
-   Signature style
-   Average length

**And** the draft matches these patterns  
**And** I can adjust style settings manually:

-   Tone slider (Formal ↔ Casual)
-   Verbosity (Concise ↔ Detailed)

**And** style analysis uses last 50 sent emails

**Prerequisites:** Story 6.4

**Technical Notes:**

-   Store style profile per user
-   LLM prompt includes style instructions
-   Covers FR48

---

## Epic 7: Verified Knowledge Base

**Goal:** Maintain and manage the golden dataset of verified Q&A pairs.  
**Value:** AI learns from every correction, getting smarter over time.  
**FR Coverage:** FR51, FR52, FR53, FR54, FR55

---

### Story 7.1: Verified KB Storage

**As a** System,  
**I want** to maintain a separate index of verified Q&A pairs,  
**So that** approved answers are prioritized in future queries.

**Acceptance Criteria:**

**Given** a Q&A pair is approved via HITL  
**Then** it is stored in the Verified KB:

-   Question (embedded for semantic match)
-   Answer (full text)
-   Source citations
-   Approved by (user)
-   Approved at (timestamp)
-   Bot ID (scoped)

**And** embeddings use same model as documents (bge-m3)  
**And** Verified KB is separate from document chunks

**Prerequisites:** Epic 5 (HITL)

**Technical Notes:**

-   Table: `verified_qa` with vector column
-   Scoped by tenant_id and bot_id
-   Covers FR51, FR52

---

### Story 7.2: Verified KB Priority

**As a** System,  
**I want** to check the Verified KB BEFORE generating new answers,  
**So that** users get consistent, human-verified responses.

**Acceptance Criteria:**

**Given** a user query  
**When** the RAG pipeline runs  
**Then** the Verified KB is searched FIRST

**Given** a semantic match with confidence > 95%  
**Then** the verified answer is returned immediately  
**And** the "Verified" badge is displayed  
**And** no LLM generation occurs

**Given** no match in Verified KB  
**Then** standard RAG pipeline continues  
**And** answer may be generated from documents

**And** Verified KB search adds <50ms latency

**Prerequisites:** Story 7.1, Epic 3

**Technical Notes:**

-   Two-stage retrieval: Verified KB → Documents
-   High threshold (95%) prevents false matches
-   Covers FR55

---

### Story 7.3: Manual Q&A Entry

**As a** User,  
**I want** to manually add Q&A pairs to the Verified KB,  
**So that** I can seed common questions without waiting for HITL.

**Acceptance Criteria:**

**Given** I am on the Verified KB page  
**When** I click "Add Entry"  
**Then** I see a form with:

-   Question (required)
-   Answer (required, rich text)
-   Tags (optional)

**When** I submit  
**Then** the entry is added to Verified KB  
**And** question is embedded automatically  
**And** entry appears in the list

**And** I can bulk import from CSV (question, answer columns)

**Prerequisites:** Story 7.1

**Technical Notes:**

-   Same embedding pipeline as documents
-   CSV import with validation
-   Covers FR53

---

### Story 7.4: Verified KB Management

**As a** User,  
**I want** to edit or remove Verified KB entries,  
**So that** I can maintain accuracy over time.

**Acceptance Criteria:**

**Given** I am on the Verified KB page  
**Then** I see a searchable list of entries with:

-   Question preview
-   Answer preview
-   Created by / date
-   Actions (Edit, Delete)

**When** I click "Edit"  
**Then** I can modify question or answer  
**And** embedding is regenerated on save

**When** I click "Delete"  
**Then** I see confirmation  
**And** on confirm, entry is removed

**And** I can search entries by keyword  
**And** I can filter by date range or creator

**Prerequisites:** Story 7.3

**Technical Notes:**

-   Editing triggers re-embedding
-   Audit log for changes
-   Covers FR54

---

## Epic 8: Analytics & Compliance

**Goal:** Provide metrics dashboard and ensure GDPR compliance.  
**Value:** Admins measure ROI, users control their data.  
**FR Coverage:** FR56, FR57, FR58, FR59, FR60, FR61, FR62, FR63, FR64

---

### Story 8.1: Analytics Dashboard

**As an** Admin,  
**I want** to see key metrics about my organization's AI usage,  
**So that** I can measure ROI and identify improvements.

**Acceptance Criteria:**

**Given** I am on the Analytics page  
**When** the page loads  
**Then** I see cards showing:

-   **Total Queries:** count for selected period
-   **Deflection Rate:** % answered from Verified KB
-   **Average Response Time:** seconds
-   **HITL Rate:** % requiring human review

**And** I can filter by date range (7d, 30d, 90d, custom)  
**And** I can filter by bot  
**And** charts show trends over time

**Prerequisites:** Epic 5 (data exists)

**Technical Notes:**

-   Pre-aggregated metrics for performance
-   Charts: line for trends, bar for comparisons
-   Covers FR56, FR57

---

### Story 8.2: Quality Metrics

**As an** Admin,  
**I want** to see rejection reasons and knowledge gaps,  
**So that** I can improve the AI and knowledge base.

**Acceptance Criteria:**

**Given** I am on Analytics  
**When** I view the "Quality" tab  
**Then** I see:

-   **Rejection Breakdown:** pie chart of reasons (Hallucination, Wrong Tone, etc.)
-   **Top Unanswered Questions:** list of queries with no good answer
-   **Feedback Score:** thumbs up vs down ratio

**And** clicking an unanswered question shows:

-   Query text
-   Attempted context (if any)
-   Suggestion: "Add to Verified KB"

**Prerequisites:** Story 8.1

**Technical Notes:**

-   Unanswered = low confidence + rejected
-   Covers FR58, FR59

---

### Story 8.3: CSV Export

**As an** Admin,  
**I want** to export analytics data as CSV,  
**So that** I can analyze in Excel or share with stakeholders.

**Acceptance Criteria:**

**Given** I am on Analytics  
**When** I click "Export CSV"  
**Then** I can select:

-   Date range
-   Metrics to include
-   Bots to include

**And** a CSV file downloads with:

-   Headers matching selected metrics
-   One row per day
-   UTF-8 encoding

**And** export respects current filters

**Prerequisites:** Story 8.1

**Technical Notes:**

-   Server-side CSV generation
-   Large exports use streaming
-   Covers FR60

---

### Story 8.4: GDPR Data Controls

**As a** User,  
**I want** to delete all my data or export it,  
**So that** I comply with GDPR rights.

**Acceptance Criteria:**

**Given** I am in Account Settings  
**When** I click "Delete All Data" (Right to be Forgotten)  
**Then** I see warning: "This will permanently delete your organization, all bots, documents, conversations, and analytics."  
**And** I must type "DELETE" to confirm

**When** confirmed  
**Then** a background job runs that deletes:

-   All users in the tenant
-   All bots and documents
-   All embeddings from vector store
-   All conversations and feedback
-   All analytics data
-   Tenant record itself

**And** deletion completes within 30 days (GDPR requirement)  
**And** confirmation email is sent

**Given** I click "Export My Data" (Data Portability)  
**Then** a ZIP file is generated containing:

-   User profile (JSON)
-   All documents (original files)
-   Verified KB entries (JSON)
-   Conversation history (JSON)
-   Analytics summary (CSV)

**Prerequisites:** Story 1.6

**Technical Notes:**

-   Async job for deletion with audit log
-   Export excludes other users' data
-   Covers FR61, FR62

---

### Story 8.5: Audit Trail & AI Labeling

**As a** System,  
**I want** to log all AI actions and clearly label AI-generated content,  
**So that** we comply with EU AI Act transparency requirements.

**Acceptance Criteria:**

**Given** any AI action occurs  
**Then** an audit log entry is created:

-   Timestamp
-   Action type (query, generation, approval, rejection)
-   Actor (user or system)
-   Input summary
-   Output summary
-   Confidence score

**And** audit logs are immutable (append-only)  
**And** logs are retained for 2 years

**Given** any AI-generated response  
**Then** it includes visible label: "AI Generated"  
**And** in email drafts: footer "This draft was generated by AI"

**And** audit logs are searchable by admins  
**And** API endpoint for audit export

**Prerequisites:** All epics

**Technical Notes:**

-   Separate audit database/table (append-only)
-   Required for EU AI Act compliance
-   Covers FR63, FR64

---

## FR Coverage Matrix

| FR   | Description                | Epic | Stories  |
| ---- | -------------------------- | ---- | -------- |
| FR1  | Register with email/OAuth  | 1    | 1.3, 1.4 |
| FR2  | Create tenant organization | 1    | 1.3      |
| FR3  | Invite team members        | 1    | 1.5      |
| FR4  | Update profile             | 1    | 1.6      |
| FR5  | RLS data isolation         | 1    | 1.2      |
| FR6  | Remove team members        | 1    | 1.6      |
| FR7  | Create multiple bots       | 2    | 2.1      |
| FR8  | Configure bot settings     | 2    | 2.1      |
| FR9  | Set confidence threshold   | 2    | 2.1      |
| FR10 | Delete bot                 | 2    | 2.2      |
| FR11 | Duplicate bot              | 2    | 2.2      |
| FR12 | Bot isolation              | 2    | 2.8      |
| FR13 | Upload documents           | 2    | 2.3      |
| FR14 | Chunk documents            | 2    | 2.4      |
| FR15 | Generate embeddings        | 2    | 2.4      |
| FR16 | Store embeddings           | 2    | 2.4      |
| FR17 | View document list         | 2    | 2.5      |
| FR18 | Delete documents           | 2    | 2.6      |
| FR19 | Reprocess documents        | 2    | 2.7      |
| FR20 | Semantic search            | 3    | 3.1      |
| FR21 | Context-only generation    | 3    | 3.2      |
| FR22 | Citations                  | 3    | 3.3      |
| FR23 | Confidence scoring         | 3    | 3.4      |
| FR24 | Check Verified KB first    | 3, 7 | 3.4, 7.2 |
| FR25 | Refuse out-of-domain       | 3    | 3.2      |
| FR26 | PII redaction              | 3    | 3.5      |
| FR27 | Chat interface             | 4    | 4.1      |
| FR28 | Display citations          | 4    | 4.1      |
| FR29 | Conversation context       | 4    | 4.2      |
| FR30 | User feedback              | 4    | 4.3      |
| FR31 | Low-confidence message     | 4    | 4.4      |
| FR32 | Verified badge             | 4    | 4.4      |
| FR33 | Widget generation          | 4    | 4.5      |
| FR34 | Widget customization       | 4    | 4.5      |
| FR35 | Domain whitelisting        | 4    | 4.6      |
| FR36 | Mobile responsive widget   | 4    | 4.6      |
| FR37 | HITL queue view            | 5    | 5.1      |
| FR38 | Queue item display         | 5    | 5.2      |
| FR39 | Approve draft              | 5    | 5.3      |
| FR40 | Edit draft                 | 5    | 5.3      |
| FR41 | Reject with reason         | 5    | 5.4      |
| FR42 | Keyboard shortcuts         | 5    | 5.5      |
| FR43 | Filter queue               | 5    | 5.5      |
| FR44 | Gmail OAuth                | 6    | 6.1      |
| FR45 | Outlook OAuth              | 6    | 6.2      |
| FR46 | Email monitoring           | 6    | 6.3      |
| FR47 | Email draft generation     | 6    | 6.4      |
| FR48 | Style matching             | 6    | 6.5      |
| FR49 | Email drafts in HITL       | 6    | 6.4      |
| FR50 | Configure folders          | 6    | 6.3      |
| FR51 | Verified KB index          | 7    | 7.1      |
| FR52 | Auto-add approved          | 7    | 7.1      |
| FR53 | Manual Q&A entry           | 7    | 7.3      |
| FR54 | Edit/remove entries        | 7    | 7.4      |
| FR55 | Verified KB priority       | 7    | 7.2      |
| FR56 | Query metrics              | 8    | 8.1      |
| FR57 | HITL rate                  | 8    | 8.1      |
| FR58 | Rejection breakdown        | 8    | 8.2      |
| FR59 | Unanswered questions       | 8    | 8.2      |
| FR60 | CSV export                 | 8    | 8.3      |
| FR61 | GDPR deletion              | 8    | 8.4      |
| FR62 | GDPR export                | 8    | 8.4      |
| FR63 | Audit trail                | 8    | 8.5      |
| FR64 | AI labeling                | 8    | 8.5      |

---

---

## Epic 9: Testing & Quality Assurance (KB Provenance & Isolation)

**Goal:** Ensure KB provenance tracking, group isolation, and RLS enforcement are thoroughly tested.  
**Value:** Users can trust that group data is isolated, bot contributions are tracked, and no data leaks occur across groups or tenants.  
**Test Coverage:** RLS policies, bot/group/tenant isolation, document provenance, RBAC enforcement

---

### Story 9.1: Unit Tests for KB Provenance Metadata

**As a** Developer,  
**I want** unit tests that verify document chunk metadata (bot_id, uploader, tenant_id, group_id) is correctly stored and retrieved,  
**So that** provenance tracking is reliable.

**Acceptance Criteria:**

**Given** a document is uploaded with bot_id and user metadata  
**When** chunks are created from the document  
**Then** each chunk stores:

-   document_id (references parent document)
-   bot_id (which bot uploaded)
-   tenant_id (for RLS)
-   group_id (for group scoping)
-   chunk_index
-   created_at
-   uploaded_by_user_id

**When** I query chunks for a bot  
**Then** only chunks with that bot_id (and matching tenant/group) are returned

**Given** two groups in the same tenant  
**When** each uploads documents  
**Then** Group A chunks have group_id=A, Group B chunks have group_id=B  
**And** querying Group A returns only Group A chunks

**And** 100% code coverage for provenance metadata functions  
**And** tests pass with both PostgreSQL and pgvector extensions

**Prerequisites:** Story 2.5

**Technical Notes:**

-   Test file: `apps/api/tests/test_kb_provenance.py`
-   Use pytest fixtures for test data setup
-   Mock Ollama for embedding tests (or use test container)
-   Covers provenance tracking

---

### Story 9.2: RLS Integration Tests for Group Isolation

**As a** Developer,  
**I want** integration tests that verify RLS policies prevent cross-group data access,  
**So that** group data remains isolated even if queries bypass application logic.

**Acceptance Criteria:**

**Given** User A in Group X and User B in Group Y (both in Tenant 1)  
**When** User A queries the database with their JWT (containing tenant_id=1, group_id=X)  
**Then** they only see documents/chunks with (tenant_id=1, group_id=X)  
**And** they cannot query Group Y data even with direct SQL

**Given** the RLS policy `(tenant_id, group_id) = current_user_claims()`  
**When** a user from a different group tries to access data  
**Then** the query returns 0 rows (RLS blocks it, not application logic)

**Given** User A is removed from Group X  
**When** their session ends and they rejoin Group Z  
**Then** subsequent queries return only Group Z data  
**And** they cannot access cached Group X data

**And** cross-tenant access is blocked by RLS (tenant_id != current_tenant)  
**And** tests simulate realistic JWT claims  
**And** tests run against actual PostgreSQL with RLS enabled

**Prerequisites:** Story 1.8

**Technical Notes:**

-   Test file: `apps/api/tests/test_rls_group_isolation.py`
-   Use testcontainers for PostgreSQL + RLS setup
-   Set session variables: `SET app.current_tenant_id = 'x'; SET app.current_group_id = 'y';`
-   Test both `documents` and `document_chunks` tables
-   Covers RLS enforcement

---

### Story 9.3: E2E Test: Multi-Bot Group KB Upload & Query

**As a** QA,  
**I want** an end-to-end test that verifies multiple bots uploading to the same Group KB and querying with correct provenance,  
**So that** the complete flow works as intended.

**Acceptance Criteria:**

**Given** a group with 2 bots (HR Bot and IT Bot)  
**When** HR Bot uploads "HR Handbook.pdf"  
**Then** chunks are stored with bot_id = HR Bot  
**And** chunk metadata shows uploader as the Manager who triggered upload

**When** IT Bot uploads "IT Policies.md"  
**Then** chunks are stored with bot_id = IT Bot  
**And** chunk metadata shows IT Bot as contributor

**Given** I query the Group KB  
**When** I search for "vacation policy"  
**Then** I get chunks from "HR Handbook.pdf" with bot_id = HR Bot  
**And** chunk source metadata displays: "HR Bot, uploaded by [Name], [date]"

**When** I delete "HR Handbook.pdf"  
**Then** HR Bot's chunks are removed from the KB  
**And** IT Bot's chunks remain  
**And** the Group KB still has access to IT Policies

**And** test runs with Playwright (web UI) and API assertions  
**And** test data is cleaned up after each run  
**And** test covers both happy path and error cases (upload fail, delete fail)

**Prerequisites:** Story 2.5, Story 5.1 (Chat API)

**Technical Notes:**

-   Test file: `tests/e2e/group-kb-multibot.spec.ts` (Playwright)
-   Setup: create tenant → create group → add 2 bots → upload docs → query → verify
-   Use real Ollama or mock embeddings API
-   Assertions: document.provenance.bot_id, document.provenance.uploader_name, etc.

---

### Story 9.4: RBAC Enforcement Tests (Bot CRUD Permissions)

**As a** Developer,  
**I want** tests that verify only authorized roles can perform bot CRUD operations,  
**So that** permissions are enforced at the API layer.

**Acceptance Criteria:**

**Given** an Operator user in a group  
**When** they try POST `/api/groups/{group_id}/bots`  
**Then** API returns 403 Forbidden  
**And** bot is not created

**Given** a Manager user in a group  
**When** they try POST `/api/groups/{group_id}/bots`  
**Then** API returns 201 Created  
**And** bot is successfully created

**Given** an Operator user  
**When** they try DELETE `/api/bots/{bot_id}`  
**Then** API returns 403 Forbidden  
**And** bot is not deleted

**Given** a Manager or Group Admin user  
**When** they try DELETE `/api/bots/{bot_id}`  
**Then** API returns 204 No Content  
**And** bot is deleted

**Given** an Operator user  
**When** they try to upload a document  
**Then** API returns 201 Created (Operators can upload)  
**And** document is created with uploader_id = Operator

**And** all permission checks log audit trail (who attempted what, result)  
**And** tests cover all CRUD endpoints for bots and documents  
**And** tests verify JWT role claim is actually checked (not just UI hiding buttons)

**Prerequisites:** Story 1.8, Story 2.1

**Technical Notes:**

-   Test file: `apps/api/tests/test_rbac_bot_crud.py`
-   Use pytest parametrize to test all role/endpoint combinations
-   Mock JWT tokens with different role claims
-   Assert HTTP status codes and error messages
-   Covers RBAC enforcement in FastAPI

---

### Story 9.5: Integration Test: Ingestion Tagging & Audit Trail

**As a** Developer,  
**I want** tests that verify documents are tagged with tenant_id/group_id/bot_id during ingestion and audit trails are recorded,  
**So that** every document action is traceable.

**Acceptance Criteria:**

**Given** a Manager uploads a document to Group A  
**When** the ingestion pipeline completes  
**Then** the document record has:

-   tenant_id = Group A's tenant
-   group_id = Group A's id
-   bot_id = selected bot id
-   uploaded_by_user_id = Manager's id
-   created_at = timestamp

**When** I query the audit log  
**Then** I see an entry: "User [Name] uploaded [Document] to Group [Name] with bot [Bot Name], 2 chunks created"

**Given** a Manager deletes a document  
**When** deletion completes  
**Then** audit log shows: "User [Name] deleted [Document] from Group [Name]"  
**And** document record is soft-deleted (deleted_at timestamp set)

**And** audit trail is queryable by group, user, date range  
**And** tests verify audit entries cannot be modified (append-only)  
**And** tests cover success and failure cases

**Prerequisites:** Story 2.4, Story 2.5

**Technical Notes:**

-   Audit table: `audit_logs` (id, tenant_id, group_id, user_id, action, resource_type, resource_id, timestamp)
-   Test file: `apps/api/tests/test_ingestion_audit.py`
-   Verify audit trail via direct DB query (RLS-scoped)
-   Soft-delete: documents.deleted_at != NULL

---

## Summary

| Metric                               | Value                                      |
| ------------------------------------ | ------------------------------------------ |
| **Total Epics**                      | 9                                          |
| **Total Stories**                    | 52                                         |
| **FRs Covered**                      | 64/64 (100%)                               |
| **New Stories (Group/RBAC/Testing)** | 8                                          |
| **MVP Scope**                        | All stories (with Epic 9 testing critical) |

### Epic Sequence

1. **Foundation & Auth** → Infrastructure + Users + Groups (blocks everything)
2. **Bot & Knowledge** → Data layer with group scoping & provenance (blocks RAG)
3. **RAG Q&A Engine** → Core AI (blocks Chat, HITL)
4. **Chat Experience** → End-user interface (enables value delivery)
5. **HITL Verification** → Trust layer (core differentiator)
6. **Email Automation** → Major use case (builds on HITL)
7. **Verified KB** → Learning loop (completes trust cycle)
8. **Analytics & Compliance** → ROI proof + legal compliance
9. **Testing & QA** → Provenance & isolation validation (runs in parallel with development)

---

_For implementation: Use the story files to generate individual story implementation plans._

_This document will be updated after UX Design and Architecture workflows to incorporate interaction details and technical decisions._
