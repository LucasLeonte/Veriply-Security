# Veriply
IT Project - AI-Powered Knowledge Base Verification Platform

## Table of Contents
- [Overview](#overview)
- [Architecture](#architecture)
- [Environment Setup](#environment-setup)
- [Centralized Database Setup](#centralized-database-setup)
- [Development Workflow](#development-workflow)
- [Branch Protection Rules](#branch-protection-rules)

## Overview

Veriply is an intelligent platform that helps organizations verify and validate information using AI-powered question answering with human-in-the-loop verification.

**Key Features:**
- Multi-tenant bot management
- Document processing and knowledge base management
- RAG (Retrieval-Augmented Generation) Q&A engine
- Human verification workflow
- Email automation integration

## Architecture

**Tech Stack:**
- **Frontend:** Next.js 14 (React, TypeScript, Tailwind CSS)
- **Backend:** FastAPI (Python, async/await)
- **Database:** PostgreSQL 16 with pgvector extension
- **LLM:** Ollama (local inference)
- **Caching:** Redis
- **Deployment:** Docker Compose

**Monorepo Structure:**
```
Veriply/
├── apps/
│   ├── api/          # FastAPI backend
│   └── web/          # Next.js frontend
├── packages/
│   └── shared/       # Shared code/types
├── docker/           # Docker configurations
├── docs/             # Documentation
└── .env.example      # Environment configuration template
```

## Environment Setup

### Prerequisites
- Docker & Docker Compose
- Git
- Node.js 18+ (for local Next.js development)
- Python 3.11+ (for local FastAPI development)

### Quick Start

1. **Clone the repository:**
   ```bash
   git clone https://github.com/DarioDML/Veriply.git
   cd Veriply
   ```

2. **Set up environment variables:**
   ```bash
   # Copy the example file
   cp .env.example .env
   
   # Edit .env with your configuration
   # See "Environment Variables" section below for details
   ```

3. **Start services with Docker Compose:**
   ```bash
   docker-compose up -d
   ```

4. **Access the application:**
   - **Frontend:** http://localhost:3000
   - **Backend API:** http://localhost:8000
   - **API Docs:** http://localhost:8000/docs
   - **Health Check:** http://localhost:8000/healthz

### Environment Variables

Veriply uses a **single centralized `.env` file** at the repository root for all configuration.

#### Configuration Pattern

```
Root .env (SINGLE SOURCE OF TRUTH)
    ↓
    ├─→ Docker Compose (loads .env automatically)
    ├─→ FastAPI (via settings.py)
    └─→ Next.js (via next.config.ts)
```

#### Required Variables

Generate secure secrets:
```bash
# JWT Secret
python -c 'import secrets; print(secrets.token_urlsafe(32))'

# NextAuth Secret
openssl rand -base64 32
```

Minimum required configuration in `.env`:
```bash
# Database (see Centralized Database Setup section)
DB_HOST=192.168.1.100          # Ubuntu server IP
DB_USER=your_db_username
DB_PASSWORD=your_secure_password

# Authentication
JWT_SECRET=your-generated-jwt-secret
NEXTAUTH_SECRET=your-generated-nextauth-secret
```

#### All Available Variables

See `.env.example` for the complete list of configurable variables:
- Database configuration (PostgreSQL)
- Ollama/LLM settings
- Redis configuration
- JWT & authentication
- API server settings
- CORS origins
- Vector search parameters
- File upload limits
- Environment flags
- Observability (Sentry, OTEL)

### Environment File Structure

```
.env.example              # Template with all variables (COMMITTED)
.env                      # Your local config (NOT COMMITTED)
apps/api/.env.example     # API variable documentation
apps/web/.env.example     # Web variable documentation
```

**Important:**
- **DO NOT** create separate `.env` files in `apps/api` or `apps/web`
- All configuration comes from the root `.env` file
- This prevents configuration drift between services

## Centralized Database Setup

### Overview

Veriply uses a **centralized PostgreSQL database** on a Linux Ubuntu server shared by all developers and production.

**Architecture:**
```
Ubuntu Server (PostgreSQL)
    ↑
    ├─→ Developer 1 (connects via DB_HOST)
    ├─→ Developer 2 (connects via DB_HOST)
    ├─→ Developer 3 (connects via DB_HOST)
    ├─→ Developer 4 (connects via DB_HOST)
    └─→ Production  (same server, different DB)
```

### For New Developers

#### 1. Request Database Credentials

Contact your team lead to get:
- **DB_HOST:** Ubuntu server IP address (e.g., `192.168.1.100`)
- **DB_USER:** Your database username
- **DB_PASSWORD:** Your database password
- **DB_NAME:** Database name (`veriply_dev` for development)

#### 2. Configure `.env` File

```bash
# Copy example file
cp .env.example .env

# Edit with your credentials
nano .env  # or use your preferred editor
```

Update these variables:
```bash
DB_HOST=192.168.1.100          # Server IP from team lead
DB_USER=your_username          # Your DB username
DB_PASSWORD=your_password      # Your DB password
DB_NAME=veriply_dev
```

#### 3. Generate Authentication Secrets

```bash
# Generate JWT secret
python -c 'import secrets; print(secrets.token_urlsafe(32))'

# Generate NextAuth secret
openssl rand -base64 32
```

Add to `.env`:
```bash
JWT_SECRET=paste_generated_secret_here
NEXTAUTH_SECRET=paste_generated_secret_here
```

#### 4. Test Connection

```bash
# Start Docker Compose
docker-compose up -d

# Check API health
curl http://localhost:8000/healthz

# Expected response:
# {
#   "status": "healthy",
#   "database": {
#     "host": "192.168.1.100",
#     "port": 5432,
#     "name": "veriply_dev"
#   }
# }
```

### For Server Administrators

#### Ubuntu Server Setup

```bash
# Install Docker and Docker Compose
sudo apt update
sudo apt install docker.io docker-compose -y

# Clone repository
git clone https://github.com/DarioDML/Veriply.git
cd Veriply

# Create production .env
cp .env.example .env
nano .env
```

Production `.env` configuration:
```bash
# Use production credentials
DB_HOST=localhost            # Local on production server
DB_NAME=veriply_prod         # Production database
DB_USER=veriply_prod_user
DB_PASSWORD=very_strong_production_password

ENVIRONMENT=production
DEBUG=false
API_RELOAD=false

# Configure CORS for production domain
CORS_ORIGINS=https://veriply.yourdomain.com
```

Start services:
```bash
# Start database
docker-compose up -d db

# Run migrations
docker-compose exec db psql -U veriply_prod_user -d veriply_prod -c "CREATE EXTENSION IF NOT EXISTS vector;"

# Start all services
docker-compose up -d
```

#### Firewall Configuration

```bash
# Allow PostgreSQL from developer IPs
sudo ufw allow from 192.168.1.0/24 to any port 5432

# Or specific IPs
sudo ufw allow from 192.168.1.50 to any port 5432
sudo ufw allow from 192.168.1.51 to any port 5432
```

#### Database Backups

```bash
# Daily backup script
docker-compose exec db pg_dump -U veriply_prod_user veriply_prod > backup_$(date +%Y%m%d).sql

# Set up cron job
crontab -e
# Add: 0 2 * * * /path/to/backup-script.sh
```

### Database Connection Pooling

FastAPI is configured to handle multiple concurrent connections:
- **Pool Size:** 10 base connections
- **Max Overflow:** 20 additional connections under load
- **Total Capacity:** Up to 30 concurrent connections (sufficient for 4 developers)

See `apps/api/app/core/settings.py` for pool configuration.

### Troubleshooting

**Can't connect to database:**
```bash
# Test from developer machine
telnet 192.168.1.100 5432

# Check Docker logs on server
docker-compose logs db

# Verify firewall
sudo ufw status
```

**Connection pool exhausted:**
```bash
# Check active connections on server
docker-compose exec db psql -U veriply_prod_user -d veriply_prod -c "SELECT count(*) FROM pg_stat_activity;"

# Increase pool size in .env if needed
DB_POOL_SIZE=15
DB_MAX_OVERFLOW=25
```

## Development Workflow

### Running Locally

**With Docker (Recommended):**
```bash
docker-compose up -d
```

**Without Docker:**

Frontend:
```bash
cd apps/web
npm install
npm run dev
# Access: http://localhost:3000
```

Backend:
```bash
cd apps/api
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
# Access: http://localhost:8000
```

### Git Workflow

1. Create feature branch from `main`:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make changes and commit:
   ```bash
   git add .
   git commit -m "feat: your feature description"
   ```

3. Push and create Pull Request:
   ```bash
   git push origin feature/your-feature-name
   ```

4. Request review from team members

5. Merge after approval (squash merge recommended)

## Branch Protection Rules

*   **Main Branch (`main`):**
    *   Require pull request reviews before merging (Minimum 1 reviewer).
    *   Require status checks to pass before merging (CI/CD).
    *   Require linear history (Squash merging recommended).
    *   Do not allow bypassing the above settings.

## Additional Documentation

- **Architecture:** See `docs/architecture.md`
- **Tech Spec:** See `docs/tech-spec.md`
- **API Documentation:** http://localhost:8000/docs (when running)
- **Sprint Status:** See `docs/sprint-artifacts/sprint-status.yaml`

## Support

For questions or issues:
1. Check existing documentation in `/docs`
2. Review `.env.example` for configuration help
3. Contact team lead for database credentials
4. Create an issue in GitHub for bugs/features

---

**License:** MIT  
**Team:** Dario, Lucas, Kainy, Soulaymane

