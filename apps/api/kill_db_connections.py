
import asyncio
import os
import sys
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from dotenv import load_dotenv

load_dotenv()

DB_URL = os.environ.get("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/veriply")

async def kill_connections():
    print(f"Connecting to {DB_URL}...")
    try:
        engine = create_async_engine(DB_URL)
        async with engine.connect() as conn:
            # Terminate all connections to this database except the one we are using
            sql = """
            SELECT pg_terminate_backend(pid) 
            FROM pg_stat_activity 
            WHERE datname = 'vector_db' 
            AND pid <> pg_backend_pid();
            """
            print("Terminating existing connections...")
            await conn.execute(text(sql))
            print("SUCCESS: Connections terminated.")
            
            # Verify count
            result = await conn.execute(text("SELECT count(*) FROM pg_stat_activity WHERE datname='vector_db';"))
            count = result.scalar()
            print(f"Active connections remaining: {count}")

    except Exception as e:
        print(f"FAILURE: Could not terminate connections. Error: {e}")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(kill_connections())
