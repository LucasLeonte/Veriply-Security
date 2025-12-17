"""Add users to their tenant's Default Group as members."""
import asyncio
import sys
from sqlalchemy import text
from app.core.database import engine

async def migrate():
    """Add all users to their tenant's Default Group."""
    async with engine.begin() as conn:
        print("Adding users to Default Groups...")
        
        # Add all users to their tenant's default group
        result = await conn.execute(text("""
            INSERT INTO group_members (id, group_id, user_id, role, invited_at, invited_by_id)
            SELECT 
                gen_random_uuid(),
                g.id,
                u.id,
                'group_admin'::grouprole,  -- Make all users admins of their default group
                NOW(),
                u.id  -- Self-invited
            FROM users u
            JOIN groups g ON g.tenant_id = u.tenant_id AND g.name = 'Default Group'
            WHERE NOT EXISTS (
                SELECT 1 FROM group_members gm 
                WHERE gm.group_id = g.id AND gm.user_id = u.id
            )
            RETURNING id
        """))
        
        count = len(result.all())
        print(f"✅ Added {count} users to their Default Groups")

if __name__ == "__main__":
    try:
        asyncio.run(migrate())
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
