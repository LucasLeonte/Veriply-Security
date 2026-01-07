import asyncio
from sqlalchemy import text
from app.core.database import AsyncSessionLocal

async def check():
    async with AsyncSessionLocal() as db:
        # Check chat_messages table structure
        result = await db.execute(text("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'chat_messages'
            ORDER BY ordinal_position
        """))
        
        cols = result.fetchall()
        print('=== CHAT_MESSAGES TABLE COLUMNS ===')
        for col in cols:
            print(f'  {col[0]}: {col[1]}')

asyncio.run(check())
