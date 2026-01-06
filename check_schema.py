"""Check database schema for confidence_logs table"""
import asyncio
import sys
from pathlib import Path

# Add apps/api to path
sys.path.insert(0, str(Path(__file__).parent / "apps" / "api"))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.core.settings import settings

async def check_schema():
    engine = create_async_engine(settings.get_database_url(), echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # Check if confidence_logs table exists
        result = await session.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'confidence_logs'
            )
        """))
        exists = result.scalar()
        print(f'confidence_logs table exists: {exists}')
        
        if exists:
            # Get all columns
            result = await session.execute(text("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'confidence_logs'
                ORDER BY ordinal_position
            """))
            columns = result.fetchall()
            print(f'\nconfidence_logs columns:')
            for col in columns:
                print(f'  {col[0]}: {col[1]}')

if __name__ == "__main__":
    asyncio.run(check_schema())
