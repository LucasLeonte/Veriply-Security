# Veriply — Source Tree Analysis

## Project Structure Overview

```
veriply-monorepo/
│
├── 📂 apps/                          # Main application parts
│   │
│   ├── 📂 api/                       # FastAPI Backend (Python)
│   │   ├── app/                      # Main application code
│   │   │   ├── api/                  # API route organization
│   │   │   │   ├── v1/               # API v1 routes (versioned)
│   │   │   │   │   ├── auth.py       # Authentication endpoints
│   │   │   │   │   ├── profile.py    # User profile management
│   │   │   │   │   ├── groups.py     # Team/group management
│   │   │   │   │   ├── bots.py       # Bot CRUD operations
│   │   │   │   │   ├── documents.py  # Document management
│   │   │   │   │   ├── folders.py    # Folder organization
│   │   │   │   │   ├── bot_access.py # Bot access control
│   │   │   │   │   ├── gdpr.py       # GDPR compliance endpoints
│   │   │   │   │   ├── knowledge_base.py  # KB queries
│   │   │   │   │   ├── review_queue.py    # Review queue (low confidence)
│   │   │   │   │   ├── query.py      # Legacy query endpoint
│   │   │   │   │   ├── schemas.py    # Pydantic request/response schemas
│   │   │   │   │   └── __init__.py
│   │   │   │   └── routes/           # Additional routes
│   │   │   │       ├── query.py      # Query execution
│   │   │   │       ├── chat.py       # Chat endpoint (public + auth)
│   │   │   │       ├── chat_history.py     # Chat message history
│   │   │   │       ├── feedback.py   # User feedback collection
│   │   │   │       ├── analytics.py  # Analytics metrics
│   │   │   │       ├── hitl.py       # Human-in-the-loop review queue
│   │   │   │       ├── integrations.py     # Email integrations (Gmail)
│   │   │   │       ├── email_rules.py     # Email monitoring rules
│   │   │   │       ├── kb_emails.py  # KB email management
│   │   │   │       ├── verified_qa.py     # Manual Q&A entry
│   │   │   │       ├── email_drafts.py    # Email draft generation
│   │   │   │       └── writing_style.py   # User writing style matching
│   │   │   │
│   │   │   ├── 📂 core/              # Core utilities and setup
│   │   │   │   ├── database.py       # SQLAlchemy async session setup
│   │   │   │   ├── migrations.py     # Database initialization (pgvector, RLS)
│   │   │   │   ├── settings.py       # Environment configuration (Pydantic)
│   │   │   │   └── __init__.py
│   │   │   │
│   │   │   ├── 📂 models/            # SQLAlchemy ORM models
│   │   │   │   ├── base.py           # Base model with UUID primary key
│   │   │   │   ├── user.py           # User model (with tenant FK)
│   │   │   │   ├── tenant.py         # Tenant/organization model
│   │   │   │   ├── bot.py            # Bot model
│   │   │   │   ├── group.py          # Team/group model
│   │   │   │   ├── document.py       # Knowledge base document
│   │   │   │   ├── folder.py         # Document folder/category
│   │   │   │   ├── chat_message.py   # Chat message history
│   │   │   │   ├── chunk.py          # Document chunk (for vector search)
│   │   │   │   ├── embedding.py      # Vector embedding storage
│   │   │   │   ├── confidence_log.py # LLM confidence tracking
│   │   │   │   ├── audit_log.py      # Audit trail for compliance
│   │   │   │   ├── feedback.py       # User feedback on answers
│   │   │   │   ├── verified_qa.py    # Manual Q&A entries
│   │   │   │   ├── integration_credentials.py  # OAuth tokens
│   │   │   │   ├── email_integration.py       # Email integration config
│   │   │   │   ├── email_monitoring_rule.py   # Email auto-reply rules
│   │   │   │   ├── email_draft.py    # Generated email drafts
│   │   │   │   ├── email_processing_queue.py  # Email processing queue
│   │   │   │   ├── kb_email.py       # Email-derived KB entries
│   │   │   │   ├── user_email_history.py     # User email interactions
│   │   │   │   ├── user_writing_style.py     # Writing style profile
│   │   │   │   ├── widget_config.py  # Bot widget configuration
│   │   │   │   └── bot_document_access.py    # Bot access to documents
│   │   │   │
│   │   │   ├── 📂 services/          # Business logic
│   │   │   │   ├── auth_service.py   # JWT token & password handling
│   │   │   │   ├── user_service.py   # User registration & management
│   │   │   │   ├── bot_service.py    # Bot creation & lifecycle
│   │   │   │   ├── chat_service.py   # Chat/Q&A execution
│   │   │   │   ├── rag_service.py    # RAG pipeline (retrieve + augment)
│   │   │   │   ├── embedding_service.py     # Document embedding
│   │   │   │   ├── llm_service.py    # LLM inference (Ollama)
│   │   │   │   ├── email_service.py  # Email sending via SMTP
│   │   │   │   ├── gmail_service.py  # Gmail API integration
│   │   │   │   ├── profile_service.py       # User profile operations
│   │   │   │   ├── group_service.py  # Team management
│   │   │   │   └── compliance_service.py    # GDPR operations
│   │   │   │
│   │   │   ├── 📂 workers/           # Background task workers
│   │   │   │   ├── email_poller.py   # Gmail polling worker
│   │   │   │   ├── email_processor.py       # Email response generation
│   │   │   │   ├── retention.py      # Data retention cleanup
│   │   │   │   └── __init__.py
│   │   │   │
│   │   │   ├── 📂 integrations/      # External service clients
│   │   │   │   ├── gmail_client.py   # Gmail API wrapper
│   │   │   │   ├── presidio_client.py       # PII detection/masking
│   │   │   │   └── __init__.py
│   │   │   │
│   │   │   ├── 📂 lib/               # Shared utilities
│   │   │   │   ├── rag.py            # RAG pipeline logic
│   │   │   │   ├── embedding.py      # Embedding generation
│   │   │   │   ├── pii_handler.py    # PII detection & anonymization
│   │   │   │   └── __init__.py
│   │   │   │
│   │   │   ├── 📂 email_automation/  # Email feature helpers
│   │   │   │   └── __init__.py
│   │   │   │
│   │   │   ├── 📂 utils/             # General utilities
│   │   │   │   ├── logger.py         # Logging setup
│   │   │   │   ├── exceptions.py     # Custom exception classes
│   │   │   │   └── __init__.py
│   │   │   │
│   │   │   ├── main.py               # FastAPI app initialization & lifespan
│   │   │   ├── worker.py             # Celery worker entrypoint
│   │   │   ├── tasks.py              # Celery task definitions
│   │   │   ├── check_integrations.py # Integration validation script
│   │   │   └── __init__.py
│   │   │
│   │   ├── requirements.txt           # Python dependencies (FastAPI, SQLAlchemy, etc.)
│   │   ├── pytest.ini                 # Pytest configuration
│   │   └── pyproject.toml             # Project metadata
│   │
│   └── 📂 web/                       # Next.js Frontend (TypeScript/React)
│       ├── 📂 src/
│       │   │
│       │   ├── 📂 app/               # Next.js App Router pages
│       │   │   ├── (auth)/           # Auth layout
│       │   │   │   ├── login/
│       │   │   │   ├── signup/
│       │   │   │   ├── forgot-password/
│       │   │   │   └── reset-password/
│       │   │   ├── (dashboard)/      # Protected dashboard pages
│       │   │   │   ├── dashboard/    # Main dashboard
│       │   │   │   ├── knowledge-base/  # KB management
│       │   │   │   ├── inbox/        # Chat/email inbox
│       │   │   │   ├── analytics/    # Analytics dashboard
│       │   │   │   ├── settings/     # User settings
│       │   │   │   ├── groups/       # Team management
│       │   │   │   ├── profile/      # User profile
│       │   │   │   ├── integrations/ # Email integration setup
│       │   │   │   └── api/          # API client layer
│       │   │   ├── privacy-policy/
│       │   │   ├── terms-of-service/
│       │   │   ├── accept-invite/    # Group invite acceptance
│       │   │   ├── accept-group-invite/
│       │   │   ├── layout.tsx        # Root layout
│       │   │   ├── page.tsx          # Homepage
│       │   │   └── globals.css       # Global styles
│       │   │
│       │   ├── 📂 components/        # Reusable React components
│       │   │   ├── ui/               # Base UI components (shadcn/ui)
│       │   │   ├── chat/             # Chat UI components
│       │   │   ├── bot/              # Bot management components
│       │   │   ├── knowledge-base/   # KB components
│       │   │   ├── email-rules/      # Email rules UI
│       │   │   ├── emails/           # Email management UI
│       │   │   ├── hitl/             # HITL review UI
│       │   │   ├── modals/           # Modal dialogs
│       │   │   ├── analytics/        # Analytics charts
│       │   │   ├── integrations/     # Integration components
│       │   │   ├── verified-kb/      # Verified Q&A UI
│       │   │   ├── DashboardLayout.tsx  # Main layout
│       │   │   ├── Header.tsx        # Navigation header
│       │   │   ├── Sidebar.tsx       # Left sidebar
│       │   │   ├── GroupSwitcher.tsx # Tenant/group switcher
│       │   │   ├── BotCard.tsx       # Bot display component
│       │   │   ├── FeedbackBar.tsx   # Feedback UI
│       │   │   └── ...               # Other shared components
│       │   │
│       │   ├── 📂 hooks/             # Custom React hooks
│       │   │   ├── useAuth.ts        # Authentication state
│       │   │   ├── useBot.ts         # Bot operations
│       │   │   ├── useChat.ts        # Chat operations
│       │   │   └── ...               # Other custom hooks
│       │   │
│       │   ├── 📂 contexts/          # React Context providers
│       │   │   ├── AuthContext.tsx   # Global auth state
│       │   │   ├── TenantContext.tsx # Tenant/group context
│       │   │   └── ...               # Other contexts
│       │   │
│       │   ├── 📂 lib/               # Utilities
│       │   │   ├── api.ts            # API client wrapper
│       │   │   ├── auth.ts           # Auth utilities
│       │   │   └── ...               # Other helpers
│       │   │
│       │   ├── 📂 types/             # TypeScript type definitions
│       │   │   ├── api.ts            # API response types
│       │   │   ├── models.ts         # Domain model types
│       │   │   └── ...               # Other type definitions
│       │   │
│       │   ├── providers.tsx         # Global providers setup
│       │   ├── proxy.ts              # API proxy configuration
│       │   └── ...                   # Other root files
│       │
│       ├── 📂 public/                # Static assets (favicon, images)
│       ├── next.config.ts            # Next.js configuration
│       ├── tsconfig.json             # TypeScript configuration
│       ├── tailwind.config.ts        # Tailwind CSS configuration
│       ├── postcss.config.js         # PostCSS plugins
│       ├── .eslintrc.json            # ESLint rules
│       ├── package.json              # Frontend dependencies
│       └── vitest.config.ts          # Vitest test runner config
│
├── 📂 packages/                      # Shared libraries
│   └── shared/                       # Shared types and utilities
│       ├── src/
│       │   ├── types.ts              # Shared type definitions
│       │   ├── schemas.ts            # Shared validation schemas
│       │   └── utils.ts              # Shared utility functions
│       └── package.json
│
├── 📂 docker/                        # Docker configurations
│   ├── nginx/                        # Nginx reverse proxy
│   │   ├── nginx.conf                # Nginx configuration
│   │   └── Dockerfile                # Nginx image
│   ├── ollama/                       # Ollama LLM setup
│   │   └── Dockerfile                # Ollama image
│   └── postgres/                     # PostgreSQL setup (optional)
│       └── Dockerfile                # Postgres image
│
├── 📂 docs/                          # Project documentation
│   ├── architecture.md               # Architecture overview
│   ├── prd.md                        # Product requirements
│   ├── ux-design-specification.md    # UI/UX design specs
│   ├── epics.md                      # Feature epics
│   ├── backlog.md                    # Product backlog
│   ├── tech-spec.md                  # Technical specification
│   ├── SECURITY-AUDIT-REPORT.md      # Security assessment
│   ├── GDPR-COMPLIANCE-ASSESSMENT-2025-01-09.md
│   ├── DATA-RETENTION-POLICY.md
│   ├── PRIVACY-POLICY.md
│   ├── TERMS-OF-SERVICE.md
│   ├── mockups/                      # UI mockups
│   └── sprint-artifacts/             # Sprint-specific docs
│
├── 📂 storage/                       # Local persistent storage
│   ├── avatars/                      # User avatar images
│   └── documents/                    # Uploaded documents
│
├── 📂 tests/                         # End-to-end tests
│   ├── e2e/                          # Playwright E2E tests
│   │   ├── auth.spec.ts
│   │   ├── chat.spec.ts
│   │   ├── bot-management.spec.ts
│   │   └── ...
│   └── playwright.config.ts
│
├── 📂 scripts/                       # Utility scripts
│   ├── setup.sh                      # Setup script
│   ├── migrate.sh                    # Migration runner
│   ├── apply_rls_security.py         # RLS setup
│   ├── check_approval_activity.py    # Activity checks
│   └── ...                           # Other helper scripts
│
├── 📄 docker-compose.yml             # Multi-container orchestration
├── 📄 .env.example                   # Environment template
├── 📄 .gitignore                     # Git ignore rules
├── 📄 package.json                   # Monorepo root package
├── 📄 README.md                      # Project README
└── 📄 playwright.config.ts           # E2E test config
```

## Critical Directories & Purposes

| Directory | Purpose | Key Files |
|-----------|---------|-----------|
| `apps/api/app/api/v1/` | Versioned API endpoints | auth.py, bots.py, documents.py, review_queue.py |
| `apps/api/app/api/routes/` | Additional API routes | chat.py, query.py, analytics.py, integrations.py |
| `apps/api/app/models/` | SQLAlchemy ORM models | user.py, bot.py, chat_message.py, embedding.py |
| `apps/api/app/services/` | Business logic | chat_service.py, rag_service.py, llm_service.py |
| `apps/api/app/workers/` | Async background tasks | email_poller.py, retention.py |
| `apps/web/src/app/` | Next.js pages (App Router) | dashboard/, knowledge-base/, analytics/ |
| `apps/web/src/components/` | React components | DashboardLayout.tsx, BotCard.tsx, FeedbackBar.tsx |
| `docs/` | Project documentation | prd.md, architecture.md, ux-design-specification.md |

## API Endpoints Overview

### Authentication (`/api/v1/auth/`)
- `POST /register` — Create new account
- `POST /login` — Login with credentials
- `POST /refresh` — Refresh JWT token

### Bots (`/api/v1/groups/{group_id}/bots`)
- `GET` — List bots in group
- `POST` — Create bot
- `GET /{bot_id}` — Get bot details
- `PUT /{bot_id}` — Update bot
- `DELETE /{bot_id}` — Delete bot

### Chat & Q&A
- `POST /api/v1/bots/{bot_id}/public` — Public chat (no auth)
- `POST /api/v1/bots/{bot_id}/chat/query` — Authenticated query with history
- `GET /api/v1/chat/history` — User chat history

### HITL Review Queue
- `GET /api/v1/hitl/queue` — Get low-confidence items
- `POST /api/v1/hitl/queue/{queue_id}/approve` — Approve answer
- `POST /api/v1/hitl/queue/{queue_id}/reject` — Reject answer

### Email Integration
- `GET /api/v1/integrations` — List email integrations
- `POST /api/v1/integrations/gmail/oauth` — Start Gmail OAuth
- `GET /api/v1/email-rules` — Email monitoring rules
- `POST /api/v1/email-drafts/queue/{queue_id}/retry` — Retry email

### Documents & KB
- `GET /api/v1/groups/{group_id}/documents` — List documents
- `POST /api/v1/groups/{group_id}/documents` — Upload document
- `GET /api/v1/verified-qa` — Get verified Q&A entries
- `POST /api/v1/verified-qa` — Create manual Q&A

### User & Profile
- `GET /api/v1/profile/me` — Get current user
- `PUT /api/v1/profile/me` — Update profile
- `DELETE /api/v1/profile/me` — Delete account (GDPR)
- `GET /api/v1/profile/export` — Export user data (GDPR)

### Analytics
- `GET /api/v1/analytics/dashboard` — Dashboard metrics
- `POST /api/v1/feedback` — Submit answer feedback

## Frontend Pages Structure

| Route | Purpose | Authentication |
|-------|---------|-----------------|
| `/` | Homepage | Public |
| `/login` | Login form | Public |
| `/signup` | Registration | Public |
| `/forgot-password` | Password reset | Public |
| `/dashboard` | Main dashboard | Required |
| `/knowledge-base` | KB management | Required |
| `/inbox` | Chat/email inbox | Required |
| `/analytics` | Analytics dashboard | Required |
| `/settings` | User settings | Required |
| `/groups` | Team management | Required |
| `/integrations` | Email setup | Required |

## Entry Points

- **Backend:** `apps/api/app/main.py` — FastAPI app initialization
- **Frontend:** `apps/web/src/app/layout.tsx` — Root layout & providers
- **Worker:** `apps/api/app/worker.py` — Celery background tasks

---

**Generated:** January 11, 2026  
**Scan Level:** Deep Scan (Critical directories analyzed)
