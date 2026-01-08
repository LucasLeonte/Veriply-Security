"""Create the missing vector index on verified_qa table."""

import asyncio
import sys
from sqlalchemy import text

sys.path.insert(0, 'apps/api')

from app.core.database import AsyncSessionLocal


async def create_vector_index():
    """Create the vector index for semantic search on verified_qa."""
    
    async with AsyncSessionLocal() as db:
        try:
            print("\n" + "="*80)
            print("CREATING VECTOR INDEX ON verified_qa.question_embedding")
            print("="*80 + "\n")
            
            # Create IVFFlat vector index for fast semantic search
            # Using lists=100 (optimal for datasets <10K vectors)
            print("Executing: CREATE INDEX idx_verified_qa_embedding...")
            await db.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_verified_qa_embedding 
                ON verified_qa 
                USING ivfflat (question_embedding vector_cosine_ops)
                WITH (lists = 100)
                WHERE question_embedding IS NOT NULL;
            """))
            
            await db.commit()
            
            print("✓ Vector index created successfully!\n")
            
            # Verify the index was created
            result = await db.execute(
                text("""
                    SELECT indexname, indexdef 
                    FROM pg_indexes 
                    WHERE tablename = 'verified_qa' 
                    AND indexname = 'idx_verified_qa_embedding';
                """)
            )
            index = result.fetchone()
            
            if index:
                index_name, index_def = index
                print(f"Verified: {index_name}")
                print(f"   {index_def}\n")
            else:
                print("⚠️  Warning: Index not found after creation attempt\n")
                
        except Exception as e:
            print(f"❌ Error creating index: {e}\n")
            await db.rollback()
            raise


if __name__ == "__main__":
    asyncio.run(create_vector_index())
