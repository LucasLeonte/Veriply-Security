"""Quick script to verify embeddings in the database."""
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def verify():
    engine = create_async_engine("postgresql+asyncpg://postgres:DarioDML@10.2.160.214:5432/vector_db")
    
    async with engine.connect() as conn:
        # Count total chunks
        result = await conn.execute(text("SELECT COUNT(*) FROM embeddings"))
        count = result.scalar()
        print(f"✓ Total chunks in database: {count}")
        
        # Check embedding dimensions
        result = await conn.execute(text("SELECT vector_dims(embedding) FROM embeddings LIMIT 1"))
        dims = result.scalar()
        print(f"✓ Embedding dimensions: {dims}")
        
        # Sample query
        result = await conn.execute(text("""
            SELECT LEFT(text, 80) as preview, metadata 
            FROM embeddings 
            LIMIT 3
        """))
        print(f"\n✓ Sample data:")
        for row in result:
            print(f"  - {row.preview}...")
            
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(verify())
