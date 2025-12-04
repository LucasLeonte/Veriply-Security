from sqlalchemy import text
from app.core.database import engine

async def enable_pgvector():
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))

async def enable_rls():
    async with engine.begin() as conn:
        await conn.execute(text("ALTER TABLE users ENABLE ROW LEVEL SECURITY;"))
        # Check if policy exists before creating it
        result = await conn.execute(text("""
            SELECT 1 FROM pg_policies 
            WHERE tablename = 'users' AND policyname = 'tenant_isolation';
        """))
        if not result.scalar():
            await conn.execute(text("CREATE POLICY tenant_isolation ON users USING (tenant_id = current_setting('app.current_tenant_id')::uuid);"))
