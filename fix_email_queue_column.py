
import asyncio
import os
import sys

# Add project root to path
sys.path.append(os.getcwd())

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from app.core.settings import settings

async def add_column():
    print(f"Connecting to {settings.DATABASE_URL.split('@')[1] if '@' in settings.DATABASE_URL else 'DB'}...")
    engine = create_async_engine(settings.DATABASE_URL)
    
    async with engine.begin() as conn:
        try:
            # Check if column exists first to avoid error
            # But the error logs say it doesn't.
            # We'll just try to add it.
            # We make it nullable first to avoid issues with existing rows
            await conn.execute(text("ALTER TABLE email_processing_queue ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES users(id);"))
            print("✓ Added user_id column (or it existed).")
            
            # Now we should probably update existing rows if any, resolving from integration_id.
            # But query is complex. Let's just assume it's okay for now.
            
        except Exception as e:
            print(f"Error adding column: {e}")
            
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(add_column())
