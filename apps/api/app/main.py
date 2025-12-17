from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.core.database import init_db
from app.core.migrations import enable_pgvector, enable_rls
from app.core.settings import settings
from app.api.v1 import auth
from app.api.v1 import profile
from app.api.v1 import groups
from app.api.v1 import bots as bots_v1
from app.api.v1 import documents as documents_v1
from app.api.v1 import folders
from app.api.v1 import bot_access
from app.api.routes import query
from app.api.routes import chat
from app.api.routes.documents import documents_router as document_detail_router  # Legacy document operations

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()
    await enable_pgvector()
    await enable_rls()
    yield
    # Shutdown (optional)

app = FastAPI(
    title="Veriply API",
    lifespan=lifespan,
    debug=settings.DEBUG,
)

# Serve avatars from local storage for development/local use
avatars_dir = Path(__file__).resolve().parents[3] / "storage" / "avatars"
avatars_dir.mkdir(parents=True, exist_ok=True)
app.mount("/avatars", StaticFiles(directory=str(avatars_dir)), name="avatars")

# Configure CORS from settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS_LIST,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(profile.router)
app.include_router(groups.router)
app.include_router(bots_v1.router)  # Group-scoped: /api/v1/groups/{group_id}/bots
app.include_router(documents_v1.router)  # Group-scoped: /api/v1/groups/{group_id}/documents
app.include_router(folders.router)  # Group-scoped: /api/v1/groups/{group_id}/folders
app.include_router(bot_access.router)  # Bot access: /api/v1/bots/{bot_id}/access
app.include_router(query.router, prefix="/api/v1")  # Legacy: /api/v1/query
app.include_router(chat.router, prefix="/api/v1")  # Public chat: /api/v1/bots/{bot_id}/public, /api/v1/bots/{bot_id}/chat/query
app.include_router(document_detail_router, prefix="/api/v1")  # Legacy: /api/v1/documents/{id} operations

@app.get("/")
async def root():
    return {"message": "Hello from Veriply API"}

@app.get("/healthz")
async def health_check():
    """
    Health check endpoint.
    
    Returns basic health status and configuration info (non-sensitive).
    Used for monitoring and deployment verification.
    """
    return {
        "status": "healthy",
        "environment": settings.ENVIRONMENT,
        "database": {
            "host": settings.DB_HOST,
            "port": settings.DB_PORT,
            "name": settings.DB_NAME,
        },
        "ollama": {
            "host": settings.OLLAMA_HOST,
            "model": settings.OLLAMA_MODEL,
        },
    }
