from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.core.database import init_db
from app.core.migrations import enable_pgvector, enable_rls
from app.core.settings import settings
from app.api.v1 import auth
from app.api.v1 import profile
from app.api.routes import bots

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
app.include_router(bots.router, prefix="/api/v1")

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
