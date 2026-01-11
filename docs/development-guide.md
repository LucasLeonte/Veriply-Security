# Veriply — Development Guide

## Quick Start

### Prerequisites

- **Node.js** 18+ (for npm workspace management)
- **Python** 3.10+ (for FastAPI backend)
- **Docker & Docker Compose** (for PostgreSQL, Redis, Ollama)
- **Git** (for version control)
- **OpenSSL** or similar for environment variable handling on Windows

### Installation Steps

#### 1. Clone Repository

```bash
git clone <repository-url>
cd veriply-monorepo
```

#### 2. Install Dependencies

```bash
# Install all npm workspace dependencies
npm install
```

This installs:
- Root-level dev tools
- `apps/web` dependencies (Next.js, React, etc.)
- `apps/api` npm dependencies (none currently, but structure supports it)
- `packages/shared` shared utilities

#### 3. Setup Environment

```bash
# Copy environment template to .env
cp .env.example .env

# Edit .env with your configuration
# Key variables to set:
# - DB_HOST: PostgreSQL server (default: 10.2.160.214)
# - DB_USER: PostgreSQL username
# - DB_PASSWORD: PostgreSQL password
# - DB_NAME: Database name
# - REDIS_HOST: Redis server
# - REDIS_PASSWORD: Redis password (if needed)
# - OLLAMA_HOST: Ollama inference server
# - OLLAMA_MODEL: LLM model to use
# - JWT_SECRET: Secret key for JWT tokens
# - CORS_ORIGINS: Allowed CORS origins
# - Gmail OAuth credentials (if using email integration)
```

#### 4. Setup Python Virtual Environment

```bash
# Option A: Let npm postinstall do it automatically
npm install  # Already ran above, but this runs setup:api

# Option B: Manual setup
python -m venv .venv

# On Windows:
.venv\Scripts\activate

# On Linux/macOS:
source .venv/bin/activate

# Install Python dependencies
pip install -r apps/api/requirements.txt
```

#### 5. Database Setup

The database migrations run automatically when the API starts:

```bash
# Migrations are handled by Alembic on app startup
# It will:
# - Create all tables from SQLAlchemy models
# - Enable pgvector extension
# - Enable Row-Level Security (RLS)
```

If you need to run migrations manually:

```bash
cd apps/api
# Create a new migration (if needed)
alembic revision --autogenerate -m "Description"

# Run all migrations
alembic upgrade head
```

## Development Workflow

### Starting All Services

```bash
# Start all services concurrently (recommended)
npm run dev
```

This runs:
- **Frontend:** Next.js dev server on `http://localhost:3000`
- **Backend:** FastAPI on `http://localhost:8000`
- **Worker:** Celery background worker for email polling and retention jobs

### Running Services Individually

```bash
# Terminal 1: Frontend
npm run dev:web
# Runs: next dev
# Access: http://localhost:3000

# Terminal 2: Backend
npm run dev:api
# Runs: FastAPI uvicorn on port 8000
# Docs: http://localhost:8000/docs (Swagger UI)
# ReDoc: http://localhost:8000/redoc

# Terminal 3: Background worker
npm run dev:worker
# Runs: Celery worker for email polling and retention jobs
```

### Environment Variables for Development

Create `.env` file in root:

```bash
# Database
DB_HOST=10.2.160.214           # Shared Ubuntu server
DB_PORT=5432
DB_USER=veriply_user
DB_PASSWORD=your_password
DB_NAME=veriply_dev
DATABASE_URL=postgresql+asyncpg://${DB_USER}:${DB_PASSWORD}@${DB_HOST}:${DB_PORT}/${DB_NAME}

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=

# Ollama (LLM)
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=qwen2.5:14b

# API Configuration
DEBUG=true
ENVIRONMENT=development
CORS_ORIGINS=http://localhost:3000,http://localhost:3001

# JWT
JWT_SECRET=your_super_secret_key_change_in_production

# Email (Gmail)
GMAIL_CLIENT_ID=your_gmail_client_id
GMAIL_CLIENT_SECRET=your_gmail_client_secret
GMAIL_REDIRECT_URI=http://localhost:3000/api/auth/gmail/callback

# Email SMTP (for sending)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password

# Email Polling
EMAIL_POLL_INTERVAL_SECONDS=60
```

## Building & Testing

### Building for Production

```bash
# Frontend
npm run build:web

# Backend (no build needed, Python is interpreted)
# But you can verify syntax:
python -m py_compile apps/api/app/main.py

# Create Docker images
docker-compose build
```

### Testing

```bash
# Run all tests (frontend + backend + e2e)
npm run test

# Frontend tests (Vitest)
npm run test:web

# Backend tests (pytest)
npm run test:api

# End-to-end tests (Playwright)
npm run test:e2e
npm run test:e2e:ui    # Interactive mode with UI
```

### Testing Individual Components

```bash
# Backend: Run specific test file
cd apps/api
pytest tests/test_auth.py -v

# Frontend: Run specific test file
cd apps/web
npm run test -- src/components/ChatBox.test.tsx

# E2E: Run specific test
npx playwright test tests/e2e/chat.spec.ts
```

## File Structure & Key Directories

### Backend (`apps/api`)

```
apps/api/
├── app/
│   ├── api/                    # API routes
│   │   ├── v1/                 # Versioned endpoints
│   │   └── routes/             # Additional routes
│   ├── models/                 # SQLAlchemy ORM models
│   ├── services/               # Business logic services
│   ├── workers/                # Background tasks
│   ├── core/                   # Core setup
│   │   ├── database.py         # SQLAlchemy session
│   │   ├── settings.py         # Environment config
│   │   └── migrations.py       # DB initialization
│   ├── main.py                 # FastAPI app
│   └── worker.py               # Celery worker
├── requirements.txt            # Python dependencies
└── pytest.ini                  # Test config
```

### Frontend (`apps/web`)

```
apps/web/
├── src/
│   ├── app/                    # Next.js App Router pages
│   ├── components/             # React components
│   ├── hooks/                  # Custom hooks
│   ├── contexts/               # Context providers
│   ├── lib/                    # Utilities
│   ├── types/                  # TypeScript types
│   ├── globals.css             # Global styles
│   └── providers.tsx           # Root providers
├── public/                     # Static assets
├── next.config.ts              # Next.js config
├── tsconfig.json               # TypeScript config
├── tailwind.config.ts          # Tailwind config
├── package.json                # Dependencies
└── vitest.config.ts            # Test config
```

## Common Development Tasks

### Adding a New API Endpoint

1. **Create schema** in `apps/api/app/api/v1/schemas.py`:

```python
from pydantic import BaseModel

class MyRequest(BaseModel):
    field: str
    value: int

class MyResponse(BaseModel):
    id: str
    message: str
```

2. **Create route** in `apps/api/app/api/v1/my_feature.py`:

```python
from fastapi import APIRouter, Depends
from app.core.database import get_db
from app.api.v1.auth import get_current_user
from .schemas import MyRequest, MyResponse

router = APIRouter(prefix="/api/v1/my-feature", tags=["my-feature"])

@router.post("/", response_model=MyResponse)
async def create_item(req: MyRequest, db=Depends(get_db)):
    # Implementation
    return {"id": "123", "message": "Success"}
```

3. **Register router** in `apps/api/app/main.py`:

```python
from app.api.v1 import my_feature
app.include_router(my_feature.router)
```

4. **Test via Swagger UI:** http://localhost:8000/docs

### Adding a New React Component

1. **Create component** in `apps/web/src/components/MyComponent.tsx`:

```typescript
"use client";
import { Button } from "@/components/ui/button";

export function MyComponent() {
  return (
    <div>
      <Button>Click me</Button>
    </div>
  );
}
```

2. **Use in page** in `apps/web/src/app/dashboard/page.tsx`:

```typescript
import { MyComponent } from "@/components/MyComponent";

export default function Dashboard() {
  return <MyComponent />;
}
```

### Adding a Database Model

1. **Create model** in `apps/api/app/models/my_model.py`:

```python
from sqlalchemy import Column, String, Uuid, ForeignKey
from .base import Base

class MyModel(Base):
    __tablename__ = "my_models"
    
    id = Column(Uuid, primary_key=True)
    tenant_id = Column(Uuid, ForeignKey("tenants.id"), nullable=False)
    name = Column(String(100), nullable=False)
```

2. **Create service** in `apps/api/app/services/my_service.py`:

```python
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.my_model import MyModel

async def create_my_item(db: AsyncSession, **kwargs):
    item = MyModel(**kwargs)
    db.add(item)
    await db.commit()
    return item
```

3. **Create endpoint** (as described above)

## Debugging

### Backend Debugging

```bash
# View logs
# Logs output to stdout by default

# Add logging in code
import logging
logger = logging.getLogger(__name__)
logger.info("Debug message")

# Use FastAPI interactive docs
# http://localhost:8000/docs  # Swagger UI
# http://localhost:8000/redoc # ReDoc
```

### Frontend Debugging

```bash
# Browser DevTools
# Open http://localhost:3000 and press F12

# VSCode Debugger (configure in .vscode/launch.json)
# Add breakpoints and run "Debug: Start Debugging"

# React DevTools Chrome Extension
# Browser console shows React component hierarchy
```

### Database Debugging

```bash
# Connect to PostgreSQL directly
psql -h 10.2.160.214 -U veriply_user -d veriply_dev

# Common queries
SELECT * FROM users;
SELECT * FROM bots;
SELECT * FROM chat_messages;

# Check RLS policies
SELECT * FROM pg_policies;

# Check pgvector status
SELECT * FROM pg_extension;
```

## Deployment Considerations

### Docker Build

```bash
# Build images
docker-compose build

# Run containers
docker-compose up -d

# View logs
docker-compose logs -f api
docker-compose logs -f web
```

### Environment for Production

```bash
# Create .env.production with:
DEBUG=false
ENVIRONMENT=production
CORS_ORIGINS=https://yourdomain.com
JWT_SECRET=<generate-secure-random-key>
# ... (other credentials for production)
```

### Database Migrations in Production

```bash
# Migrations run automatically on app startup
# But you can run manually:
cd apps/api
alembic upgrade head
```

## Performance Optimization

### Frontend

- Use Next.js Image component for optimization
- Code splitting automatic via App Router
- Check bundle size: `npm run build:web` shows size estimates
- Use React.memo for expensive components

### Backend

- Database indexes on frequently queried columns (already in models)
- Vector search uses pgvector HNSW index (fast)
- Async/await for I/O operations
- Connection pooling via SQLAlchemy

## Troubleshooting

### "Cannot connect to PostgreSQL"

```bash
# Check connection string in .env
# Verify DB_HOST is accessible from your network
ping 10.2.160.214

# Check credentials
psql -h 10.2.160.214 -U veriply_user -d veriply_dev
```

### "Module not found" errors

```bash
# Reinstall dependencies
npm install
pip install -r apps/api/requirements.txt
```

### "Port already in use"

```bash
# Find and kill process using port
# On Windows:
netstat -ano | findstr :3000
taskkill /PID <PID> /F

# On Linux/macOS:
lsof -i :3000
kill -9 <PID>
```

### "Email integration failing"

```bash
# Check Gmail OAuth credentials in .env
# Verify SMTP credentials work
# Check email logs in backend console
```

## Useful Commands

```bash
# Clean install
rm -rf node_modules .venv
npm install

# Format code
npm run lint

# Type check (TypeScript)
cd apps/web && npx tsc --noEmit

# Database
alembic current          # Show current migration
alembic history          # Show all migrations
alembic downgrade -1     # Rollback last migration

# Redis
redis-cli                # Connect to Redis
redis-cli FLUSHALL       # Clear all Redis data

# Ollama
curl http://localhost:11434/api/tags  # List available models
```

---

**Generated:** January 11, 2026  
**Scan Level:** Deep Scan  
**Last Updated:** 2025-2026 Development
