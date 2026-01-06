"""Check if there are HITL items in the database"""
import asyncio
import sys
sys.path.insert(0, 'apps/api')

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import os

DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql+asyncpg://veriply:veriply@localhost:5432/veriply')
engine = create_async_engine(DATABASE_URL)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def check():
    async with async_session() as session:
        from app.models.confidence_log import ConfidenceLog, RoutingDecision
        
        # Check total confidence logs
        result = await session.execute(select(ConfidenceLog))
        all_logs = result.scalars().all()
        print(f'Total ConfidenceLog entries: {len(all_logs)}')
        
        # Check HITL unresolved
        result = await session.execute(
            select(ConfidenceLog).where(
                and_(
                    ConfidenceLog.routing_decision == RoutingDecision.hitl,
                    ConfidenceLog.hitl_resolved == False
                )
            )
        )
        hitl_logs = result.scalars().all()
        print(f'HITL unresolved entries: {len(hitl_logs)}')
        
        # Show latest 5 entries
        if hitl_logs:
            print('\nLatest HITL items:')
            for log in hitl_logs[-5:]:
                query_preview = log.query_text[:50] if log.query_text else "N/A"
                print(f'  ID: {log.id}')
                print(f'    Query: {query_preview}...')
                print(f'    Tenant: {log.tenant_id}')
                print(f'    Group: {log.group_id}')
                print(f'    Decision: {log.routing_decision}')
                print(f'    Resolved: {log.hitl_resolved}')
                print(f'    Created: {log.created_at}')
                print()

asyncio.run(check())
