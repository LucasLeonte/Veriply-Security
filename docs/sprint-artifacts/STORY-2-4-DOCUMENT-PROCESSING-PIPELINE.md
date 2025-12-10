<<<<<<< Updated upstream
Go to './epic-2/story-2-4-document-processing-pipeline.md'
=======
# STORY 2-4 — Document Processing Pipeline (Draft Context)

Generated: 2025-12-10

Summary
-------
Process documents uploaded in Story 2-3 into searchable vector chunks and metadata so bots can answer RAG queries.

Background
----------
Story 2-3 implemented document upload, storage, and a DB `Document` row with `status` = `uploaded`. We now need a reliable, scalable processing pipeline that:
- downloads the stored document (MinIO or local fallback)
- converts to plain text (PDF, DOCX, TXT, HTML, etc.)
- splits/normalizes the text into chunks with overlap
- generates embeddings for chunks
- stores chunk vectors in the vector store (pgvector) with metadata linking to `documents` and `bots`
- updates `documents` status transitions and stores processing metadata (error, attempts, chunk count)

Goals
-----
- Build a resilient worker that consumes processing jobs enqueued by the upload flow.
- Support common document formats and fail gracefully for unsupported types.
- Ensure idempotency and safe retries.
- Produce searchable vectors and minimal metadata for citation and debugging.
- Provide observability (metrics/logs) and a small runbook for manual reprocessing.

Scope
-----
Included:
- Worker to handle single-document processing jobs.
- Document-to-text conversion for PDF/DOCX/TXT/HTML and plain text.
- Text chunking strategy and embedding generation.
- Persisting vectors to pgvector-backed table and chunk metadata to DB.
- Document `status` lifecycle: `uploaded` -> `processing` -> `processed` | `failed`.

Out of scope:
- Frontend UI for document processing status (only API-level status updates).
- Large-scale batching/streaming optimizations (this is a single-document worker per job).

Dependencies & Blockers
-----------------------
- Story 2-3 (Document Upload) must be completed and deployed — document rows and storage paths must exist.
- PostgreSQL with `pgvector` extension (used as the vector store). Migration to create `chunks` table + vector column must be added.
- Embedding model or service (external API or local model): env var `EMBEDDING_PROVIDER` / `EMBEDDING_MODEL`.
- Object storage available (MinIO or local FS) and envs: `MINIO_ENDPOINT`, `MINIO_ACCESS_KEY`, `MINIO_SECRET_KEY`, `MINIO_BUCKET`, `MINIO_SECURE`, `MINIO_STRICT`.
- Enqueuer library (e.g., Redis + RQ/Celery, or simple in-process queue for dev). Upload flow should enqueue a job payload (see contract below).

Required versions & packages (suggested)
---------------------------------------
- Python: 3.10+ (project already uses an async stack).
- PostgreSQL: 13+ with `pgvector` extension installed.
- Python packages (examples; pin in `apps/api/requirements.txt`):
  - `sqlalchemy`, `asyncpg`, `alembic`, `pgvector`, `databases`/`sqlalchemy[asyncio]`
  - document parsing: `pdfplumber` or `pdfminer.six`, `python-docx`, `mammoth` (optional)
  - embeddings: `openai` (if using OpenAI) or client SDK for local providers (e.g., `ollama` CLI integration)
  - storage: `minio`
  - testing: `pytest`, `pytest-asyncio`, `httpx`

Local dev options
-----------------
- For quick local development you can use a Postgres docker image and a local MinIO container (or rely on the filesystem fallback already implemented in Story 2-3).
- Example docker-compose (dev):
  - `postgres:15` with a mounted init SQL to `CREATE EXTENSION IF NOT EXISTS vector;`
  - `minio/minio` for object storage.

Notes on secrets and envs
------------------------
- `JWT_SECRET` must be set for auth flows (>=32 characters recommended).
- `DATABASE_URL` should point to the dev database.
- `EMBEDDING_PROVIDER` / `EMBEDDING_MODEL` should be set for embedding generation; a local provider may be used in dev to avoid API costs.


Job / API Contract
------------------
The upload endpoint enqueues a job with this shape (JSON):

{
  "document_id": "<uuid>",
  "tenant_id": "<uuid>",
  "bot_id": "<uuid|null>",
  "storage_path": "s3://bucket/tenant/<tenant>/bot/<bot>/.../file.ext" | "file://...",
  "filename": "original-filename.ext",
  "content_type": "mime/type",
  "uploaded_by": "<user_id|null>",
  "attempt": 0
}

Worker behavior (high level)
---------------------------
1. Claim job (enqueuer semantics). Mark `documents.status` = `processing` and increment `processing_attempts` (DB column — migration required) inside a transaction to avoid double processing.
2. Download object from storage. If download fails and `attempt` < MAX_RETRIES, re-enqueue (or raise to let enqueuer retry). If `MINIO_STRICT` is set, treat storage failures as hard errors.
3. Convert to plain text using best-effort toolchain:
   - PDF: use `pdfminer` or `pdfplumber` (dev) or `pdftotext` if available
   - DOCX: `python-docx` or `mammoth`
   - HTML: strip tags and normalize
   - TXT: decode using UTF-8 with fallback encodings
   - For other/unsupported types, mark as `failed` and store error message.
4. Normalize and clean text: remove excessive whitespace, normalize newlines, remove null bytes.
5. Chunking algorithm:
   - Target chunk size: 500 tokens (approx 3000 characters) with 20% overlap (configurable).
   - Preserve document order; attach `chunk_index` and `char_range` metadata.
6. For each chunk:
   - Generate embedding vector via configured provider.
   - Insert into `chunks` table with columns: id (uuid), document_id, bot_id, tenant_id, chunk_index, text, vector (pgvector), metadata (json: filename, source_page if available), created_at.
   - Consider upsert semantics to make worker idempotent (use deterministic chunk id: e.g., hash(document_id + chunk_index)).
7. Update `documents` row: `status` = `processed`, `chunk_count` = N, `processed_at` timestamp, optionally `metadata` JSON with stats.
8. Emit observability events/metrics (processing_time, chunk_count, failed_chunks).

Database: required migrations
----------------------------
- Create `chunks` table (alembic migration):
  - id UUID primary key
  - document_id UUID FK -> documents(id) (indexed)
  - tenant_id UUID indexed
  - bot_id UUID indexed (nullable)
  - chunk_index integer
  - text text
  - vector vector (pgvector) -- ensure `pgvector` extension exists
  - metadata jsonb (nullable)
  - created_at timestamptz default now()
  - UNIQUE(document_id, chunk_index) (for idempotency)

- Add optional columns to `documents` (if not present): `processing_attempts` integer default 0, `chunk_count` integer default 0, `processed_at` timestamptz nullable, `error` text nullable.

Idempotency & retry behavior
----------------------------
- The worker should treat a job as idempotent: if `chunks` rows already exist for `document_id` with expected `chunk_count`, skip embedding generation.
- Use `attempt` counting in the job payload and a DB `processing_attempts` column to avoid infinite retries.
- On fatal errors (unsupported format, persistent storage errors), set `documents.status` = `failed` and attach `error` message.

Observability & metrics
-----------------------
- Logs: include document_id, tenant_id, bot_id, attempt, processing time, chunk_count, error traces.
- Metrics (Prometheus-friendly): `document_processing_jobs_total{status=processed|failed}`, `document_processing_duration_seconds`, `document_chunks_generated_total`.

Acceptance Criteria
-------------------
1. Uploading a supported document (via Story 2-3 endpoint) enqueues a processing job and the upload response includes `queued: true`.
2. Worker processes the job and `documents.status` transitions from `uploaded` -> `processing` -> `processed`.
3. The `chunks` table contains N rows for the document (N > 0) with populated `vector` and `text`.
4. Embeddings are persisted in pgvector column and are retrievable with a simple similarity query.
5. Failures produce `documents.status` = `failed` and `error` text for debugging; recoverable errors are retried up to `MAX_RETRIES`.
6. Tests exist to cover: a) successful processing of a small TXT/PDF, b) idempotent reprocessing, c) retry behavior for simulated transient storage failures.

Tests & QA
----------
- Unit tests for chunker (given text produce expected chunks and overlap).
- Integration test for worker:
  - Create a test `Document` row pointing to a small `file://` test file
  - Run worker synchronously and assert: status=processed, chunk_count matches, and `chunks` rows exist with non-null vectors.
- Simulated failure test: mock storage client to fail first download, ensure worker retries and eventually marks as failed if max retries exceeded.

Smoke / Manual runbook
----------------------
Smoke / Manual runbook
----------------------
1. Ensure `DATABASE_URL` points to a dev DB with `pgvector` extension and migrations applied.
2. Ensure `JWT_SECRET` is set and (optionally) `MINIO_*` envs are set or local storage is available.
3. Start dev server (API) that includes the enqueuer integration or exposes an endpoint to push a job to the local worker.
4. Run the smoke upload script: `python apps/api/scripts/smoke_story_2_3.py` → confirm upload returns `queued: true`.
5. Start the worker in the foreground (dev mode) — implementation detail depends on chosen enqueuer. For a simple dev worker, run `python -m apps.api.worker.process document_worker` or similar.
6. Confirm `documents.status` becomes `processed` and `chunks` table is populated.

Quick PowerShell commands (run from project root)
-------------------------------------------------
1) Activate virtualenv (if using the repository venv):

```powershell
& ".\.venv\Scripts\Activate.ps1"
```

2) Install dependencies (from `apps/api`):

```powershell
Set-Location -Path .\apps\api
pip install -r requirements.txt
```

3) Apply migrations (example using alembic inside `apps/api`):

```powershell
Set-Location -Path .\apps\api
alembic upgrade head
```

4) Start the API dev server (example with Uvicorn):

```powershell
Set-Location -Path .\apps\api
$env:DATABASE_URL = 'postgresql+asyncpg://user:pass@localhost:5432/veriply_dev'
$env:JWT_SECRET = 'replace-this-with-32+chars'
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

5) Run the smoke upload script (from `apps/api`):

```powershell
Set-Location -Path .\apps\api
python scripts\smoke_story_2_3.py
```

6) Start a dev worker (example patterns):

```powershell
# If using an RQ worker
Set-Location -Path .\apps\api
rq worker default

# Or run a local ad-hoc worker entrypoint (if implemented)
python -m apps.api.workers.document_processor --run-once --document-id <document_id>
```

7) Inspect DB to confirm processed document and chunks (psql or any DB client):

```powershell
psql "${env:DATABASE_URL}" -c "SELECT id, status, chunk_count, processed_at FROM documents WHERE id='your-document-id';"
psql "${env:DATABASE_URL}" -c "SELECT count(*) FROM chunks WHERE document_id='your-document-id';"
```

Notes
-----
- Paths and module names above are examples — if your project exposes a different module path for the FastAPI app or a worker entrypoint, adapt the commands accordingly.
- For CI, run tests from `apps/api` so `pytest.ini` is applied: `Set-Location -Path .\apps\api; pytest`.


Environment variables (dev)
-------------------------
- `DATABASE_URL` — Postgres with `pgvector` installed
- `JWT_SECRET` — JWT secret for tests/dev
- `MINIO_ENDPOINT`, `MINIO_ACCESS_KEY`, `MINIO_SECRET_KEY`, `MINIO_BUCKET`, `MINIO_SECURE`, `MINIO_STRICT` — or fallback to local storage
- `EMBEDDING_PROVIDER`/`EMBEDDING_MODEL` — embedding service settings
- `MAX_PROCESSING_RETRIES` — integer (default 3)

Implementation tasks (developer checklist)
----------------------------------------
1. Add alembic migration to create `chunks` table and optional `documents` columns.
2. Implement worker: `apps/api/app/workers/document_processor.py`.
3. Implement embedding adapter with pluggable providers: `apps/api/app/lib/embeddings.py`.
4. Hook worker to enqueuer used by upload flow (support sync/async enqueue semantics already implemented in Story 2-3).
5. Add unit tests and integration tests under `apps/api/tests` and CI job referencing `apps/api/pytest.ini`.
6. Add lightweight metrics and structured logs.

Open questions / decisions
------------------------
- Which enqueuer should be the long-term standard? (Redis+RQ, Celery, or a lightweight in-process queue for early sprints). Recommend Redis+RQ for simplicity and dev ergonomics.
- Which embedding provider do we standardize on for production vs dev (OpenAI vs local Ollama)? Provide adapter abstraction.
- Chunk size/token target: 500 tokens default — confirm.

Done / Next
-----------
This draft should be reviewed by the team (backend + ML) to confirm embedding provider, enqueuer choice, and chunk sizing. After approval, convert the checklist into issues or story tasks and assign to backend engineers.
>>>>>>> Stashed changes
