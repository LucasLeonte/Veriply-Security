"""Check database indexes on verified_qa table."""

import asyncio
import sys
from sqlalchemy import text

sys.path.insert(0, 'apps/api')

from app.core.database import AsyncSessionLocal


async def check_indexes():
    """Check all indexes on verified_qa table."""
    
    async with AsyncSessionLocal() as db:
        # Get all indexes on verified_qa table
        result = await db.execute(
            text("""
                SELECT 
                    indexname, 
                    indexdef 
                FROM pg_indexes 
                WHERE tablename = 'verified_qa'
                ORDER BY indexname;
            """)
        )
        indexes = result.fetchall()
        
        print(f"\n{'='*80}")
        print(f"INDEXES ON verified_qa TABLE")
        print(f"{'='*80}\n")
        
        if indexes:
            for idx, (index_name, index_def) in enumerate(indexes, 1):
                print(f"{idx}. {index_name}")
                print(f"   {index_def}\n")
        else:
            print("NO INDEXES FOUND!\n")
        
        # Check if the table exists
        table_check = await db.execute(
            text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'verified_qa'
                );
            """)
        )
        table_exists = table_check.scalar()
        print(f"Table 'verified_qa' exists: {table_exists}\n")
        
        # Check if pgvector extension is installed
        ext_check = await db.execute(
            text("""
                SELECT EXISTS (
                    SELECT FROM pg_extension 
                    WHERE extname = 'vector'
                );
            """)
        )
        ext_exists = ext_check.scalar()
        print(f"pgvector extension installed: {ext_exists}\n")


if __name__ == "__main__":
    asyncio.run(check_indexes())
