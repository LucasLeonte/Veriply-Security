import asyncio
import sys
sys.path.insert(0, 'apps/api')
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.core.settings import settings
import json

async def check():
    engine = create_async_engine(settings.get_database_url())
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        result = await session.execute(text(
            "SELECT metadata_json FROM confidence_logs WHERE id='cb5de0eb-daf0-4af5-920a-71b50d69b4c6'"
        ))
        row = result.fetchone()
        if row and row[0]:
            print(json.dumps(row[0], indent=2, default=str))

asyncio.run(check())
