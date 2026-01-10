"""Fix enum values to be lowercase"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "apps" / "api"))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from app.core.settings import settings

async def fix_enum():
    engine = create_async_engine(settings.get_database_url())
    
    async with engine.begin() as conn:
        print("Dropping the routingdecision enum...")
        # First, need to drop the column that uses the enum
        await conn.execute(text("""
            ALTER TABLE confidence_logs 
            DROP COLUMN routing_decision;
        """))
        print("✓ Column dropped")
        
        await conn.execute(text("""
            DROP TYPE routingdecision;
        """))
        print("✓ Enum type dropped")
        
        print("Creating new enum with lowercase values...")
        await conn.execute(text("""
            CREATE TYPE routingdecision AS ENUM ('auto_send', 'hitl');
        """))
        print("✓ Enum type created")
        
        print("Re-adding routing_decision column...")
        await conn.execute(text("""
            ALTER TABLE confidence_logs 
            ADD COLUMN routing_decision routingdecision NOT NULL DEFAULT 'hitl'::routingdecision;
        """))
        print("✓ Column added")
        
        print("Creating index...")
        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_confidence_logs_routing 
            ON confidence_logs(bot_id, routing_decision);
        """))
        print("✓ Index created")
        
        print("\nEnum fix completed successfully!")

if __name__ == "__main__":
    asyncio.run(fix_enum())
