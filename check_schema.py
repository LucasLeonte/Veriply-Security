"""Check database schema for users table."""
import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'apps', 'api'))

from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from app.core.settings import settings

async def check_schema():
    engine = create_async_engine(settings.get_database_url())
    
    async with engine.connect() as conn:
        # Check is_active column type
        result = await conn.execute(text("""
            SELECT column_name, data_type, column_default
            FROM information_schema.columns 
            WHERE table_name = 'users' AND column_name = 'is_active'
        """))
        print('is_active column info:')
        for row in result:
            print(f'  name: {row[0]}, type: {row[1]}, default: {row[2]}')
        
        # Check actual values
        result = await conn.execute(text("SELECT DISTINCT is_active, pg_typeof(is_active) FROM users"))
        print('\nActual is_active values and types:')
        for row in result:
            print(f'  value: {row[0]}, type: {row[1]}')
    
    await engine.dispose()

if __name__ == '__main__':
    asyncio.run(check_schema())
