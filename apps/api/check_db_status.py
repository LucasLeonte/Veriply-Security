
import asyncio
import os
import sys
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

# Assuming .env is loaded or vars are set. If not, we might need to load them.
# For this script we'll try to use the default connection string if env var not set
# or try to read .env
from dotenv import load_dotenv
load_dotenv()

DB_URL = os.environ.get("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/veriply")

async def check_db():
    print(f"Connecting to {DB_URL}...")
    try:
        engine = create_async_engine(DB_URL)
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT count(*) FROM pg_stat_activity;"))
            count = result.scalar()
            print(f"SUCCESS: Connected to database.")
            print(f"Active connections: {count}")
            
            result = await conn.execute(text("SELECT datname, usename, state FROM pg_stat_activity;"))
            rows = result.fetchall()
            print("\nDetailed connections:")
            for row in rows:
                print(row)
    except Exception as e:
        print(f"FAILURE: Could not connect to database. Error: {e}")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(check_db())
