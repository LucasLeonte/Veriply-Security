"""Quick migration to add group_id to bots table."""
import asyncio
import sys
from sqlalchemy import text
from app.core.database import engine

async def migrate():
    """Add group_id column to bots table."""
    async with engine.begin() as conn:
        # Check if column exists
        result = await conn.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'bots' AND column_name = 'group_id'
        """))
        
        if result.first():
            print("✅ group_id column already exists")
            return
        
        print("Adding group_id column to bots table...")
        
        # Add column
        await conn.execute(text("""
            ALTER TABLE bots 
            ADD COLUMN group_id UUID
        """))
        
        # Create a default group for existing bots if needed
        await conn.execute(text("""
            DO $$
            DECLARE
                default_group_id UUID;
                tenant_record RECORD;
            BEGIN
                FOR tenant_record IN SELECT DISTINCT tenant_id FROM bots WHERE group_id IS NULL
                LOOP
                    -- Create a default group for this tenant
                    INSERT INTO groups (id, tenant_id, name, description, created_by, created_at, updated_at)
                    SELECT 
                        gen_random_uuid(),
                        tenant_record.tenant_id,
                        'Default Group',
                        'Auto-created group for existing bots',
                        (SELECT id FROM users WHERE tenant_id = tenant_record.tenant_id LIMIT 1),
                        NOW(),
                        NOW()
                    ON CONFLICT DO NOTHING
                    RETURNING id INTO default_group_id;
                    
                    -- Update bots to use this group
                    UPDATE bots 
                    SET group_id = default_group_id 
                    WHERE tenant_id = tenant_record.tenant_id AND group_id IS NULL;
                END LOOP;
            END $$;
        """))
        
        # Make column NOT NULL
        await conn.execute(text("""
            ALTER TABLE bots ALTER COLUMN group_id SET NOT NULL
        """))
        
        # Add foreign key
        await conn.execute(text("""
            ALTER TABLE bots 
            ADD CONSTRAINT fk_bots_group_id 
            FOREIGN KEY (group_id) REFERENCES groups(id) ON DELETE CASCADE
        """))
        
        # Add indexes
        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_bots_group_id ON bots(group_id)
        """))
        
        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_bots_tenant_group ON bots(tenant_id, group_id)
        """))
        
        # Update unique constraint
        await conn.execute(text("""
            ALTER TABLE bots DROP CONSTRAINT IF EXISTS uq_bots_tenant_name
        """))
        
        await conn.execute(text("""
            ALTER TABLE bots 
            ADD CONSTRAINT uq_bots_tenant_group_name 
            UNIQUE (tenant_id, group_id, name)
        """))
        
        print("✅ Migration completed successfully!")

if __name__ == "__main__":
    try:
        asyncio.run(migrate())
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
