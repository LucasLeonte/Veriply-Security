from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.core.database import init_db
from app.core.migrations import enable_pgvector, enable_rls

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()
    await enable_pgvector()
    await enable_rls()
    yield
    # Shutdown (optional)

app = FastAPI(title="Veriply API", lifespan=lifespan)

@app.get("/")
async def root():
    return {"message": "Hello from Veriply API"}
