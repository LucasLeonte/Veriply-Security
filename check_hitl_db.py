"""Check HITL items in database"""
import asyncio
import sys
from pathlib import Path

# Add apps/api to path
sys.path.insert(0, str(Path(__file__).parent / "apps" / "api"))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.core.settings import settings

async def check_hitl():
    engine = create_async_engine(settings.get_database_url(), echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # Check total confidence logs
        result = await session.execute(text('SELECT COUNT(*) FROM confidence_logs'))
        total = result.scalar()
        print(f'Total confidence_logs: {total}')
        
        # Check HITL items
        result = await session.execute(text("""
            SELECT COUNT(*) FROM confidence_logs 
            WHERE routing_decision = 'hitl' AND hitl_resolved = false
        """))
        hitl_pending = result.scalar()
        print(f'HITL pending items: {hitl_pending}')
        
        # Show recent HITL items with details
        result = await session.execute(text("""
            SELECT id, query_text, overall_confidence, routing_decision, hitl_resolved, created_at, tenant_id, bot_id
            FROM confidence_logs 
            WHERE routing_decision = 'hitl' 
            ORDER BY created_at DESC 
            LIMIT 5
        """))
        rows = result.fetchall()
        print(f'\nRecent HITL items:')
        for row in rows:
            print(f'  ID: {row[0]}')
            print(f'  Query: {row[1][:50] if row[1] else "None"}...')
            print(f'  Confidence: {row[2]}')
            print(f'  Decision: {row[3]}')
            print(f'  Resolved: {row[4]}')
            print(f'  Created: {row[5]}')
            print(f'  Tenant: {row[6]}')
            print(f'  Bot: {row[7]}')
            print()
        
        # Check most recent query regardless of routing
        result = await session.execute(text("""
            SELECT id, query_text, overall_confidence, routing_decision, hitl_resolved, created_at
            FROM confidence_logs 
            ORDER BY created_at DESC 
            LIMIT 3
        """))
        rows = result.fetchall()
        print(f'\nMost recent queries (any routing):')
        for row in rows:
            print(f'  Query: {row[1][:80] if row[1] else "None"}')
            print(f'  Confidence: {row[2]} | Decision: {row[3]} | Resolved: {row[4]}')
            print()

if __name__ == "__main__":
    asyncio.run(check_hitl())
