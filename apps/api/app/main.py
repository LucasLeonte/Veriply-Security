from fastapi import FastAPI, Depends
from contextlib import asynccontextmanager
from app.core.database import get_db, init_db
from app.core.migrations import enable_pgvector, enable_rls
from app.api.v1 import auth, profile

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()
    await enable_pgvector()
    await enable_rls()
    yield
    # Shutdown (optional)

app = FastAPI(title="Veriply API", lifespan=lifespan)

# Include routers
app.include_router(auth.router)
app.include_router(profile.router)

@app.get("/")
async def root():
    return {"message": "Hello from Veriply API"}

@app.get("/healthz")
async def health():
    """Health check endpoint."""
    return {"status": "ok"}
