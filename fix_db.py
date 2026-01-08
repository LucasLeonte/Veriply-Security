
import asyncio
import sys
import os
import logging

# Add the project root to the python path
sys.path.append(os.path.join(os.getcwd(), 'apps', 'api'))

from app.core.database import AsyncSessionLocal
from app.models.email_integration import EmailIntegration
from sqlalchemy import select, delete

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    async with AsyncSessionLocal() as db:
        logger.info("Checking for broken Email Integrations...")
        # Find integrations with missing refresh tokens
        query = select(EmailIntegration)
        result = await db.execute(query)
        integrations = result.scalars().all()
        
        for i in integrations:
            logger.info(f"checking integration {i.id}, token: '{i.encrypted_refresh_token}'")
            if not i.encrypted_refresh_token:
                logger.info(f"Deleting broken integration ID: {i.id} (No refresh token)")
                await db.delete(i)
        
        await db.commit()
        logger.info("Cleanup complete.")

if __name__ == "__main__":
    asyncio.run(main())
