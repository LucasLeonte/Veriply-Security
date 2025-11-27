# Veriply - Technical Specification

**Author:** Dario
**Date:** 2025-11-27
**Project Level:** SaaS B2B Platform
**Change Type:** Greenfield MVP
**Development Context:** New Monorepo Setup

---

## Context

### Available Documents

*   `docs/prd.md`: Product Requirements Document (v1.0)
*   `docs/epics.md`: Epic & Story Breakdown
*   `docs/ux-color-themes.html`: Design System & Color Palette

### Project Stack

*   **Frontend:** Next.js 14 (App Router), TypeScript, Tailwind CSS, shadcn/ui
*   **Backend:** FastAPI (Python 3.11+), Pydantic, SQLAlchemy (Async)
*   **Database:** PostgreSQL 16 with `pgvector` extension
*   **AI Inference:** **Ollama** (Self-Hosted/Local)
    *   LLM: `llama3` (or `qwen2.5`)
    *   Embeddings: `nomic-embed-text` (or `all-minilm`)
*   **Orchestration:** LangChain (Python)
*   **Queue:** Redis + Celery (for document processing)
*   **Auth:** NextAuth.js (Frontend) + JWT Validation (Backend)
*   **Infrastructure:** Docker Compose (Monorepo)

### Existing Codebase Structure

*   **Greenfield Project:** No existing code.
*   **Proposed Structure:** Turborepo-style Monorepo
    *   `apps/web`: Next.js application
    *   `apps/api`: FastAPI application
    *   `packages/shared`: Shared TypeScript types/configs
    *   `docker`: Infrastructure configuration

---

## The Change

### Problem Statement

Current AI support tools lack trust and verification. Veriply needs a robust, privacy-focused architecture that enables "Human-in-the-Loop" verification of AI answers. The system must run efficiently with local inference (Ollama) to ensure data privacy and reduce costs.

### Proposed Solution

Build a multi-tenant SaaS platform with a "Trust-First" RAG architecture.
1.  **Ingestion:** Secure pipeline to upload, scan (Malware), redact (PII), and embed documents.
2.  **RAG Engine:** Semantic search via `pgvector` + Generation via **Ollama**.
3.  **HITL Workflow:** Agent dashboard to review/edit AI drafts before sending.
4.  **Verification:** Approved answers are stored in a "Verified KB" for future exact matching.

### Scope

**In Scope:**
*   Monorepo setup (Next.js + FastAPI).
*   Authentication & Multi-tenancy (RLS).
*   Document Ingestion (PDF/Text), PII Redaction, Malware Scan.
*   RAG Pipeline using Ollama.
*   Agent Dashboard (Inbox, Draft Review, Approval).
*   Email Integration (OAuth2) & Draft Generation.
*   Basic Analytics.

**Out of Scope:**
*   Billing/Stripe Integration (MVP).
*   Voice/Telephony Support.
*   Multi-channel integrations (WhatsApp/Slack) - Email only for MVP.
*   Complex RBAC (Simple Admin/Agent roles only).

---

## Implementation Details

### Source Tree Changes

**Create Monorepo Structure:**
*   `apps/web/`: Next.js Frontend
    *   `app/(dashboard)/`: App Layout (Sidebar, Header)
    *   `components/ui/`: shadcn/ui components
    *   `lib/auth.ts`: NextAuth configuration
*   `apps/api/`: FastAPI Backend
    *   `app/main.py`: Entry point
    *   `app/api/v1/`: API Routes (auth, documents, chat, inbox)
    *   `app/core/`: Config, Security, Database
    *   `app/services/`: Business Logic (ingestion, rag, ollama_client)
    *   `app/models/`: SQLAlchemy Models
*   `docker-compose.yml`: Orchestration for Web, API, DB, Redis, Ollama.

### Technical Approach

**1. AI Inference (Ollama Integration):**
*   Use `ollama` service in Docker Compose.
*   Backend communicates via HTTP (`http://ollama:11434`).
*   **Service Layer:** `OllamaService` in FastAPI to handle prompt construction and streaming responses.
*   **Fallback:** Handle Ollama downtime gracefully (Circuit Breaker).

**2. Database & Multi-Tenancy:**
*   **RLS (Row Level Security):** All tables (`documents`, `chats`, `interactions`) must have `tenant_id`.
*   **Session:** Inject `tenant_id` into PostgreSQL session on every request.
*   **Vector Store:** Use `pgvector` for embeddings. Create an IVFFlat index for performance.

**3. Ingestion Pipeline (Async):**
*   Upload -> API -> S3/MinIO (Storage) -> Celery Task.
*   **Task Steps:**
    1.  **Malware Scan:** `clamav` check.
    2.  **Text Extraction:** `pypdf` / `unstructured`.
    3.  **PII Redaction:** `presidio-analyzer` + `presidio-anonymizer`.
    4.  **Embedding:** Call Ollama (`nomic-embed-text`) -> Store in DB.

**4. HITL Workflow:**
*   **Drafts:** Stored in `interactions` table with `status='PENDING_REVIEW'`.
*   **Locking:** Optimistic locking to prevent two agents editing the same draft.
*   **Real-time:** Use Server-Sent Events (SSE) or Polling for Inbox updates.

### Integration Points

*   **Ollama API:** Internal (Docker network).
*   **PostgreSQL:** Internal (Docker network).
*   **Redis:** Internal (Celery Broker).
*   **Google/Microsoft OAuth:** External (for Email integration).

---

## Development Context

### Dependencies

**Backend (Python):**
*   `fastapi`, `uvicorn[standard]`
*   `sqlalchemy[asyncio]`, `alembic`, `asyncpg`
*   `pgvector`
*   `celery`, `redis`
*   `langchain`, `langchain-community`
*   `python-multipart` (uploads)
*   `pydantic-settings`

**Frontend (Node/TS):**
*   `next`, `react`, `react-dom`
*   `tailwindcss`, `postcss`, `autoprefixer`
*   `lucide-react` (icons)
*   `next-auth`
*   `swr` or `tanstack-query` (data fetching)
*   `shadcn-ui` (components)

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

*   **Runtime:** Node.js 20.x (Frontend), Python 3.11 (Backend)
*   **Frameworks:** Next.js 14, FastAPI 0.109+
*   **Database:** PostgreSQL 16
*   **AI:** Ollama (v0.1.20+)

---

## Technical Details

**Ollama Docker Setup:**
We need a custom Dockerfile or entrypoint for Ollama to pull models on startup:
```dockerfile
FROM ollama/ollama
COPY ./pull-models.sh /pull-models.sh
ENTRYPOINT ["/bin/bash", "/pull-models.sh"]
```
*Script:* Start server -> `ollama pull llama3` -> `ollama pull nomic-embed-text` -> Keep running.

**RAG Retrieval Logic:**
```python
# Hybrid Search Concept (Future) but Semantic for MVP
results = await session.execute(
    select(DocumentChunk)
    .filter(DocumentChunk.tenant_id == current_tenant.id)
    .order_by(DocumentChunk.embedding.cosine_distance(query_vector))
    .limit(5)
)
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
    *   Wait for Ollama to pull models (check logs).
5.  **Run Apps:**
    ```bash
    npm run dev # Starts Next.js and FastAPI (via concurrently or separate terminals)
    ```

### Version Control & Workflow

*   **Platform:** GitHub.
*   **Branching Strategy:** GitHub Flow.
    *   `main`: Production-ready code.
    *   `feat/<feature-name>`: New features (e.g., `feat/auth-login`).
    *   `fix/<bug-name>`: Bug fixes (e.g., `fix/upload-error`).
    *   `chore/<task-name>`: Maintenance/Config (e.g., `chore/update-deps`).
*   **Organization:**
    *   **Pull Requests:** All changes must be submitted via PR.
    *   **Reviews:** Code must be reviewed before merging.
    *   **Commits:** Use conventional commits (e.g., `feat: add login page`).

---

## Implementation Guide

### Phase 1: Foundation (Epic 1)
1.  Set up Monorepo & Docker Compose (incl. Ollama).
2.  Initialize FastAPI with SQLAlchemy & Alembic.
3.  Implement Tenant/User models & RLS.
4.  Setup Next.js with Shadcn UI & Login Page.

### Phase 2: Ingestion (Epic 2)
1.  Implement File Upload API (MinIO).
2.  Create Celery Worker for processing.
3.  Implement PII Redaction & Embedding (Ollama).
4.  Build "Knowledge Base" UI.

### Phase 3: RAG & Chat (Epic 3)
1.  Implement Chat API with Streaming.
2.  Connect to Ollama for generation.
3.  Build Chat UI.

### Phase 4: HITL & Email (Epic 4)
1.  Implement "Interactions" model (Drafts).
2.  Build Agent Inbox & Review UI.
3.  Integrate Email OAuth & Polling.

### Testing Strategy
*   **Backend:** `pytest` with `testcontainers` (Postgres).
*   **Frontend:** `vitest` for components.
*   **E2E:** Playwright (Critical flows: Login -> Upload -> Chat).

---

## UX/UI Considerations

*   **Theme:** Deep Ocean (Slate 900 / Slate 50).
*   **Trust Indicators:**
    *   Use **Amber** badges for AI Drafts.
    *   Use **Green** badges for Verified Answers.
*   **Streaming:** Ensure chat responses stream smoothly to reduce perceived latency.
*   **Citations:** Display citations clearly below answers.

---

## Deployment Strategy

*   **MVP:** Docker Compose on a single VPS (e.g., Hetzner/AWS EC2).
*   **Hardware:** Requires sufficient RAM (16GB+) for Ollama/Llama3. GPU recommended but not strictly required for MVP (CPU inference is acceptable for low volume).
*   **CI/CD:** GitHub Actions to build images and push to registry.
