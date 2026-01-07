"""Add missing routing_decision column to confidence_logs table"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "apps" / "api"))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from app.core.settings import settings

async def fix_schema():
    engine = create_async_engine(settings.get_database_url())
    
    async with engine.begin() as conn:
        print("Checking if routing_decision column exists...")
        result = await conn.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.columns 
                WHERE table_name = 'confidence_logs' 
                AND column_name = 'routing_decision'
            )
        """))
        exists = result.scalar()
        
        if exists:
            print("✓ routing_decision column already exists")
            return
        
        print("Creating routingdecision enum type if it doesn't exist...")
        await conn.execute(text("""
            DO $$ BEGIN
                CREATE TYPE routingdecision AS ENUM ('auto_send', 'hitl');
            EXCEPTION
                WHEN duplicate_object THEN null;
            END $$;
        """))
        print("✓ Enum type created/verified")
        
        print("Adding routing_decision column...")
        await conn.execute(text("""
            ALTER TABLE confidence_logs 
            ADD COLUMN routing_decision routingdecision NOT NULL DEFAULT 'HITL'::routingdecision;
        """))
        print("✓ Column added")
        
        print("Creating index on routing_decision...")
        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_confidence_logs_routing 
            ON confidence_logs(bot_id, routing_decision);
        """))
        print("✓ Index created")
        
        print("\nSchema fix completed successfully!")
        
        # Verify
        result = await conn.execute(text("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns 
            WHERE table_name = 'confidence_logs' 
            AND column_name = 'routing_decision'
        """))
        row = result.fetchone()
        if row:
            print(f"\nVerification: {row[0]} ({row[1]}, nullable: {row[2]})")

if __name__ == "__main__":
    asyncio.run(fix_schema())
