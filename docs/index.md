# Veriply Project Documentation Index

## 📚 Welcome to Veriply Documentation

**Veriply** is an enterprise AI-powered knowledge base verification platform. Use this index to navigate comprehensive project documentation.

---

## 🚀 Quick Start

### For Developers

1. **New to the project?** Start here: [Project Overview](./guides/project-overview.md)
2. **Setting up locally?** Follow: [Development Guide](./guides/development-guide.md)
3. **Exploring the codebase?** Review: [Source Tree Analysis](./technical/source-tree-analysis.md)
4. **Integrating with APIs?** Check: [API Contracts](./technical/api-contracts.md)

### For Product/Design

1. **Product vision:** [Product Requirements (PRD)](./product/prd.md)
2. **UI/UX design:** [UX Design Specification](./product/ux-design-specification.md)
3. **Feature planning:** [Epics](./product/epics.md) & [Backlog](./product/backlog.md)

### For Deployment

1. **Deploying the app:** [Deployment Guide](./guides/deployment-guide.md)
2. **Understanding architecture:** [Architecture](./technical/architecture.md)
3. **Security considerations:** [Security Audit Report](./security/SECURITY-AUDIT-REPORT.md)

---

## 📖 Complete Documentation Map

### Core Project Documentation

| Document | Purpose | Audience |
|----------|---------|----------|
| [Project Overview](./guides/project-overview.md) | Executive summary, tech stack, structure | Everyone |
| [Architecture](./technical/architecture.md) | System architecture and design patterns | Architects, Senior Devs |
| [Technology Stack](./guides/project-overview.md#tech-stack-summary) | Detailed tech analysis | Developers |
| [Epics](./product/epics.md) | Major feature definitions | Product, Dev Leads |
| [Product Brief](./product/product-brief-Veriply-2025-11-27.md) | Strategic product vision | Product Managers |

### Development Documentation

| Document | Purpose | Use When |
|----------|---------|----------|
| [Development Guide](./guides/development-guide.md) | Setup, build, test instructions | Setting up local environment |
| [Source Tree Analysis](./technical/source-tree-analysis.md) | Directory structure with annotations | Exploring codebase |
| [API Contracts](./technical/api-contracts.md) | All endpoints, request/response schemas | Building API integrations |
| [Data Models](./technical/data-models.md) | Database schema, ERD, relationships | Database queries, migrations |
| [Tech Spec](./technical/tech-spec.md) | Technical specifications | Implementation planning |

### Deployment & Operations

| Document | Purpose | Use When |
|----------|---------|----------|
| [Deployment Guide](./guides/deployment-guide.md) | Production deployment procedures | Deploying to production |
| [SECURITY-AUDIT-REPORT.md](./security/SECURITY-AUDIT-REPORT.md) | Security assessment findings | Security review, hardening |
| [SECURITY-IMPLEMENTATION-CHECKLIST.md](./security/SECURITY-IMPLEMENTATION-CHECKLIST.md) | Security implementation tasks | Implementing security features |

### Compliance & Governance

| Document | Purpose | Regulatory Focus |
|----------|---------|------------------|
| [GDPR Compliance Assessment](./compliance/GDPR-COMPLIANCE-ASSESSMENT-2025-01-09.md) | GDPR requirements and compliance | Data Privacy (EU) |
| [Data Retention Policy](./compliance/DATA-RETENTION-POLICY.md) | Data lifecycle and retention | Data Management |
| [Data Protection Impact Assessment](./compliance/DATA-PROTECTION-IMPACT-ASSESSMENT.md) | Privacy impact analysis | Data Processing |
| [DPA Subprocessor Template](./compliance/DPA-SUBPROCESSOR-TEMPLATE.md) | Data processor agreements | Legal/Contracts |
| [Privacy Policy](./compliance/PRIVACY-POLICY.md) | User-facing privacy statement | Legal/Users |
| [Terms of Service](./compliance/TERMS-OF-SERVICE.md) | User terms and conditions | Legal/Users |

### Design & UX

| Document | Purpose | For |
|----------|---------|-----|
| [UX Design Specification](./product/ux-design-specification.md) | UI/UX design details | Designers, Frontend Devs |
| [Design Themes - Light](./product/ux-color-themes-light.html) | Color themes (light mode) | Designers |
| [Design Themes - Dark](./product/ux-color-themes.html) | Color themes (dark mode) | Designers |
| [Mockups Directory](./product/mockups/) | UI mockups and wireframes | Product, Design |

### Project Management

| Document | Purpose | Status |
|----------|---------|--------|
| [Backlog](./product/backlog.md) | Product backlog and prioritization | Current sprint |
| [Sprint Status](./product/sprint-status.yaml) | Current sprint tracking | Team sync |
| [Implementation Readiness](./archive/implementation-readiness-report-2025-12-11.md) | Implementation status | Dev planning |

### Research & Discovery

| Document | Purpose | Phase |
|----------|---------|-------|
| [Market Research](./product/research-market-2025-11-27.md) | Market analysis | Discovery |
| [Technical Research](./product/research-technical-2025-11-27.md) | Technical exploration | Discovery |
| [User/Domain Research](./product/research-user-domain-2025-11-27.md) | User personas, workflows | Discovery |
| [Brainstorming Results](./product/brainstorming-session-results-2025-11-27.md) | Ideation outcomes | Discovery |

### Additional Resources

| Document | Purpose |
|----------|---------|
| [Team Coordination](./team/team-coordination.md) | Team structure and processes |
| [Team Welcome](./team/TEAM-WELCOME.md) | New member onboarding |
| [Team Quick Reference](./team/TEAM-QUICK-REF.md) | Quick lookup guide |
| [Moderation Guide](./security/moderation-guide.md) | Content moderation guidelines |
| [Incident Response Plan](./security/INCIDENT-RESPONSE-PLAN.md) | Crisis response procedures |

---

## 🏗️ Project Structure

```
veriply-monorepo/
├── apps/
│   ├── api/              # FastAPI backend (Python)
│   └── web/              # Next.js frontend (React/TypeScript)
├── packages/shared/      # Shared code
├── docker/               # Docker configurations
├── docs/                 # This directory 📌
├── storage/              # Local file storage
├── tests/                # E2E tests
└── scripts/              # Utility scripts
```

See [Source Tree Analysis](./technical/source-tree-analysis.md) for complete structure.

---

## 💻 Technology Stack

**Frontend:**
- Next.js 16 (React, TypeScript)
- shadcn/ui + Tailwind CSS
- Vitest + Playwright E2E

**Backend:**
- FastAPI (Python, async)
- PostgreSQL 16 + pgvector
- SQLAlchemy 2.x (ORM)

**Infrastructure:**
- Docker & Docker Compose
- Ollama (local LLM)
- Redis (caching)
- Alembic (migrations)

See [Technology Stack Summary](./guides/project-overview.md#tech-stack-summary) for details.

---

## 🔑 Key Features

✅ **Multi-tenant Bot Management** — Create, manage, and configure knowledge base bots
✅ **Document Processing** — Upload and vectorize documents with pgvector
✅ **RAG Q&A** — Retrieve-Augmented Generation with confidence scoring
✅ **Human-in-the-Loop (HITL)** — Review low-confidence answers
✅ **Email Integration** — Gmail OAuth and email automation
✅ **Verified Knowledge Base** — Manually curated Q&A entries
✅ **Writing Style Matching** — Adapt responses to user style
✅ **GDPR Compliance** — Data retention, anonymization, right-to-be-forgotten

---

## 🚀 Getting Started

### Clone & Setup

```bash
git clone <repo>
cd veriply-monorepo
npm install
cp .env.example .env
```

### Run Development

```bash
npm run dev
# Frontend: http://localhost:3000
# Backend: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

### Run Tests

```bash
npm run test          # All tests
npm run test:web      # Frontend
npm run test:api      # Backend
npm run test:e2e      # E2E
```

Complete setup guide: [Development Guide](./guides/development-guide.md)

---

## 📊 API Reference

**API Documentation:** [API Contracts](./technical/api-contracts.md)

Key endpoints:
- `POST /api/v1/auth/register` — Create account
- `POST /api/v1/auth/login` — Login
- `POST /api/v1/groups/{group_id}/bots` — Create bot
- `POST /api/v1/bots/{bot_id}/chat/query` — Chat query
- `GET /api/v1/hitl/queue` — HITL review queue
- `POST /api/v1/integrations/gmail/oauth` — Email integration

Interactive API docs: `/docs` (Swagger) or `/redoc`

---

## 🗄️ Database Schema

**Database:** PostgreSQL 16 + pgvector
**Location:** External at 10.2.160.214

Key tables:
- `users` — User accounts
- `bots` — Knowledge base bots
- `documents` — Uploaded documents
- `chunks` — Document segments
- `embeddings` — Vector embeddings (pgvector)
- `chat_messages` — Chat history
- `confidence_logs` — HITL tracking

See [Data Models](./technical/data-models.md) for complete schema.

---

## 🔒 Security & Compliance

### Security

- ✅ JWT token authentication
- ✅ Row-Level Security (RLS) in PostgreSQL
- ✅ Password hashing with bcrypt
- ✅ CORS protection
- ✅ Audit logging
- See [Security Audit Report](./security/SECURITY-AUDIT-REPORT.md)

### Compliance

- ✅ GDPR requirements (data retention, anonymization)
- ✅ PII detection and masking (Presidio)
- ✅ Data portability and export
- ✅ Right-to-be-forgotten implementation
- ✅ Audit trail for compliance
- See [GDPR Compliance Assessment](./compliance/GDPR-COMPLIANCE-ASSESSMENT-2025-01-09.md)

---

## 📋 Sprint & Release Planning

**Current Sprint:** See [Sprint Status](./product/sprint-status.yaml)
**Product Backlog:** [Backlog](./product/backlog.md)
**Readiness Report:** [Implementation Readiness](./archive/implementation-readiness-report-2025-12-11.md)

### Stories by Epic

| Epic | Status | Stories |
|------|--------|---------|
| Core Platform | Complete | Auth, Bots, Chat, Documents |
| HITL Workflow | Complete | Review Queue (4.4), Scoping (4.5) |
| Email Integration | Complete | Gmail OAuth (6.2), Rules (6.3), Style Matching (6.5) |
| Verified KB | Complete | Manual Q&A (7.3) |
| Compliance | Complete | GDPR (8.x), Security (9.x) |

See [Epics](./product/epics.md) for complete mapping.

---

## 👥 Team

- **Project Lead:** Dario (Erasmus Hogeschool Brussel)
- **Academic Context:** 2025-2026 IT Project
- **Team Structure:** [Team Coordination](./team/team-coordination.md)

---

## 📞 FAQ & Support

### Common Questions

**Q: How do I run the project locally?**
A: Follow [Development Guide](./guides/development-guide.md) — takes ~10 minutes.

**Q: Where's the API documentation?**
A: [API Contracts](./technical/api-contracts.md) or interactive `/docs` endpoint.

**Q: How do I deploy to production?**
A: See [Deployment Guide](./guides/deployment-guide.md).

**Q: How is user data protected?**
A: See [GDPR Compliance](./compliance/GDPR-COMPLIANCE-ASSESSMENT-2025-01-09.md) and [Security Audit](./security/SECURITY-AUDIT-REPORT.md).

**Q: Where's the database schema?**
A: [Data Models](./technical/data-models.md) has complete ERD and table definitions.

---

## 🔗 Quick Links

- **Code Repository:** GitHub (link)
- **Bug Tracker:** GitHub Issues
- **Team Wiki:** [Team Coordination](./team/team-coordination.md)
- **Design System:** [UX Design Specification](./product/ux-design-specification.md)
- **Video Tutorials:** (to be added)

---

## 📅 Document Status

| Category | Status | Last Updated |
|----------|--------|---------------|
| Architecture | ✅ Complete | 2025-01-10 |
| API Docs | ✅ Complete | 2025-01-11 |
| Dev Guide | ✅ Complete | 2025-01-11 |
| Deployment | ✅ Complete | 2025-01-11 |
| Security | ✅ Complete | 2025-01-09 |
| GDPR | ✅ Complete | 2025-01-09 |
| Product Docs | ✅ Complete | 2025-11-27 |

---

## 📝 Documentation Generated

**Workflow:** document-project (Deep Scan)
**Generated:** January 11, 2026
**Scan Depth:** Deep (critical files analyzed)
**Files Generated:** 6 documentation files

### Generated Files

1. ✅ [project-overview.md](./guides/project-overview.md) — Project summary
2. ✅ [source-tree-analysis.md](./technical/source-tree-analysis.md) — Code structure
3. ✅ [api-contracts.md](./technical/api-contracts.md) — API endpoints
4. ✅ [data-models.md](./technical/data-models.md) — Database schema
5. ✅ [development-guide.md](./guides/development-guide.md) — Dev setup
6. ✅ [deployment-guide.md](./guides/deployment-guide.md) — Production deployment

### Existing Documentation

26+ existing markdown files documenting product, design, research, and compliance.

---

**Last Updated:** January 11, 2026
**Generated by:** BMAD document-project workflow v1.2.0
**For questions or updates:** Contact project lead

---

## 🎯 Next Steps

- [ ] Review Project Overview for high-level understanding
- [ ] Follow Development Guide for local setup
- [ ] Explore Source Tree Analysis for codebase navigation
- [ ] Check API Contracts for integration points
- [ ] Review deployment guide before production deployment
