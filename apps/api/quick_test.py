import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from app.models.confidence_log import ConfidenceLog
from app.core.config import settings

async def test():
    engine = create_async_engine(settings.database_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession)
    
    async with async_session() as s:
        r = await s.execute(select(ConfidenceLog).where(ConfidenceLog.hitl_resolved.is_(False)))
        pending = r.scalars().all()
        print(f'PENDING: {len(pending)}')
        
    async with async_session() as s:
        r = await s.execute(select(ConfidenceLog).where(ConfidenceLog.hitl_resolved.is_(True)))
        resolved = r.scalars().all()
        print(f'RESOLVED: {len(resolved)}')
    
    await engine.dispose()

asyncio.run(test())
