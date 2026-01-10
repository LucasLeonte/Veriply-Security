"""Check applied migrations"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "apps" / "api"))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from app.core.settings import settings

async def check():
    engine = create_async_engine(settings.get_database_url())
    async with engine.begin() as conn:
        result = await conn.execute(text('SELECT version_num FROM alembic_version'))
        versions = [r[0] for r in result.fetchall()]
        print('Applied migrations:', versions)

asyncio.run(check())
