#!/usr/bin/env python3
"""
Quick verification test for HITL flow.
Run this after the API has been restarted to verify the enhanced logging is working.
"""

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "apps" / "api"))

from app.core.settings import settings
from app.models.confidence_log import ConfidenceLog, RoutingDecision


async def verify_hitl_state():
    """Quick verification of HITL queue state."""
    
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as db:
        print("\n" + "="*80)
        print("HITL QUEUE STATE VERIFICATION")
        print("="*80 + "\n")
        
        # Count unresolved items
        stmt_unresolved = select(ConfidenceLog).where(
            ConfidenceLog.routing_decision == RoutingDecision.HITL,
            ConfidenceLog.hitl_resolved == False,
        )
        result_unresolved = await db.execute(stmt_unresolved)
        unresolved_items = result_unresolved.scalars().all()
        
        # Count resolved items
        stmt_resolved = select(ConfidenceLog).where(
            ConfidenceLog.routing_decision == RoutingDecision.HITL,
            ConfidenceLog.hitl_resolved == True,
        )
        result_resolved = await db.execute(stmt_resolved)
        resolved_items = result_resolved.scalars().all()
        
        print(f"📊 HITL Queue Summary:")
        print(f"  Unresolved items: {len(unresolved_items)}")
        print(f"  Resolved items:   {len(resolved_items)}")
        
        if unresolved_items:
            print(f"\n🔵 Unresolved items waiting for review:")
            for item in unresolved_items[:5]:
                print(f"  - ID: {str(item.id)[:8]}...")
                print(f"    Query: {item.query_text[:40]}..." if item.query_text else "    Query: N/A")
                print(f"    Confidence: {float(item.overall_confidence):.1%}")
        
        if resolved_items:
            print(f"\n✅ Resolved items:")
            for item in resolved_items[:5]:
                action = item.metadata_json.get("resolution_action", "unknown") if item.metadata_json else "unknown"
                print(f"  - ID: {str(item.id)[:8]}...")
                print(f"    Query: {item.query_text[:40]}..." if item.query_text else "    Query: N/A")
                print(f"    Action: {action}")
                print(f"    Resolved by: {item.resolution_user_id if item.resolution_user_id else 'N/A'}")
        
        print("\n" + "="*80)
        
        return len(unresolved_items), len(resolved_items)
    
    await engine.dispose()


if __name__ == "__main__":
    unresolved, resolved = asyncio.run(verify_hitl_state())
    print("\n✓ Verification complete")
    
    # Exit code: 0 if items in queue, 1 if queue is empty
    sys.exit(0 if (unresolved + resolved) > 0 else 1)
