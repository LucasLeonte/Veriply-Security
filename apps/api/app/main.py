from fastapi import FastAPI, Depends
from apps.api.app.core.database import get_db, init_db
from apps.api.app.core.migrations import enable_pgvector, enable_rls

app = FastAPI(title="Veriply API")

@app.on_event("startup")
async def startup():
    await init_db()
    await enable_pgvector()
    await enable_rls()

@app.get("/")
async def root():
    return {"message": "Hello from Veriply API"}
