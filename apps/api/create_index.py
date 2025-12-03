"""Create vector index for fast similarity search."""
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def create_index():
    engine = create_async_engine("postgresql+asyncpg://postgres:DarioDML@10.2.160.214:5432/vector_db")
    
    async with engine.connect() as conn:
        print("Creating HNSW index for fast vector similarity search...")
        print("(This may take a minute for 417 vectors)")
        
        # Create HNSW index with cosine distance
        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS embeddings_embedding_idx 
            ON embeddings 
            USING hnsw (embedding vector_cosine_ops)
            WITH (m = 16, ef_construction = 64)
        """))
        
        await conn.commit()
        print("✓ Index created successfully!")
        
        # Test a simple similarity search
        print("\nTesting similarity search for 'authentication'...")
        result = await conn.execute(text("""
            WITH query_vec AS (
                SELECT embedding FROM embeddings 
                WHERE text ILIKE '%authentication%' 
                LIMIT 1
            )
            SELECT 
                LEFT(text, 100) as preview,
                1 - (embedding <=> (SELECT embedding FROM query_vec)) as similarity
            FROM embeddings
            ORDER BY embedding <=> (SELECT embedding FROM query_vec)
            LIMIT 3
        """))
        
        for i, row in enumerate(result, 1):
            print(f"\n{i}. Similarity: {row.similarity:.3f}")
            print(f"   {row.preview}...")
    
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(create_index())
