"""Quick check of HITL queue items."""
import asyncio
from sqlalchemy import select, and_
from sqlalchemy.orm import joinedload

from app.core.database import async_session_maker
from app.models.confidence_log import ConfidenceLog, RoutingDecision


async def main():
    """Check HITL queue items."""
    async with async_session_maker() as session:
        # Get all confidence logs
        all_result = await session.execute(select(ConfidenceLog))
        all_logs = all_result.scalars().all()
        print(f"\n📊 Total confidence logs: {len(all_logs)}")
        
        # Get HITL items
        hitl_query = select(ConfidenceLog).where(
            and_(
                ConfidenceLog.routing_decision == RoutingDecision.HITL,
                ConfidenceLog.hitl_resolved.is_(False),
            )
        ).options(joinedload(ConfidenceLog.bot))
        
        hitl_result = await session.execute(hitl_query)
        hitl_items = hitl_result.unique().scalars().all()
        
        print(f"🔍 HITL items (unresolved): {len(hitl_items)}")
        
        if hitl_items:
            print("\n📋 HITL Items:")
            for item in hitl_items:
                bot_name = item.bot.name if item.bot else "N/A"
                print(f"  - ID: {item.id}")
                print(f"    Tenant: {item.tenant_id}")
                print(f"    Bot: {bot_name}")
                print(f"    Question: {item.question[:80]}...")
                print(f"    Confidence: {item.overall_confidence}")
                print()
        
        # Show routing breakdown
        if all_logs:
            print("📈 Routing Decisions:")
            from collections import Counter
            decisions = Counter(log.routing_decision.value if log.routing_decision else "None" for log in all_logs)
            for decision, count in decisions.items():
                print(f"  - {decision}: {count}")


if __name__ == "__main__":
    asyncio.run(main())
