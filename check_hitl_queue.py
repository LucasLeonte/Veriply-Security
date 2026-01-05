"""Check HITL queue items in the database."""
import asyncio
import sys
from pathlib import Path

# Add the apps/api directory to path
api_dir = Path(__file__).parent / "apps" / "api"
sys.path.insert(0, str(api_dir))

from sqlalchemy import select, and_
from sqlalchemy.orm import joinedload
from app.core.database import async_session_maker
from app.models.confidence_log import ConfidenceLog, RoutingDecision


async def check_hitl_queue():
    """Check what HITL items exist in the database."""
    async with async_session_maker() as session:
        # Query all confidence logs
        all_logs = await session.execute(select(ConfidenceLog))
        all_logs = all_logs.scalars().all()
        
        print(f"\n📊 Total confidence logs in database: {len(all_logs)}")
        
        # Query HITL items (unresolved)
        hitl_query = select(ConfidenceLog).where(
            and_(
                ConfidenceLog.routing_decision == RoutingDecision.HITL,
                ConfidenceLog.hitl_resolved.is_(False),
            )
        ).options(joinedload(ConfidenceLog.bot))
        
        result = await session.execute(hitl_query)
        hitl_items = result.unique().scalars().all()
        
        print(f"🔍 Total HITL items (unresolved): {len(hitl_items)}")
        
        if hitl_items:
            print("\n📋 HITL Items Details:")
            for i, item in enumerate(hitl_items, 1):
                print(f"\n  {i}. ID: {item.id}")
                print(f"     Tenant ID: {item.tenant_id}")
                print(f"     Bot ID: {item.bot_id}")
                print(f"     Bot Name: {item.bot.name if item.bot else 'N/A'}")
                print(f"     Question: {item.question[:100]}...")
                print(f"     Confidence: {item.overall_confidence}")
                print(f"     Routing: {item.routing_decision}")
                print(f"     Resolved: {item.hitl_resolved}")
                print(f"     Created: {item.created_at}")
        else:
            print("\n⚠️  No HITL items found in the database!")
            print("\nPossible reasons:")
            print("  1. No questions have been asked with low confidence")
            print("  2. All HITL items have been resolved")
            print("  3. Routing decision is not being set correctly")
        
        # Check if there are any confidence logs at all
        if all_logs:
            print(f"\n📈 Routing Decision Breakdown:")
            routing_counts = {}
            for log in all_logs:
                decision = log.routing_decision.value if log.routing_decision else "None"
                routing_counts[decision] = routing_counts.get(decision, 0) + 1
            
            for decision, count in routing_counts.items():
                print(f"  - {decision}: {count}")
            
            # Check resolved status
            resolved_count = sum(1 for log in all_logs if log.hitl_resolved)
            print(f"\n📝 Resolution Status:")
            print(f"  - Resolved: {resolved_count}")
            print(f"  - Unresolved: {len(all_logs) - resolved_count}")


if __name__ == "__main__":
    asyncio.run(check_hitl_queue())
