"""Mark already-applied migrations as complete."""
import asyncio
from app.core.database import AsyncSessionLocal
from sqlalchemy import text

async def mark_migrations():
    async with AsyncSessionLocal() as db:
        # The migrations that have already been applied but not marked in alembic_version
        migrations_to_mark = [
            '012_add_email_integrations',
            '013_add_integration_credentials',
            '014_add_email_monitoring_rules',
            '015_add_email_processing_queue',
            '016_update_email_integrations_monitoring',
        ]
        
        for migration in migrations_to_mark:
            try:
                await db.execute(text(f"INSERT INTO alembic_version (version_num) VALUES ('{migration}')"))
                print(f"[OK] Marked {migration} as applied")
            except Exception as e:
                print(f"[FAIL] Failed to mark {migration}: {e}")
        
        await db.commit()
        
        # Verify
        result = await db.execute(text('SELECT version_num FROM alembic_version ORDER BY version_num'))
        rows = result.fetchall()
        print('\nApplied migrations:')
        for row in rows:
            print(f'  {row[0]}')

asyncio.run(mark_migrations())
