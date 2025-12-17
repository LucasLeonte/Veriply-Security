"""Script to update vector dimensions from 1024 to 768."""
import asyncio
import asyncpg
import sys
from pathlib import Path

# Add app directory to path
sys.path.insert(0, str(Path(__file__).parent))
from app.core.settings import settings


async def update_vector_dimensions():
    """Update chunks table vector column from 1024 to 768 dimensions."""
    try:
        # Get database URL and extract connection params
        db_url = settings.DATABASE_URL_SYNC  # Use sync URL without +asyncpg
        print(f"Connecting to database...")
        
        # Parse connection string to get individual components
        # Format: postgresql://user:password@host:port/database
        import re
        match = re.match(r'postgresql://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)', db_url)
        if not match:
            raise ValueError(f"Could not parse database URL")
        
        user, password, host, port, database = match.groups()
        
        # Connect to database
        conn = await asyncpg.connect(
            host=host,
            port=int(port),
            user=user,
            password=password,
            database=database
        )
        
        print("Connected to database")
        
        # Drop existing vector column
        print("Dropping old vector column...")
        await conn.execute("ALTER TABLE chunks DROP COLUMN IF EXISTS vector;")
        
        # Add new vector column with 768 dimensions
        print("Adding new vector column with 768 dimensions...")
        await conn.execute("ALTER TABLE chunks ADD COLUMN vector vector(768);")
        
        # Drop old index if exists
        print("Dropping old index...")
        await conn.execute("DROP INDEX IF EXISTS idx_chunks_tenant_group_vector;")
        
        # Create new index
        print("Creating new index...")
        await conn.execute("""
            CREATE INDEX idx_chunks_tenant_group_vector 
            ON chunks USING ivfflat (vector vector_cosine_ops) 
            WITH (lists = 100)
            WHERE vector IS NOT NULL;
        """)
        
        await conn.close()
        print("✅ Vector column successfully updated to 768 dimensions!")
        
    except Exception as e:
        print(f"❌ Error updating vector dimensions: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(update_vector_dimensions())
