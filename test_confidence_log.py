"""Test confidence logging"""
import asyncio
import sys
from pathlib import Path
from uuid import uuid4
from decimal import Decimal

sys.path.insert(0, str(Path(__file__).parent / "apps" / "api"))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.core.settings import settings
from app.models.confidence_log import ConfidenceLog, RoutingDecision

async def test_logging():
    engine = create_async_engine(settings.get_database_url(), echo=True)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # First, get a valid bot_id and tenant_id
        result = await session.execute(text("SELECT id, tenant_id FROM bots LIMIT 1"))
        row = result.fetchone()
        if not row:
            print("No bots found!")
            return
        
        bot_id, tenant_id = row[0], row[1]
        print(f"Using bot_id: {bot_id}, tenant_id: {tenant_id}")
        
        try:
            log_entry = ConfidenceLog(
                bot_id=bot_id,
                tenant_id=tenant_id,
                query_id=uuid4(),
                query_text="Test question for HITL",
                retrieval_confidence=Decimal("0.5"),
                source_consistency=None,
                generation_confidence=None,
                overall_confidence=Decimal("0.5"),
                threshold_used=Decimal("0.8"),
                routing_decision=RoutingDecision.hitl,
                is_verified_kb=False,
                hitl_resolved=False,
                metadata_json={"ai_draft": "This is a test draft", "citations": []},
            )
            
            session.add(log_entry)
            await session.flush()
            await session.commit()
            print(f"✓ Successfully created confidence log: {log_entry.id}")
            
            # Verify it's there
            result = await session.execute(text("SELECT COUNT(*) FROM confidence_logs"))
            count = result.scalar()
            print(f"Total confidence_logs now: {count}")
            
        except Exception as e:
            print(f"ERROR: {e}")
            import traceback
            traceback.print_exc()
            await session.rollback()

if __name__ == "__main__":
    asyncio.run(test_logging())
