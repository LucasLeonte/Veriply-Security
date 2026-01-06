from sqlalchemy import text
from app.core.database import engine
import logging

logger = logging.getLogger(__name__)

async def enable_pgvector():
    """Enable pgvector extension for vector similarity search."""
    try:
        async with engine.begin() as conn:
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
            logger.info("✓ pgvector extension enabled")
    except Exception as e:
        logger.warning(f"Could not enable pgvector (may already be enabled): {e}")

async def enable_rls():
    """Enable Row Level Security on users table (optional - skip on error)."""
    try:
        async with engine.begin() as conn:
            # Check if RLS is already enabled
            result = await conn.execute(text("""
                SELECT relrowsecurity 
                FROM pg_class 
                WHERE relname = 'users' AND relnamespace = 'public'::regnamespace;
            """))
            rls_enabled = result.scalar()
            
            if not rls_enabled:
                await conn.execute(text("ALTER TABLE users ENABLE ROW LEVEL SECURITY;"))
                logger.info("✓ Row Level Security enabled on users table")
            else:
                logger.info("✓ Row Level Security already enabled on users table")
            
            # Check if policy exists before creating it
            result = await conn.execute(text("""
                SELECT 1 FROM pg_policies 
                WHERE tablename = 'users' AND policyname = 'tenant_isolation';
            """))
            if not result.scalar():
                await conn.execute(text("""
                    CREATE POLICY tenant_isolation ON users 
                    USING (tenant_id = current_setting('app.current_tenant_id', true)::uuid);
                """))
                logger.info("✓ Tenant isolation policy created")
            else:
                logger.info("✓ Tenant isolation policy already exists")
                
    except Exception as e:
        # RLS is optional - don't fail startup if it errors
        logger.warning(f"Could not enable RLS (this is optional): {e}")
        logger.info("Continuing without RLS...")
