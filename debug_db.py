
import asyncio
import sys
import os

# Add the project root to the python path
sys.path.append(os.path.join(os.getcwd(), 'apps', 'api'))

from app.core.database import AsyncSessionLocal
from app.models.email_integration import EmailIntegration
from app.models.user import User
from sqlalchemy import select

import logging
logging.disable(logging.CRITICAL)

async def main():
    async with AsyncSessionLocal() as db:
        # print("Checking Users...")
        # users = await db.execute(select(User))
        # for user in users.scalars().all():
        #    print(f"User: {user.email} (ID: {user.id})")

        # print("\nChecking Email Integrations...")
        query = select(EmailIntegration)
        result = await db.execute(query)
        integrations = result.scalars().all()
        
        if not integrations:
            print("No email integrations found.")
        else:
            for i in integrations:
                print(f"ID: {i.id} | User: {i.user_id} | Tenant: {i.tenant_id} | Active: {i.is_active} | RefreshToken: {bool(i.encrypted_refresh_token)}")

if __name__ == "__main__":
    asyncio.run(main())
