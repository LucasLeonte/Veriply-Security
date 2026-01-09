import asyncio
import sys
import os

# Add the parent directory to sys.path to allow imports
sys.path.append(r"C:\Users\Dario\OneDrive - Erasmushogeschool Brussel\Erasmus Hogeschool\2025-2026\IT Project\Veriply\apps\api")

from sqlalchemy import select
from app.db.session import async_session_factory
from app.models.email_integrations import EmailIntegration

async def main():
    async with async_session_factory() as session:
        result = await session.execute(select(EmailIntegration))
        integrations = result.scalars().all()
        print(f"Found {len(integrations)} integrations")
        for i in integrations:
            print(f"ID: {i.id}")
            print(f"Provider: {i.provider}")
            print(f"User: {i.user_id}")
            print(f"Active: {i.is_active}")
            print(f"Has Refresh Token: {i.encrypted_refresh_token is not None}")
            print("-" * 20)

if __name__ == "__main__":
    asyncio.run(main())
