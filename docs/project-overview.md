# Veriply — Project Overview

## Executive Summary

**Veriply** is an enterprise AI-powered knowledge base verification platform designed to help organizations maintain accurate, trustworthy information through intelligent question-answering and human-in-the-loop verification workflows.

### Project Classification

- **Type:** Full-Stack SaaS Application (Brownfield)
- **Repository Structure:** Monorepo with 2 main parts (Web + API)
- **Primary Tech Stack:** Next.js 14 (React) + FastAPI (Python) + PostgreSQL + pgvector + Ollama
- **Maturity:** Active Development (Jan 2026)

## Key Features

✅ **Multi-tenant Bot Management** — Create and manage AI-powered knowledge base bots per tenant  
✅ **Document Processing** — Upload, process, and vectorize knowledge base documents  
✅ **RAG Q&A Engine** — Retrieve-Augmented Generation with confidence scoring  
✅ **Human-in-the-Loop (HITL)** — Review low-confidence answers before delivery  
✅ **Email Automation** — Integrate with Gmail for email-based responses  
✅ **Writing Style Matching** — Match bot responses to user writing style  
✅ **Verified Q&A** — Maintain curated knowledge base entries  
✅ **GDPR Compliance** — Data retention, anonymization, right-to-be-forgotten

## Project Structure

```
veriply-monorepo/
├── apps/
│   ├── api/              # FastAPI backend (Python)
│   └── web/              # Next.js frontend (React/TypeScript)
├── packages/
│   └── shared/           # Shared code and types
├── docker/               # Docker configurations
│   ├── nginx/
│   ├── ollama/
│   └── postgres/
├── docs/                 # Project documentation and research
├── storage/              # Local file storage (avatars, documents)
├── tests/                # E2E tests (Playwright)
└── scripts/              # Utility scripts
```

## Tech Stack Summary

### Frontend (`apps/web`)

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| **Framework** | Next.js | 16.0.7 | React meta-framework with app router |
| **UI Library** | shadcn/ui | 0.9.5 | Headless component library |
| **Styling** | Tailwind CSS | Latest | Utility-first CSS |
| **State** | React Context | Built-in | Global state management |
| **Testing** | Playwright + Vitest | Latest | E2E and unit tests |
| **Language** | TypeScript | Latest | Type-safe development |
| **HTTP Client** | Fetch API | Browser | API communication |

### Backend (`apps/api`)

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| **Framework** | FastAPI | Latest | Python async web framework |
| **Database** | PostgreSQL | 16 | Primary data store + pgvector |
| **ORM** | SQLAlchemy | 2.x | Async database ORM |
| **Migrations** | Alembic | Latest | Database schema management |
| **Vector Search** | pgvector | Latest | Vector similarity search in PostgreSQL |
| **LLM** | Ollama | Latest | Local model inference |
| **RAG Library** | LangChain | Latest | RAG orchestration |
| **Cache** | Redis | Alpine | Session and queue caching |
| **Task Queue** | Celery | Latest | Background job processing |
| **Email** | aiosmtplib | Latest | SMTP for email automation |
| **PII Detection** | Presidio | Latest | PII masking and anonymization |
| **Auth** | JWT + bcrypt | Latest | Token-based authentication |
| **Testing** | pytest + pytest-asyncio | Latest | Async test framework |

### Infrastructure

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Containerization** | Docker & Docker Compose | Local development and deployment |
| **Web Server** | Nginx | Reverse proxy and static file serving |
| **Database Host** | PostgreSQL 16 (External) | Centralized database at 10.2.160.214 |
| **Embeddings** | nomic-embed-text (via Ollama) | Text embeddings for vector search |
| **LLM** | Qwen 2.5 (recommended) | Language model for Q&A |

## Architecture Pattern

**Multi-tier Architecture with Service-Oriented Backend:**

- **Presentation Tier:** Next.js frontend with React components
- **API Tier:** FastAPI with RESTful endpoints
- **Service Tier:** Business logic services (auth, bot, chat, email, etc.)
- **Data Tier:** PostgreSQL with pgvector for vectors
- **Background Workers:** Celery for async tasks and email polling
- **External Services:** Ollama for LLM, Gmail API for email integration

## Repository Statistics

- **Total Parts:** 2 (web + api)
- **Primary Languages:** Python (backend), TypeScript (frontend)
- **Key Directories:** apps/api/app/, apps/web/src/
- **Documentation Files:** 25+ markdown files in docs/
- **Configuration Files:** docker-compose.yml, .env.example, tsconfig.json, pyproject.toml equivalents

## Development Workflow

### Getting Started

1. **Clone and Setup**
   ```bash
   git clone <repo>
   cd veriply-monorepo
   npm install  # Installs all workspaces
   ```

2. **Environment Configuration**
   ```bash
   cp .env.example .env
   # Edit .env with your database, API keys, etc.
   ```

3. **Database Initialization**
   - Use external PostgreSQL at `DB_HOST` (default: 10.2.160.214)
   - Alembic migrations run automatically on app startup

4. **Start Development Servers**
   ```bash
   npm run dev          # Runs all services in parallel
   # Or individually:
   npm run dev:web      # Next.js on :3000
   npm run dev:api      # FastAPI on :8000
   npm run dev:worker   # Celery worker
   ```

5. **Testing**
   ```bash
   npm run test         # Run all tests
   npm test:web         # Frontend tests
   npm run test:api     # Backend tests
   npm run test:e2e     # End-to-end Playwright tests
   ```

## Key Business Features

### Story 3.4: Confidence-Based Query Response
- LLM generates confidence scores for answers
- Low-confidence answers routed to HITL queue for human review
- Verified answers stored in database

### Story 4.4: Review Queue Scoping
- Team members can review low-confidence answers
- Scope-based visibility (personal/group/all)
- Approval workflow before response delivery

### Story 6.2-6.5: Email Integration & Automation
- Gmail OAuth2 integration
- Email monitoring rules for auto-reply
- Writing style matching for bot responses
- Email drafts with human review

### Story 7.3: Manual Q&A Entry
- Verified Knowledge Base (separate from AI-generated)
- Manual Q&A creation and management

## Compliance & Security

✅ **GDPR Compliance**
- Data retention policies (90-365 days depending on type)
- Right-to-be-forgotten implementation
- PII anonymization (Presidio)
- Data portability features

✅ **Security**
- JWT token-based authentication
- Row-Level Security (RLS) in PostgreSQL
- Password hashing with bcrypt
- Email credential encryption
- CORS protection
- Rate limiting (recommended)

✅ **Audit & Logging**
- Audit log model for tracking changes
- Background cleanup for inactive users (daily at 2 AM UTC)

## Documentation Index

- [Technology Stack Details](./technology-stack.md) - Detailed tech analysis
- [API Contracts](./api-contracts.md) - All endpoints and schemas
- [Data Models](./data-models.md) - Database schema and relationships
- [Source Tree Analysis](./source-tree-analysis.md) - Directory structure with annotations
- [Development Guide](./development-guide.md) - Setup, build, and test instructions
- [Deployment Guide](./deployment-guide.md) - Deployment configurations
- [Component Inventory](./component-inventory.md) - UI components and design system
- [Architecture Details](./architecture.md) - Existing architecture document

## Team & Contact

- **Project Lead:** Dario (Erasmus Hogeschool Brussel)
- **2025-2026 IT Project**
- **Status:** Active Development

## Quick Links

- 📚 **Product Requirements:** [docs/prd.md](./prd.md)
- 🎨 **UX Design:** [docs/ux-design-specification.md](./ux-design-specification.md)
- 🏗️ **Epics:** [docs/epics.md](./epics.md)
- 📋 **Backlog:** [docs/backlog.md](./backlog.md)
- ✅ **Security Audit:** [docs/SECURITY-AUDIT-REPORT.md](./SECURITY-AUDIT-REPORT.md)
- ⚖️ **GDPR Assessment:** [docs/GDPR-COMPLIANCE-ASSESSMENT-2025-01-09.md](./GDPR-COMPLIANCE-ASSESSMENT-2025-01-09.md)

---

**Generated:** January 11, 2026  
**Scan Level:** Deep (read critical files per project type)  
**Documentation Workflow Version:** 1.2.0
