"""Check enum types in database"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "apps" / "api"))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from app.core.settings import settings

async def check_enums():
    engine = create_async_engine(settings.get_database_url())
    
    async with engine.begin() as conn:
        result = await conn.execute(text("""
            SELECT t.typname, e.enumlabel
            FROM pg_type t 
            JOIN pg_enum e ON t.oid = e.enumtypid  
            WHERE t.typname = 'routingdecision'
            ORDER BY e.enumsortorder
        """))
        rows = result.fetchall()
        
        if rows:
            print("routingdecision enum values:")
            for row in rows:
                print(f"  - {row[1]}")
        else:
            print("routingdecision enum not found")

asyncio.run(check_enums())
