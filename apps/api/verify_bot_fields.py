"""Verify bot presentation fields migration."""
import asyncio
from sqlalchemy import text
from app.core.database import engine

async def verify():
    """Check if the new columns exist."""
    async with engine.begin() as conn:
        result = await conn.execute(text("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns 
            WHERE table_name = 'bots' 
            AND column_name IN ('avatar_url', 'welcome_message', 'is_public')
            ORDER BY column_name
        """))
        
        print("\nBot presentation columns:")
        for row in result.fetchall():
            print(f"  - {row[0]}: {row[1]} (nullable: {row[2]})")

if __name__ == "__main__":
    asyncio.run(verify())
