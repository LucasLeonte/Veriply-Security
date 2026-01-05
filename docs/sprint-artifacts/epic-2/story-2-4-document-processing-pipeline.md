# Story 2.4: Document Processing Pipeline

**Epic:** 2. Bot & Knowledge Management  
**Status:** done  
**Assigned to:** null  
**Blocked by:** 2-3-document-upload-api

## Story

As a System,  
I want to extract, chunk, and embed uploaded documents,  
so that content is searchable via semantic search.

## Acceptance Criteria

### Document Processing Trigger

- [ ] When document upload completes (status = "Processing")
- [ ] Background worker picks up document from processing queue
- [ ] Worker polls queue every 5 seconds for new documents
- [ ] Multiple workers can process documents in parallel (up to 3 concurrent)
- [ ] Processing jobs retry up to 3 times on failure with exponential backoff

### Text Extraction

- [ ] System extracts raw text from PDF files:
  - Multi-page PDFs supported
  - Multi-column layouts handled correctly
  - Images ignored (OCR out of scope for MVP)
  - Tables extracted as structured text
  - Preserves paragraph boundaries
- [ ] System extracts text from DOCX files:
  - Paragraphs and headings preserved
  - Lists and tables extracted
  - Heading levels stored as metadata
  - Comments and track changes ignored
- [ ] System extracts text from TXT and MD files:
  - UTF-8 encoding assumed
  - Line breaks preserved
  - Markdown syntax retained for context
- [ ] System extracts text from CSV files:
  - First row treated as column headers
  - Each row becomes a separate chunk
  - Column headers included in each chunk for context
  - Handles quoted fields with commas

### Text Chunking

- [ ] Extracted text is split into semantic chunks:
  - Target chunk size: 512 tokens
  - Overlap between chunks: 50 tokens (10%)
  - Preserves sentence boundaries (doesn't break mid-sentence)
  - Preserves paragraph boundaries when possible
- [ ] Each chunk record stores:
  - chunk_id (UUID primary key)
  - document_id (UUID foreign key)
  - bot_id (UUID foreign key for scoping)
  - tenant_id (UUID for RLS)
  - chunk_index (integer, 0-based sequential)
  - content (TEXT, the actual chunk text)
  - token_count (integer)
  - metadata (JSONB: page_number, heading, section, etc.)
  - created_at (timestamp)
- [ ] Metadata captured per chunk:
  - For PDF: page_number, position_in_page
  - For DOCX: heading_level, heading_text, section
  - For CSV: row_number, column_headers
  - For all: document_filename, file_type

### Embedding Generation

- [ ] System generates embeddings for each chunk:
  - Model: bge-m3 (1024 dimensions)
  - Hosted: Ollama local instance
  - Batch size: 10 chunks per API call for efficiency
  - Timeout: 30 seconds per batch
- [ ] Embeddings are stored in pgvector:
  - embedding (vector(1024))
  - Indexed with HNSW for fast similarity search
  - Index parameters: m=16, ef_construction=64
- [ ] Embedding records linked to chunks:
  - One embedding per chunk
  - Foreign key: chunk_id
  - Include tenant_id and bot_id for RLS and scoping

### Processing Completion

- [ ] On successful processing:
  - Document status changes from "Processing" to "Ready"
  - processing_completed_at timestamp set
  - chunk_count and embedding_count fields updated
  - Success event logged
- [ ] On processing failure:
  - Document status changes to "Failed"
  - error_message field populated with specific error
  - processing_completed_at timestamp set
  - Failure event logged with stack trace
  - User can retry processing via UI (Story 2.7)

### Progress Tracking

- [ ] Processing progress is tracked and exposed via API:
  - GET `/api/v1/bots/{bot_id}/documents/{document_id}/status`
  - Returns: status, progress_percent, current_step, estimated_time_remaining
  - Steps: extracting (25%), chunking (50%), embedding (75%), indexing (100%)
- [ ] Frontend can poll status endpoint to show real-time progress
- [ ] Estimated time based on document size:
  - Small (<1MB): ~10 seconds
  - Medium (1-10MB): ~30-60 seconds
  - Large (10-25MB): ~2-5 minutes

### Error Handling

- [ ] Corrupted file error: "File is corrupted and cannot be processed"
- [ ] Unsupported format error: "File format not supported for text extraction"
- [ ] Empty document error: "Document contains no extractable text"
- [ ] Ollama API timeout: "Embedding generation timed out. Retrying..."
- [ ] Database error: "Failed to store chunks. Retrying..."
- [ ] Vector index error: "Failed to index embeddings. Retrying..."
- [ ] Generic error: "Processing failed: [specific error]. Contact support if issue persists."

### Performance Requirements

- [ ] Text extraction: < 5 seconds for typical PDF (10 pages)
- [ ] Chunking: < 2 seconds for 10,000 tokens
- [ ] Embedding generation: < 3 seconds per 10 chunks (batch of 10)
- [ ] Total processing time: < 60 seconds for 5MB PDF (target)
- [ ] System can process 3 documents simultaneously without degradation
- [ ] Queue backlog does not exceed 100 pending documents

## Tasks / Subtasks

### 1) Backend - Document Processing Worker

- [ ] Create background worker service (separate process):
  - Uses Redis Queue (RQ), Celery, or similar task queue
  - Polls for documents with status "Processing"
  - Processes one document at a time per worker instance
  - Supports multiple worker instances for parallelism
- [ ] Implement main processing pipeline function:
  - `process_document(document_id)`
  - Fetch document record and file from S3
  - Extract text → chunk → embed → store
  - Update document status throughout
  - Handle errors and retries gracefully
- [ ] Add worker management commands:
  - `python manage.py start_worker` (starts single worker)
  - `python manage.py stop_worker` (graceful shutdown)
  - Worker registers with Redis on start, deregisters on stop
- [ ] Configure worker environment:
  - Environment vars: OLLAMA_HOST, REDIS_URL, S3_CONFIG
  - Worker logs to stdout/file with structured logging
  - Health check endpoint for monitoring

### 2) Backend - Text Extraction Service

- [ ] Create `TextExtractorService` class:
  - `extract_from_pdf(file_path) -> str`
  - `extract_from_docx(file_path) -> str`
  - `extract_from_text(file_path) -> str`
  - `extract_from_csv(file_path) -> List[str]`
- [ ] Install and configure dependencies:
  - pypdf or PyPDF2 for PDF extraction
  - python-docx for DOCX extraction
  - Standard library for TXT/MD
  - csv module for CSV files
- [ ] Implement extraction logic:
  - PDF: iterate pages, extract text, handle multi-column
  - DOCX: iterate paragraphs, preserve headings and structure
  - TXT/MD: read as UTF-8, handle encoding errors gracefully
  - CSV: pandas.read_csv(), convert rows to text chunks
- [ ] Extract metadata during extraction:
  - PDF: page numbers, text positions
  - DOCX: heading levels, section titles
  - CSV: row numbers, column names
- [ ] Handle extraction errors:
  - Corrupted files → log error, set document status to "Failed"
  - Empty content → log warning, set status to "Failed" with message
  - Unsupported features (e.g., encrypted PDFs) → fail gracefully

### 3) Backend - Text Chunking Service

- [ ] Create `ChunkingService` class:
  - `chunk_text(text: str, metadata: dict) -> List[Chunk]`
  - Uses LangChain's RecursiveCharacterTextSplitter or similar
  - Configuration: chunk_size=512 tokens, chunk_overlap=50 tokens
- [ ] Implement semantic chunking:
  - Split on sentence boundaries (periods, question marks, exclamation marks)
  - Split on paragraph boundaries (\n\n) when possible
  - Never split mid-word or mid-sentence
  - Preserve context with overlap (last 50 tokens of chunk N = first 50 tokens of chunk N+1)
- [ ] Calculate token count per chunk:
  - Use tiktoken library with cl100k_base encoding (GPT-4 tokenizer)
  - Store token_count in chunk record
- [ ] Create chunk records in database:
  - Batch insert for efficiency (50 chunks per INSERT)
  - Include document_id, bot_id, tenant_id, chunk_index, content, metadata
  - Foreign key constraints ensure referential integrity

### 4) Backend - Embedding Generation Service

- [ ] Create `EmbeddingService` class:
  - `generate_embeddings(chunks: List[Chunk]) -> List[np.ndarray]`
  - Integrates with Ollama API (bge-m3 model)
  - Batch processing: 10 chunks per API call
- [ ] Configure Ollama client:
  - Endpoint: http://ollama:11434 (or configured OLLAMA_HOST)
  - Model: bge-m3 (1024-dimensional embeddings)
  - Timeout: 30 seconds per request
  - Retry logic: 3 attempts with exponential backoff
- [ ] Implement batched embedding generation:
  - Collect chunks into batches of 10
  - Call Ollama API: POST /api/embed with model and prompts
  - Parse response: extract embeddings array
  - Convert to numpy arrays for storage
- [ ] Store embeddings in database:
  - Insert into embeddings table (chunk_id, embedding vector)
  - Batch insert: 50 embeddings per query
  - Create HNSW index on embedding column after bulk insert
- [ ] Handle embedding errors:
  - API timeout → retry with backoff
  - Invalid response → log error, retry
  - Model not found → fail with clear error message

### 5) Backend - Vector Storage Setup

- [ ] Create `chunks` table schema:
  - chunk_id (UUID primary key)
  - document_id (UUID, foreign key to documents)
  - bot_id (UUID, foreign key to bots)
  - tenant_id (UUID, foreign key to tenants)
  - chunk_index (INTEGER)
  - content (TEXT)
  - token_count (INTEGER)
  - metadata (JSONB)
  - created_at (TIMESTAMP)
- [ ] Create `embeddings` table schema:
  - embedding_id (UUID primary key)
  - chunk_id (UUID, foreign key to chunks, unique)
  - bot_id (UUID for scoping)
  - tenant_id (UUID for RLS)
  - embedding (vector(1024) from pgvector)
  - created_at (TIMESTAMP)
- [ ] Add indexes for performance:
  - chunks: (document_id), (bot_id), (tenant_id, bot_id)
  - embeddings: (chunk_id), (bot_id)
  - HNSW index on embeddings.embedding: CREATE INDEX ON embeddings USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64)
- [ ] Add RLS policies:
  - chunks: tenant_id = current_setting('app.current_tenant_id')::uuid
  - embeddings: tenant_id = current_setting('app.current_tenant_id')::uuid
- [ ] Add CASCADE delete:
  - When document deleted → delete all chunks
  - When chunk deleted → delete corresponding embedding

### 6) Backend - Processing Status API

- [ ] Create GET `/api/v1/bots/{bot_id}/documents/{document_id}/status` endpoint:
  - Return: status, progress_percent, current_step, chunks_created, embeddings_created
  - Calculate progress:
    - Extracting: 0-25%
    - Chunking: 25-50%
    - Embedding: 50-99%
    - Indexing: 99-100%
  - Expose estimated_time_remaining based on document size
- [ ] Update document record throughout processing:
  - Set processing_started_at when worker starts
  - Update status: processing → ready/failed
  - Update processing_completed_at when done
  - Update chunk_count and embedding_count
- [ ] Add processing logs table (optional):
  - Log each step: extraction started, chunks created (count), embeddings started, etc.
  - Useful for debugging and monitoring

### 7) Backend - Task Queue Setup

- [ ] Configure Redis for task queue:
  - Install Redis server (Docker container)
  - Connection: redis://redis:6379/0
  - Configure RQ (Redis Queue) or Celery
- [ ] Define processing task:
  - @task decorator for async execution
  - task_id generated and returned to client
  - Task result stored in Redis (TTL: 24 hours)
- [ ] Implement task enqueue from upload endpoint:
  - After document uploaded to S3
  - Enqueue: `process_document.delay(document_id)`
  - Return task_id to client for status polling
- [ ] Worker monitoring:
  - Track active workers in Redis
  - Dashboard endpoint: GET `/api/v1/admin/workers` (admin only)
  - Shows: worker_id, status, current_task, uptime

### 8) Frontend - Processing Status Display

- [ ] Update Knowledge Base page to show processing status:
  - Documents with status "Processing" show spinner
  - Progress bar (0-100%) if available from API
  - Current step text: "Extracting text...", "Creating chunks...", "Generating embeddings..."
  - Estimated time remaining
- [ ] Implement status polling:
  - Poll `/api/v1/documents/{doc_id}/status` every 2 seconds
  - Only poll for documents with status "Processing"
  - Stop polling when status changes to "Ready" or "Failed"
  - Show success toast when processing completes
- [ ] Display processing metrics:
  - Chunk count badge on document card
  - Embedding count (should equal chunk count)
  - Processing duration (e.g., "Processed in 42 seconds")
- [ ] Handle failed processing:
  - Red error badge on document
  - Tooltip shows error message
  - "Retry" button to re-trigger processing

### 9) Testing

#### Backend Tests (Pytest)

- [ ] Test TextExtractorService:
  - Extract from valid PDF → returns text
  - Extract from valid DOCX → returns text with headings
  - Extract from TXT/MD → returns raw text
  - Extract from CSV → returns list of row chunks
  - Corrupted file → raises exception
  - Empty file → raises exception
- [ ] Test ChunkingService:
  - Chunk text with correct size and overlap
  - Chunks don't break mid-sentence
  - Metadata preserved in chunks
  - Token count calculated correctly
- [ ] Test EmbeddingService (mocked Ollama):
  - Generate embeddings for batch of chunks
  - Returns correct dimension (1024)
  - Handles API timeout gracefully
  - Retries on failure
- [ ] Test document processing pipeline (integration):
  - Upload document → status "Processing"
  - Worker processes document → status "Ready"
  - Chunks created in database
  - Embeddings created and indexed
  - Document metadata updated (chunk_count, etc.)
- [ ] Test processing failures:
  - Corrupted PDF → status "Failed", error message set
  - Ollama API down → retries 3 times, then fails
  - Database error → retries, then fails
- [ ] Test status endpoint:
  - Returns correct progress during processing
  - Returns "Ready" when complete
  - Returns "Failed" with error message

#### Performance Tests

- [ ] Benchmark text extraction:
  - 10-page PDF: < 5 seconds
  - 100-page PDF: < 30 seconds
- [ ] Benchmark chunking:
  - 10,000 tokens: < 2 seconds
  - 100,000 tokens: < 10 seconds
- [ ] Benchmark embedding generation:
  - 100 chunks: < 30 seconds (batches of 10)
  - 1000 chunks: < 5 minutes
- [ ] End-to-end processing time:
  - 1MB PDF (~10 pages): < 30 seconds
  - 5MB PDF (~50 pages): < 60 seconds
  - 10MB PDF (~100 pages): < 2 minutes

#### Frontend Tests

- [ ] Test processing status display:
  - Document shows "Processing" spinner
  - Progress bar updates as status changes
  - Success toast appears when complete
  - Error message displayed on failure
- [ ] Test status polling:
  - Starts polling on page load for "Processing" docs
  - Stops polling when status changes
  - Handles API errors gracefully

### 10) Database Migrations

- [ ] Alembic migration: create `chunks` table
- [ ] Alembic migration: create `embeddings` table with pgvector column
- [ ] Alembic migration: enable pgvector extension (CREATE EXTENSION IF NOT EXISTS vector)
- [ ] Alembic migration: create HNSW index on embeddings
- [ ] Alembic migration: add RLS policies to chunks and embeddings
- [ ] Alembic migration: add processing fields to documents table:
  - processing_started_at (TIMESTAMP nullable)
  - processing_completed_at (TIMESTAMP nullable)
  - chunk_count (INTEGER default 0)
  - embedding_count (INTEGER default 0)
- [ ] Ensure migrations are reversible

### 11) Infrastructure & DevOps

- [ ] Deploy Ollama container:
  - Docker image: ollama/ollama
  - Expose port 11434
  - Pre-load bge-m3 model: `ollama pull bge-m3`
  - Resource limits: 4GB RAM, 2 CPU cores
- [ ] Deploy Redis container:
  - Docker image: redis:7-alpine
  - Expose port 6379
  - Persistence enabled (AOF or RDB)
- [ ] Deploy worker container(s):
  - Use same API image with different command
  - Command: `python manage.py start_worker`
  - Scale horizontally: 3 worker instances
  - Health check: worker heartbeat in Redis
- [ ] Configure monitoring:
  - Prometheus metrics: documents_processed_total, processing_duration_seconds
  - Alerts: processing_failures_total, queue_depth_high
- [ ] Add logging:
  - Structured logs (JSON format)
  - Log levels: INFO for normal processing, ERROR for failures
  - Include document_id, bot_id, tenant_id in all logs

### 12) Documentation

- [ ] Update README.md:
  - Document processing architecture (extraction → chunking → embedding)
  - Worker deployment instructions
  - Ollama setup guide
- [ ] API documentation:
  - Document status endpoint with examples
  - Processing flow diagram
- [ ] Troubleshooting guide:
  - Common processing errors and solutions
  - How to check worker health
  - How to manually retry failed documents
- [ ] Performance tuning guide:
  - Chunking parameter recommendations
  - Ollama resource requirements
  - Worker scaling guidelines

## Dev Notes

### Processing Architecture

**Pipeline Flow:**
1. Document uploaded → status = "Processing", job enqueued
2. Worker picks up job from Redis queue
3. Extract text from file (PDF/DOCX/TXT/CSV)
4. Split text into semantic chunks (512 tokens, 50 token overlap)
5. Generate embeddings for chunks using Ollama (bge-m3)
6. Store chunks and embeddings in PostgreSQL + pgvector
7. Create HNSW index for fast similarity search
8. Update document status to "Ready" or "Failed"

**Technology Stack:**
- **Text Extraction**: pypdf (PDF), python-docx (DOCX), csv module (CSV)
- **Chunking**: LangChain RecursiveCharacterTextSplitter or custom splitter
- **Embeddings**: Ollama with bge-m3 model (1024 dimensions)
- **Vector Storage**: PostgreSQL + pgvector extension with HNSW index
- **Task Queue**: Redis Queue (RQ) or Celery for background jobs
- **Worker**: Separate Python process, horizontally scalable

### Chunking Strategy

- **Target size**: 512 tokens (~2000 characters)
- **Overlap**: 50 tokens (10% of chunk size)
- **Rationale**: 512 tokens provides enough context for semantic meaning while fitting within most LLM context windows efficiently
- **Overlap rationale**: Ensures continuity across chunks, prevents information loss at boundaries

### Embedding Model

- **Model**: bge-m3 (BAAI general embedding)
- **Dimensions**: 1024
- **Hosting**: Ollama (self-hosted, GDPR-compliant)
- **Performance**: ~100 chunks/second with batching
- **Cost**: Free (self-hosted)

### Vector Index

- **Algorithm**: HNSW (Hierarchical Navigable Small Worlds)
- **Parameters**: m=16 (connections per node), ef_construction=64 (construction quality)
- **Distance metric**: Cosine similarity
- **Query performance**: O(log n) approximate nearest neighbor
- **Rationale**: HNSW provides best balance of speed and accuracy for semantic search

### Scalability Considerations

- **Horizontal scaling**: Run multiple worker instances
- **Queue depth**: Monitor backlog, scale workers up if >50 pending
- **Ollama scaling**: Use GPU if available (10x speedup), otherwise CPU sufficient for MVP
- **Database scaling**: Partition chunks/embeddings by tenant_id if >10M rows

### Future Enhancements (Out of Scope)

- OCR support for scanned PDFs (Tesseract integration)
- Advanced PDF parsing (tables, images, footnotes)
- Multi-language support (language detection, language-specific chunking)
- Semantic chunking (use LLM to determine natural boundaries)
- Incremental updates (re-chunk only modified sections)
- Custom chunking strategies per bot (adjustable chunk size)

### Project Structure Notes

**Backend:**
- Workers: `apps/api/app/workers/document_processor.py` (main worker)
- Services: 
  - `apps/api/app/services/text_extractor.py` (extraction)
  - `apps/api/app/services/chunking_service.py` (chunking)
  - `apps/api/app/services/embedding_service.py` (Ollama integration)
- Models: 
  - `apps/api/app/models/chunk.py` (Chunk model)
  - `apps/api/app/models/embedding.py` (Embedding model with vector column)
- Routes: `apps/api/app/api/routes/documents.py` (add status endpoint)
- Database: `apps/api/alembic/versions/` (migrations for chunks, embeddings)

**Infrastructure:**
- Docker Compose: add Ollama and Redis services
- Worker Dockerfile: separate service definition
- Environment: OLLAMA_HOST, REDIS_URL

### References

- [Source: docs/epics.md#Story-2.4-Document-Processing-Pipeline]
- [Source: docs/architecture.md#Model-hosting-embeddings] - Ollama with bge-m3
- [Source: docs/architecture.md#Data-storage-vector-strategy] - PostgreSQL + pgvector with HNSW
- [Source: docs/prd.md#FR14] - System automatically chunks documents into semantic segments
- [Source: docs/prd.md#FR15] - System generates embeddings using bge-m3 model
- [Source: docs/prd.md#FR16] - System stores embeddings in PostgreSQL + pgvector with scoping
- Functional Requirements: FR14 (chunking), FR15 (embeddings), FR16 (vector storage)

## Dev Agent Record

### Context Reference

- Will be generated as: docs/sprint-artifacts/story-2-4-document-processing-pipeline.context.xml

### Agent Model Used

Claude Sonnet 4.5

### Completion Notes

- Drafted comprehensive Story 2.4 with complete processing pipeline
- Covers text extraction, semantic chunking, embedding generation, vector storage
- Background worker architecture with Redis queue
- Ollama integration for embeddings (bge-m3, 1024 dimensions)
- PostgreSQL + pgvector with HNSW index for fast retrieval
- Full test coverage including performance benchmarks
- Database migrations for chunks and embeddings tables
- Infrastructure setup: Ollama, Redis, worker deployment

### Learnings from Previous Stories

**From Story 2-1-bot-creation-configuration (Status: done)**
- **Bot Service**: `bot_service.get_bot_by_id()` available - use to validate bot exists before processing
- **RLS Pattern**: `current_setting('app.current_tenant_id')::uuid` - apply to chunks and embeddings tables
- **Foreign Keys**: Use CASCADE delete - chunks should cascade when document deleted
- **Subscription Tier**: Tenant has subscription_tier - could add processing limits per tier in future

**From Story 2-3-document-upload-api (Status: assigned to Soulaymane)**
- **Document Model**: Document table structure defined with status enum (uploading, processing, ready, failed)
- **S3 Integration**: Files stored in S3 with path format `{tenant_id}/{bot_id}/documents/{document_id}/{filename}`
- **Status Flow**: Upload sets status to "Processing" - this story changes it to "Ready" or "Failed"
- **File Types**: Support PDF, DOCX, TXT, MD, CSV - extraction service must handle all
- **Storage Path**: Use document.storage_path to retrieve file from S3 for processing

**Key Integration Points:**
- Worker monitors documents table for status = "Processing"
- Fetch document file from S3 using storage_path
- Update document status throughout pipeline
- Create chunks and embeddings linked to document_id and bot_id
- Frontend polls status endpoint added in Story 2.3

**Technical Debt to Address:**
- Alembic migrations for documents table (from 2-3) must be complete before this story
- Ollama must be deployed and accessible
- Redis must be configured for task queue

### Debug Log References

None yet (story in draft status)

### File List

<!-- Will be updated by dev agent during implementation -->

**TO BE CREATED:**

Backend:
- `apps/api/app/workers/document_processor.py` - Main worker process
- `apps/api/app/services/text_extractor.py` - Text extraction from PDFs, DOCX, CSV
- `apps/api/app/services/chunking_service.py` - Semantic text chunking
- `apps/api/app/services/embedding_service.py` - Ollama API integration for embeddings
- `apps/api/app/models/chunk.py` - Chunk SQLAlchemy model
- `apps/api/app/models/embedding.py` - Embedding model with vector column
- `apps/api/app/schemas/chunk.py` - Pydantic schemas
- `apps/api/tests/test_text_extractor.py` - Extraction tests
- `apps/api/tests/test_chunking.py` - Chunking tests
- `apps/api/tests/test_embeddings.py` - Embedding generation tests
- `apps/api/tests/test_document_processor.py` - End-to-end pipeline tests
- `apps/api/alembic/versions/XXX_create_chunks_table.py` - Chunks table migration
- `apps/api/alembic/versions/XXX_create_embeddings_table.py` - Embeddings table migration
- `apps/api/alembic/versions/XXX_enable_pgvector.py` - Enable vector extension
- `apps/api/alembic/versions/XXX_create_hnsw_index.py` - Create vector index

**TO BE MODIFIED:**
- `apps/api/app/api/routes/documents.py` - Add GET /documents/{id}/status endpoint
- `apps/api/app/models/document.py` - Add processing timestamp and count fields
- `apps/api/app/main.py` - May need worker startup integration
- `docker-compose.yml` - Add Ollama, Redis, worker services
- `requirements.txt` - Add pypdf, python-docx, tiktoken, numpy, redis, rq/celery

**INFRASTRUCTURE:**
- Ollama container with bge-m3 model pre-loaded
- Redis container for task queue
- Worker container(s) running document_processor

## Change Log

- 2025-12-04: Initial draft created by AI (SM workflow)
  - Comprehensive pipeline design: extraction → chunking → embedding → storage
  - Background worker architecture with Redis queue
  - Ollama integration for self-hosted embeddings (GDPR-compliant)
  - PostgreSQL + pgvector with HNSW index
  - Performance requirements and benchmarks
  - Full test coverage including integration and performance tests
  - Learnings from Stories 2-1 and 2-3 incorporated
