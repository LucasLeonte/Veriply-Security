
import asyncio
import os
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Mock environment if needed, or rely on .env (loaded by app.core.settings usually)
# We'll import the settings from the app to be safe
import sys
sys.path.append(os.getcwd())

from app.core.settings import settings
from app.models.verified_qa import VerifiedQA
from app.core.database import set_tenant_context

async def check_offensive_content():
    engine = create_async_engine(settings.DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # We need to check all tenants theoretically, or the current one if we knew it.
        # But VerifiedQA is tenant-isolated.
        # Let's search broadly or just try to list all VerifiedQA items with the offensive keyword.
        # Since RLS might block us if we don't set a tenant, we might need to be careful.
        # However, usually the DB user has access. The RLS is often application-level or DB-level polices.
        # If DB level, we need to bypass or set context.
        # Let's try raw SQL to bypass ORM-level filters if any, though the model uses standard SQLAlchemy.
        
        # Query to find the specific offensive item
        query = select(VerifiedQA).where(VerifiedQA.answer_text.ilike("%nigger%"))
        
        try:
            result = await session.execute(query)
            items = result.scalars().all()
            
            if items:
                print(f"FOUND {len(items)} OFFENSIVE ITEMS. DELETING NOW...")
                for item in items:
                    print(f"Deleting ID: {item.id}")
                    await session.delete(item)
                
                await session.commit()
                print("✓ Successfully deleted offensive items.")
            else:
                print("No active offensive items found with that keyword in verified_qa.")
                
        except Exception as e:
            print(f"Error querying: {e}")
            
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(check_offensive_content())
