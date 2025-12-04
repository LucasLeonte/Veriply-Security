from sqlalchemy import text
from app.core.database import engine

async def enable_pgvector():
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))

async def enable_rls():
    async with engine.begin() as conn:
        await conn.execute(text("ALTER TABLE users ENABLE ROW LEVEL SECURITY;"))
        await conn.execute(text("CREATE POLICY tenant_isolation ON users USING (tenant_id = current_setting('app.current_tenant_id')::uuid);") )
