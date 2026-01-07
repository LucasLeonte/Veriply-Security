#!/usr/bin/env python3
"""Quick check of email_integrations for testing monitoring endpoints."""
import asyncio
import sys
from pathlib import Path

# Adjust sys.path to load app from apps/api
sys.path.insert(0, str(Path(__file__).parent / 'apps' / 'api'))

from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from app.core.settings import settings


async def check():
    engine = create_async_engine(settings.DATABASE_URL)
    async with engine.begin() as conn:
        res = await conn.execute(
            text('SELECT id, provider, is_active, is_paused, last_poll_at, next_poll_at FROM email_integrations LIMIT 3')
        )
        print('\nEmail Integrations:')
        for row in res:
            print(f'  ID: {row[0]}')
            print(f'  Provider: {row[1]}')
            print(f'  Active: {row[2]}, Paused: {row[3]}')
            print(f'  Last poll: {row[4]}')
            print(f'  Next poll: {row[5]}')
            print()
    await engine.dispose()


if __name__ == '__main__':
    asyncio.run(check())
