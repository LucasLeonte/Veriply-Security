# Veriply - Technical Specification

**Author:** Dario
**Date:** 2025-11-27
**Project Level:** SaaS B2B Platform
**Change Type:** Greenfield MVP
**Development Context:** New Monorepo Setup

---

## Context

### Available Documents

-   `docs/prd.md`: Product Requirements Document (v1.0)
-   `docs/epics.md`: Epic & Story Breakdown
-   `docs/ux-color-themes.html`: Design System & Color Palette

### Project Stack

-   **Frontend:** Next.js 14 (App Router), TypeScript, Tailwind CSS, shadcn/ui
-   **Backend:** FastAPI (Python 3.11+), Pydantic, SQLAlchemy (Async)
-   **Database:** PostgreSQL 16 with `pgvector` extension
-   **AI Inference:** **Ollama** (Self-Hosted/Local)
    -   LLM: `llama3` (or `qwen2.5`)
    -   Embeddings: `nomic-embed-text` (or `all-minilm`)
-   **Orchestration:** LangChain (Python)
-   **Queue:** Redis + Celery (for document processing)
-   **Auth:** NextAuth.js (Frontend) + JWT Validation (Backend)
-   **Tenancy Model:** Tenant → Group(s) → Bots; users belong to groups; a group has a single Knowledge Base shared by members; multiple bots per group read/write to that KB with provenance
-   **Infrastructure:** Docker Compose (Monorepo)

### Existing Codebase Structure

-   **Monorepo:** Turborepo-style (already initialized)
    -   `apps/web`: Next.js application
    -   `apps/api`: FastAPI application
    -   `packages/shared`: Shared TypeScript types/configs
    -   `docker`: Infrastructure configuration

---

## The Change

### Problem Statement

Current AI support tools lack trust and verification. Veriply needs a robust, privacy-focused architecture that enables "Human-in-the-Loop" verification of AI answers. The system must run efficiently with local inference (Ollama) to ensure data privacy and reduce costs.

### Proposed Solution

Build a multi-tenant SaaS platform with a "Trust-First" RAG architecture.

1.  **Ingestion:** Secure pipeline to upload, scan (Malware), redact (PII), and embed documents with tenant_id/group_id/bot_id provenance into a single Group KB.
2.  **RAG Engine:** Semantic search via `pgvector` scoped to tenant_id + group_id + KB; Generation via **Ollama**.
3.  **HITL Workflow:** Agent dashboard to review/edit AI drafts before sending; drafts tagged with group/bot for audit.
4.  **Verification:** Approved answers stored in Group KB as verified entries; AI responses cite source chunks.

### Scope

**In Scope:**

-   Monorepo setup (Next.js + FastAPI).
-   Authentication & Multi-tenancy (Tenant → Group → Bots; RLS).
-   \*\*Group management (create/switch), member invites, RBAC (Group Admin / Manager / Operator).
-   Bot management per group; multiple bots share the Group KB with provenance.
-   Document Ingestion (PDF/Text), PII Redaction, Malware Scan with group/bot tagging.
-   RAG Pipeline using Ollama.
-   Agent Dashboard (Inbox, Draft Review, Approval) + Group KB view.
-   Email Integration (OAuth2) & Draft Generation.
-   Basic Analytics.

**Out of Scope:**

-   Billing/Stripe Integration (MVP).
-   Voice/Telephony Support.
-   Multi-channel integrations (WhatsApp/Slack) - Email only for MVP.
-   Advanced RBAC features (team hierarchies, custom roles) — keep 3 core roles for MVP.

---

## Implementation Details

### Source Tree Changes

**Create Monorepo Structure:**

-   `apps/web/`: Next.js Frontend
    -   `app/(dashboard)/`: App Layout (Sidebar, Header)
    -   `components/ui/`: shadcn/ui components
    -   `lib/auth.ts`: NextAuth configuration
-   `apps/api/`: FastAPI Backend
    -   `app/main.py`: Entry point
    -   `app/api/v1/`: API Routes (auth, documents, chat, inbox)
    -   `app/core/`: Config, Security, Database
    -   `app/services/`: Business Logic (ingestion, rag, ollama_client)
    -   `app/models/`: SQLAlchemy Models
-   `docker-compose.yml`: Orchestration for Web, API, DB, Redis, Ollama.

### Technical Approach

**1. AI Inference (Ollama Integration):**

-   Use `ollama` service in Docker Compose.
-   Backend communicates via HTTP (`http://ollama:11434`).
-   **Service Layer:** `OllamaService` in FastAPI to handle prompt construction and streaming responses.
-   **Fallback:** Handle Ollama downtime gracefully (Circuit Breaker).

**2. Database & Multi-Tenancy:**

-   **RLS (Row Level Security):** All core tables (`groups`, `group_members`, `bots`, `documents`, `document_chunks`, `interactions`, `chat_sessions`) carry `tenant_id` and `group_id`; bot-scoped data also stores `bot_id` for provenance.
-   **Session:** Inject `tenant_id` and `group_id` from JWT claims into PostgreSQL session on every request; enforce membership via policies on `group_members`.
-   **Vector Store:** Use `pgvector` for embeddings with composite index `(tenant_id, group_id, embedding)` and IVFFlat for performance; ensure queries always constrain tenant_id + group_id.
-   **RBAC Model:** Three roles per group — `group_admin`, `manager`, `operator`. Stored in `group_members.role` (enum); enforced in API layer via permission decorators and RLS policies on sensitive tables.

**3. Ingestion Pipeline (Async):**

-   Upload -> API -> S3/MinIO (Storage) -> Celery Task.
-   **Task Steps:**
    1.  **Malware Scan:** `clamav` check.
    2.  **Text Extraction:** `pypdf` / `unstructured`.
    3.  **PII Redaction:** `presidio-analyzer` + `presidio-anonymizer`.
    4.  **Embedding:** Call Ollama (`nomic-embed-text`) -> Store in DB with `tenant_id`, `group_id`, `bot_id` metadata.

**4. HITL Workflow:**

-   **Drafts:** Stored in `interactions` table with `status='PENDING_REVIEW'`.
-   **Locking:** Optimistic locking to prevent two agents editing the same draft.
-   **Real-time:** Use Server-Sent Events (SSE) or Polling for Inbox updates.

### Integration Points

-   **Ollama API:** Internal (Docker network).
-   **PostgreSQL:** Internal (Docker network).
-   **Redis:** Internal (Celery Broker).
-   **Google/Microsoft OAuth:** External (for Email integration).

---

## Development Context

### Dependencies

**Backend (Python):**

-   `fastapi`, `uvicorn[standard]`
-   `sqlalchemy[asyncio]`, `alembic`, `asyncpg`
-   `pgvector`
-   `celery`, `redis`
-   `langchain`, `langchain-community`
-   `python-multipart` (uploads)
-   `pydantic-settings`

**Frontend (Node/TS):**

-   `next`, `react`, `react-dom`
-   `tailwindcss`, `postcss`, `autoprefixer`
-   `lucide-react` (icons)
-   `next-auth`
-   `@tanstack/react-query` (data fetching & state management)
-   `shadcn-ui` (components)

### Configuration Changes

**Environment Variables (.env):**

```bash
# Database
DATABASE_URL=postgresql+asyncpg://user:pass@db:5432/veriply

# Auth
NEXTAUTH_SECRET=...
NEXTAUTH_URL=http://localhost:3000

# AI
OLLAMA_BASE_URL=http://ollama:11434
LLM_MODEL=llama3
EMBEDDING_MODEL=nomic-embed-text

# Object Storage
MINIO_ENDPOINT=...
MINIO_ACCESS_KEY=...
```

---

## Implementation Stack

-   **Runtime:** Node.js 20.x (Frontend), Python 3.11 (Backend)
-   **Frameworks:** Next.js 14, FastAPI 0.109+
-   **Database:** PostgreSQL 16
-   **AI:** Ollama (v0.1.20+)

---

## Technical Details

**Ollama Docker Setup:**
We need a custom Dockerfile or entrypoint for Ollama to pull models on startup:

```dockerfile
FROM ollama/ollama
COPY ./pull-models.sh /pull-models.sh
ENTRYPOINT ["/bin/bash", "/pull-models.sh"]
```

_Script:_ Start server -> `ollama pull llama3` -> `ollama pull nomic-embed-text` -> Keep running.

---

## Recent Backend Updates (Dec 2025)

### Embeddings and Vector Store Alignment

- Embedding model: `nomic-embed-text` via Ollama HTTP API
    - Endpoint: `POST /api/embeddings`
    - Payload: `{ "model": "nomic-embed-text", "prompt": "<text>" }`
    - Response field: `embedding` (length 768)
- Application expects and validates 768-dim vectors.
- Database column `chunks.vector` is `vector(768)` (pgvector) with HNSW index; cosine distance is used for similarity.

### Group-Scoped Knowledge Base and Processing

- Knowledge base is scoped at the Group level (multi-bot shared KB per group).
- Upload path: `POST /api/v1/groups/{group_id}/documents/upload`
    - Files are stored under: `storage/documents/groups/{group_id}/documents/{filename}`
    - Processing is executed asynchronously by `app/workers/group_document_processor.py`:
        1. Extract text (PDF/DOCX/plain fallback)
        2. Chunk into ~200-word segments with overlap
        3. Generate 768-dim embeddings via Ollama
        4. Persist chunks and mark document status `ready`

### Bot-Level Access Control (Allowlist)

- Access is controlled via `BotDocumentAccess` records:
    - Explicit document access: allow or deny
    - Folder-level access: allow all docs within a folder
    - Explicit deny overrides any allow (including folder allow)
- Management API:
    - Set document access: `POST /api/v1/bots/{bot_id}/access/documents/{document_id}` `{ is_allowed: boolean }`
    - Set folder access: `POST /api/v1/bots/{bot_id}/access/folders/{folder_id}` `{ is_allowed: boolean }`
    - Bulk set: `POST /api/v1/bots/{bot_id}/access/bulk`
    - Summary: `GET /api/v1/bots/{bot_id}/access`

### Semantic Search Endpoint

- New endpoint for direct vector search (no LLM call):
    - `POST /api/v1/bots/{bot_id}/search`
    - Body: `{ query: string, k?: number = 5, similarity_threshold?: number = 0.5 }`
    - Returns: top chunks with similarity and document metadata
- Backed by `VectorSearchService`, which enforces the bot allowlist rules above and filters by tenant + group.

### Query (LLM) Endpoint

- `POST /api/v1/bots/{bot_id}/query` continues to use `VectorSearchService` for retrieval, thus inheriting the same allowlist enforcement; it then streams/generates the answer via the LLM service.

### Notes

- Any previous assumptions of per-chunk `bot_id` have been removed in favor of Group-scoped storage and bot allowlists.
- Ensure Ollama is running locally and the `nomic-embed-text` model is pulled before starting the API for successful embeddings.

**RAG Retrieval Logic:**

```python
# Hybrid Search Concept (Future) but Semantic for MVP
results = await session.execute(
    select(DocumentChunk)
    .filter(DocumentChunk.tenant_id == current_tenant.id)
    .filter(DocumentChunk.group_id == current_group.id)
    .order_by(DocumentChunk.embedding.cosine_distance(query_vector))
    .limit(5)
)
```

**Role-Based Access Control (RBAC):**

Three roles per group:

| Role            | Group Mgmt | Bot/Doc Mgmt | Submit | Approve | View KB |
| --------------- | ---------- | ------------ | ------ | ------- | ------- |
| **Group Admin** | ✓          | ✓            | ✓      | ✓       | ✓       |
| **Manager**     | ✗          | ✓            | ✓      | ✓       | ✓       |
| **Operator**    | ✗          | ✗            | ✓      | ✗       | ✓       |

**Database Schema:**

```python
class GroupMember(Base):
    __tablename__ = "group_members"
    id = Column(UUID, primary_key=True)
    group_id = Column(UUID, ForeignKey("groups.id"), index=True)
    user_id = Column(UUID, ForeignKey("users.id"), index=True)
    role = Column(Enum(RoleEnum))  # 'group_admin', 'manager', 'operator'
    invited_at = Column(DateTime, default=utcnow)
    invited_by_id = Column(UUID)  # who invited them
```

**Permission Patterns (FastAPI):**

```python
# Decorator for permission checks
def require_role(*allowed_roles):
    async def decorator(request, group_id: UUID, ...):
        member = await get_group_member(user_id, group_id)
        if member.role not in allowed_roles:
            raise HTTPException(403, "Insufficient permissions")
    return decorator

# Usage:
@router.post("/groups/{group_id}/bots")
@require_role('group_admin', 'manager')
async def create_bot(...):
    ...

@router.post("/interactions/{id}/approve")
@require_role('group_admin', 'manager')
async def approve_draft(...):
    ...
```

---

## Development Setup

1.  **Prerequisites:** Docker Desktop, Node.js 20+, Python 3.11+.
2.  **Clone & Install:**
    ```bash
    git clone <repo>
    npm install # Root dependencies
    ```
3.  **Start Infrastructure:**
    ```bash
    docker-compose up -d db redis ollama minio
    ```
4.  **Initialize Models:**
    -   Wait for Ollama to pull models (check logs).
5.  **Run Apps:**
    ```bash
    npm run dev # Starts Next.js and FastAPI (via concurrently or separate terminals)
    ```

### Version Control & Workflow

-   **Platform:** GitHub.
-   **Branching Strategy:** GitHub Flow.
    -   `main`: Production-ready code. Protected branch.
    -   `feat/<feature-name>`: New features (e.g., `feat/auth-login`).
    -   `fix/<bug-name>`: Bug fixes (e.g., `fix/upload-error`).
    -   `chore/<task-name>`: Maintenance/Config (e.g., `chore/update-deps`).
-   **Organization:**
    -   **Pull Requests:** All changes must be submitted via PR.
    -   **Reviews:** Code must be reviewed before merging.
    -   **Commits:** Use conventional commits (e.g., `feat: add login page`).

**Branch Protection Rules (Main):**

-   Require pull request reviews before merging (Minimum 1 reviewer).
-   Require status checks to pass before merging (CI/CD).
-   Require linear history (Squash merging recommended).
-   Do not allow bypassing the above settings.

**CI/CD Pipeline (GitHub Actions):**

-   **Triggers:** Push to `main`, Pull Request to `main`.
-   **Jobs:**
    -   `lint`: Run ESLint (Frontend) and Ruff/Black (Backend).
    -   `test`: Run `vitest` (Frontend) and `pytest` (Backend).
    -   `build`: Verify Docker build succeeds.

---

## Implementation Guide

### Phase 1: Foundation (Epic 1)

1.  Set up Monorepo & Docker Compose (incl. Ollama).
2.  Initialize FastAPI with SQLAlchemy & Alembic.
3.  Implement Tenant/User/Group models, membership, RLS (tenant_id + group_id), JWT claims enforcement.
4.  Setup Next.js with Shadcn UI, Login Page, Group switcher shell.

### Phase 2: Ingestion & KB (Epic 2)

1.  Implement File Upload API (MinIO) with tenant/group/bot metadata.
2.  Create Celery Worker for processing.
3.  Implement PII Redaction & Embedding (Ollama) writing to Group KB.
4.  Build Group KB UI (documents, chunks provenance per bot).

### Phase 3: Bots, RAG & Chat (Epic 3)

1.  Implement Bot model (per group), bot selection in chat.
2.  Implement Chat API with Streaming scoped to tenant/group; bot_id recorded on sessions.
3.  Connect to Ollama for generation with citations; Build Chat UI with bot picker.

### Phase 4: HITL & Email (Epic 4)

1.  Implement "Interactions" model (Drafts) scoped by group/bot.
2.  Build Agent Inbox & Review UI; approve to Group KB.
3.  Integrate Email OAuth & Polling for group inbox.

### Testing Strategy

-   **Backend:** `pytest` with `testcontainers` (Postgres); add RLS isolation tests (cross-tenant and cross-group denial), membership-required tests, ingestion provenance tests.
-   **Frontend:** `vitest` for components; add tests for group switcher, bot picker, and KB listing.
-   **E2E:** Playwright (Critical flows: Login -> Select Group -> Upload -> Chat -> Approve Draft).

---

## UX/UI Considerations

-   **Theme:** Cool Slate direction (per design-direction-coolslate.html) with group switcher and multi-bot list.
-   **Trust Indicators:**
    -   Use **Amber** badges for AI Drafts.
    -   Use **Green** badges for Verified Answers.
-   **Streaming:** Ensure chat responses stream smoothly to reduce perceived latency.
-   **Citations:** Display citations clearly below answers.

---

## Deployment Strategy

-   **MVP:** Docker Compose on a single VPS (e.g., Hetzner/AWS EC2).
-   **Hardware:** Requires sufficient RAM (16GB+) for Ollama/Llama3. GPU recommended but not strictly required for MVP (CPU inference is acceptable for low volume).
-   **CI/CD:** GitHub Actions to build images and push to registry.
