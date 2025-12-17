"""
Migration: Remove bot_id from documents and chunks - Knowledge base is per GROUP not per BOT
"""
import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

async def migrate():
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise ValueError("DATABASE_URL not set")
    
    # Parse asyncpg connection from DATABASE_URL
    conn = await asyncpg.connect(db_url.replace("postgresql+asyncpg://", "postgresql://"))
    
    try:
        # Check if bot_id still exists in documents
        result = await conn.fetchval("""
            SELECT COUNT(*) 
            FROM information_schema.columns 
            WHERE table_name = 'documents' AND column_name = 'bot_id'
        """)
        
        if result == 0:
            print("⚠️  bot_id column already removed from documents table")
            documents_done = True
        else:
            documents_done = False
        
        # Check if bot_id still exists in chunks
        result = await conn.fetchval("""
            SELECT COUNT(*) 
            FROM information_schema.columns 
            WHERE table_name = 'chunks' AND column_name = 'bot_id'
        """)
        
        if result == 0:
            print("⚠️  bot_id column already removed from chunks table")
            chunks_done = True
        else:
            chunks_done = False
        
        if documents_done and chunks_done:
            print("✅ Migration already completed!")
            return
        
        # Start transaction
        async with conn.transaction():
            # 1. Remove bot_id from documents table
            if not documents_done:
                print("\nRemoving bot_id from documents table...")
                
                # Drop foreign key constraint first
                await conn.execute("""
                    ALTER TABLE documents 
                    DROP CONSTRAINT IF EXISTS fk_documents_bot_id
                """)
                print("  - Dropped foreign key constraint fk_documents_bot_id")
                
                # Drop indexes
                await conn.execute("DROP INDEX IF EXISTS ix_documents_bot_id")
                print("  - Dropped index ix_documents_bot_id")
                
                await conn.execute("DROP INDEX IF EXISTS ix_documents_tenant_bot")
                print("  - Dropped index ix_documents_tenant_bot")
                
                # Drop the column
                await conn.execute("ALTER TABLE documents DROP COLUMN bot_id")
                print("  - Dropped bot_id column")
                
                print("✅ Removed bot_id from documents")
            
            # 2. Remove bot_id from chunks table
            if not chunks_done:
                print("\nRemoving bot_id from chunks table...")
                
                # Drop foreign key constraint first
                await conn.execute("""
                    ALTER TABLE chunks 
                    DROP CONSTRAINT IF EXISTS fk_chunks_bot_id
                """)
                print("  - Dropped foreign key constraint fk_chunks_bot_id")
                
                # Drop indexes
                await conn.execute("DROP INDEX IF EXISTS idx_chunks_bot_id")
                print("  - Dropped index idx_chunks_bot_id")
                
                await conn.execute("DROP INDEX IF EXISTS idx_chunks_bot_tenant")
                print("  - Dropped index idx_chunks_bot_tenant")
                
                # Drop the column
                await conn.execute("ALTER TABLE chunks DROP COLUMN bot_id")
                print("  - Dropped bot_id column")
                
                print("✅ Removed bot_id from chunks")
            
            print("\n✅ Migration completed successfully!")
            print("   Knowledge base is now GROUP-SCOPED (not bot-scoped)")
    
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(migrate())
