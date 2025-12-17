import asyncio
from app.core.database import engine
from sqlalchemy import text

async def check():
    async with engine.begin() as conn:
        result = await conn.execute(text('SELECT COUNT(*) FROM embeddings'))
        print(f'Total embeddings: {result.scalar()}')
        
        result = await conn.execute(text('SELECT bot_id, COUNT(*) FROM embeddings GROUP BY bot_id'))
        print('Per bot:')
        for row in result:
            print(f'  Bot {row[0]}: {row[1]} chunks')

asyncio.run(check())
