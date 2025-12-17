"""Migration to add bot presentation fields (avatar_url, welcome_message, is_public)."""
import asyncio
import sys
from sqlalchemy import text
from app.core.database import engine

async def migrate():
    """Add avatar_url, welcome_message, and is_public columns to bots table."""
    async with engine.begin() as conn:
        # Check if columns already exist
        result = await conn.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'bots' AND column_name IN ('avatar_url', 'welcome_message', 'is_public')
        """))
        
        existing_columns = {row[0] for row in result.fetchall()}
        
        if len(existing_columns) == 3:
            print("✅ All bot presentation columns already exist")
            return
        
        print("Adding bot presentation fields to bots table...")
        
        # Add avatar_url column if it doesn't exist
        if 'avatar_url' not in existing_columns:
            print("  - Adding avatar_url column...")
            await conn.execute(text("""
                ALTER TABLE bots 
                ADD COLUMN avatar_url VARCHAR(500)
            """))
        else:
            print("  - avatar_url column already exists")
        
        # Add welcome_message column if it doesn't exist
        if 'welcome_message' not in existing_columns:
            print("  - Adding welcome_message column...")
            await conn.execute(text("""
                ALTER TABLE bots 
                ADD COLUMN welcome_message TEXT
            """))
        else:
            print("  - welcome_message column already exists")
        
        # Add is_public column if it doesn't exist
        if 'is_public' not in existing_columns:
            print("  - Adding is_public column...")
            await conn.execute(text("""
                ALTER TABLE bots 
                ADD COLUMN is_public BOOLEAN DEFAULT FALSE
            """))
            
            # Set default value for existing rows
            await conn.execute(text("""
                UPDATE bots 
                SET is_public = FALSE 
                WHERE is_public IS NULL
            """))
            
            # Remove the server default (keep application default)
            await conn.execute(text("""
                ALTER TABLE bots 
                ALTER COLUMN is_public DROP DEFAULT
            """))
        else:
            print("  - is_public column already exists")
        
        print("✅ Migration completed successfully!")

if __name__ == "__main__":
    try:
        asyncio.run(migrate())
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
