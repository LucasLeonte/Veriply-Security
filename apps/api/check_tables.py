"""Manually apply KB email migrations"""
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql+asyncpg://postgres:postgres@10.2.160.214:5432/vector_db')
if not DATABASE_URL.startswith('postgresql+asyncpg://'):
    DATABASE_URL = DATABASE_URL.replace('postgresql://', 'postgresql+asyncpg://')

engine = create_async_engine(DATABASE_URL)

async def check_and_create_tables():
    async with engine.begin() as conn:
        # Check if kb_emails table exists
        result = await conn.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'kb_emails'
            );
        """))
        exists = result.fetchone()[0]
        print(f"kb_emails table exists: {exists}")
        
        # Check if user_email_history table exists
        result = await conn.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'user_email_history'
            );
        """))
        exists = result.fetchone()[0]
        print(f"user_email_history table exists: {exists}")
        
        # Check if user_writing_styles table exists
        result = await conn.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'user_writing_styles'
            );
        """))
        exists = result.fetchone()[0]
        print(f"user_writing_styles table exists: {exists}")

if __name__ == '__main__':
    asyncio.run(check_and_create_tables())
