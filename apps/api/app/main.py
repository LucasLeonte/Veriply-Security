from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.core.database import init_db
from app.core.migrations import enable_pgvector, enable_rls
from app.api.v1 import auth
from app.api.routes import bots

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
app.include_router(bots.router, prefix="/api/v1")

@app.get("/")
async def root():
    return {"message": "Hello from Veriply API"}
