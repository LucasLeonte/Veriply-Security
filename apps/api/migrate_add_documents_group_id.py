"""Add group_id to documents and chunks tables."""
import asyncio
from sqlalchemy import text
from app.core.database import engine

async def migrate():
    """Add group_id column to documents and chunks tables."""
    async with engine.begin() as conn:
        # Check if column exists in documents
        result = await conn.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'documents' AND column_name = 'group_id'
        """))
        
        if result.first():
            print("✅ documents.group_id already exists")
        else:
            print("Adding group_id to documents table...")
            
            # Add column
            await conn.execute(text("""
                ALTER TABLE documents 
                ADD COLUMN group_id UUID
            """))
            
            # Set group_id from bot's group_id
            await conn.execute(text("""
                UPDATE documents 
                SET group_id = bots.group_id 
                FROM bots 
                WHERE documents.bot_id = bots.id AND documents.group_id IS NULL
            """))
            
            # Make column NOT NULL
            await conn.execute(text("""
                ALTER TABLE documents ALTER COLUMN group_id SET NOT NULL
            """))
            
            # Add foreign key
            await conn.execute(text("""
                ALTER TABLE documents 
                ADD CONSTRAINT fk_documents_group_id 
                FOREIGN KEY (group_id) REFERENCES groups(id) ON DELETE CASCADE
            """))
            
            # Add indexes
            await conn.execute(text("""
                CREATE INDEX IF NOT EXISTS ix_documents_group_id ON documents(group_id)
            """))
            
            await conn.execute(text("""
                CREATE INDEX IF NOT EXISTS ix_documents_tenant_group ON documents(tenant_id, group_id)
            """))
            
            print("✅ Added group_id to documents")
        
        # Check if column exists in chunks
        result = await conn.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'chunks' AND column_name = 'group_id'
        """))
        
        if result.first():
            print("✅ chunks.group_id already exists")
        else:
            print("Adding group_id to chunks table...")
            
            # Add column
            await conn.execute(text("""
                ALTER TABLE chunks 
                ADD COLUMN group_id UUID
            """))
            
            # Set group_id from bot's group_id
            await conn.execute(text("""
                UPDATE chunks 
                SET group_id = bots.group_id 
                FROM bots 
                WHERE chunks.bot_id = bots.id AND chunks.group_id IS NULL
            """))
            
            # Make column NOT NULL
            await conn.execute(text("""
                ALTER TABLE chunks ALTER COLUMN group_id SET NOT NULL
            """))
            
            # Add foreign key
            await conn.execute(text("""
                ALTER TABLE chunks 
                ADD CONSTRAINT fk_chunks_group_id 
                FOREIGN KEY (group_id) REFERENCES groups(id) ON DELETE CASCADE
            """))
            
            # Add indexes
            await conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_chunks_group_id ON chunks(group_id)
            """))
            
            await conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_chunks_bot_tenant_group ON chunks(bot_id, tenant_id, group_id)
            """))
            
            print("✅ Added group_id to chunks")
        
        # Check and rename uploaded_by to uploader_id in documents if needed
        result = await conn.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'documents' AND column_name = 'uploaded_by'
        """))
        
        if result.first():
            print("Renaming uploaded_by to uploader_id...")
            await conn.execute(text("""
                ALTER TABLE documents 
                RENAME COLUMN uploaded_by TO uploader_id
            """))
            print("✅ Renamed uploaded_by to uploader_id")
        
        # Add deleted_at column if missing
        result = await conn.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'documents' AND column_name = 'deleted_at'
        """))
        
        if not result.first():
            print("Adding deleted_at to documents...")
            await conn.execute(text("""
                ALTER TABLE documents 
                ADD COLUMN deleted_at TIMESTAMP
            """))
            await conn.execute(text("""
                CREATE INDEX IF NOT EXISTS ix_documents_deleted ON documents(deleted_at)
            """))
            print("✅ Added deleted_at to documents")
        
        print("✅ Migration completed successfully!")

if __name__ == "__main__":
    try:
        asyncio.run(migrate())
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
