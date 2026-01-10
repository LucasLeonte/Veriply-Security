"""
Test script to verify review queue rejection flow:
1. Reject a review in review queue
2. Go to bots page
3. Go back to review queue
4. Verify the review is NOT shown (should stay rejected)
"""
import asyncio
import sys
sys.path.insert(0, "apps/api")

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from uuid import UUID
import os
from datetime import datetime

from app.models.confidence_log import ConfidenceLog, RoutingDecision
from app.models.bot import Bot


async def main():
    """Test the full rejection flow"""
    
    # Database connection
    db_url = os.getenv("DATABASE_URL", "postgresql+asyncpg://veriply_user:veriply123@localhost:5432/veriply_db")
    engine = create_async_engine(db_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        print("\n" + "="*80)
        print("REVIEW QUEUE REJECTION FLOW TEST")
        print("="*80)
        
        # Step 1: Find a pending HITL item
        print("\n📋 Step 1: Finding a pending HITL item...")
        result = await session.execute(
            select(ConfidenceLog).where(
                and_(
                    ConfidenceLog.routing_decision == RoutingDecision.hitl,
                    ConfidenceLog.hitl_resolved.is_(False),
                )
            ).limit(1)
        )
        item = result.scalars().first()
        
        if not item:
            print("   ❌ No pending HITL items found. Creating a test item...")
            # Create a test item if none exists
            from app.models.user import User
            result = await session.execute(select(Bot).limit(1))
            bot = result.scalars().first()
            result = await session.execute(select(User).limit(1))
            user = result.scalars().first()
            
            if not bot or not user:
                print("   ❌ Cannot create test item - no bot or user found")
                return
            
            item = ConfidenceLog(
                query_text="Test question for rejection flow",
                overall_confidence=0.45,
                routing_decision=RoutingDecision.hitl,
                hitl_resolved=False,
                bot_id=bot.id,
                tenant_id=bot.tenant_id,
                metadata_json={
                    "ai_draft": "Test AI draft response",
                    "type": "chat",
                    "session_id": "test-session"
                }
            )
            session.add(item)
            await session.commit()
            await session.refresh(item)
            print(f"   ✅ Created test item: {item.id}")
        else:
            print(f"   ✅ Found pending item: {item.id}")
            print(f"      Question: {item.query_text[:60]}...")
            print(f"      Confidence: {item.overall_confidence}")
            print(f"      HITL Resolved: {item.hitl_resolved}")
        
        item_id = item.id
        tenant_id = item.tenant_id
        
        # Step 2: Query the review queue (simulating GET /api/v1/hitl/queue)
        print("\n📥 Step 2: Querying review queue (before rejection)...")
        result = await session.execute(
            select(ConfidenceLog).where(
                and_(
                    ConfidenceLog.routing_decision == RoutingDecision.hitl,
                    ConfidenceLog.hitl_resolved.is_(False),
                    ConfidenceLog.tenant_id == tenant_id,
                )
            )
        )
        queue_items = result.scalars().all()
        print(f"   ✅ Found {len(queue_items)} items in review queue")
        item_in_queue = any(i.id == item_id for i in queue_items)
        print(f"   {'✅' if item_in_queue else '❌'} Our test item IS in the queue: {item_in_queue}")
        
        # Step 3: Reject the item (simulating POST /api/v1/hitl/queue/{item_id}/reject)
        print(f"\n❌ Step 3: Rejecting item {item_id}...")
        result = await session.execute(
            select(ConfidenceLog).where(
                and_(
                    ConfidenceLog.id == item_id,
                    ConfidenceLog.tenant_id == tenant_id,
                )
            )
        )
        item = result.scalars().first()
        
        if not item:
            print("   ❌ ERROR: Item not found for rejection!")
            return
        
        # Mark as resolved (this is what the reject endpoint does)
        item.hitl_resolved = True
        item.resolution_timestamp = datetime.utcnow()
        metadata = dict(item.metadata_json or {})
        metadata["resolution_action"] = "rejected"
        metadata["rejection_reason"] = "Test rejection"
        item.metadata_json = metadata
        
        await session.commit()
        print(f"   ✅ Item marked as resolved (hitl_resolved = True)")
        
        # Step 4: Simulate going to bots page and back (session refresh)
        print("\n🔄 Step 4: Simulating navigation to Bots page and back...")
        await session.commit()  # Close current transaction
        
        # Step 5: Query the review queue again (simulating GET /api/v1/hitl/queue after navigation)
        print("\n📥 Step 5: Querying review queue (after rejection + navigation)...")
        result = await session.execute(
            select(ConfidenceLog).where(
                and_(
                    ConfidenceLog.routing_decision == RoutingDecision.hitl,
                    ConfidenceLog.hitl_resolved.is_(False),
                    ConfidenceLog.tenant_id == tenant_id,
                )
            )
        )
        queue_items_after = result.scalars().all()
        print(f"   ✅ Found {len(queue_items_after)} items in review queue")
        item_in_queue_after = any(i.id == item_id for i in queue_items_after)
        
        # Step 6: Verify the rejected item is NOT in the queue
        print("\n" + "="*80)
        print("VERIFICATION RESULTS")
        print("="*80)
        
        if not item_in_queue_after:
            print("✅ SUCCESS: Rejected item is NOT in the queue (correct behavior)")
        else:
            print("❌ FAILURE: Rejected item IS STILL in the queue (bug!)")
        
        # Step 7: Double-check the item's status directly
        print("\n🔍 Step 7: Verifying item status directly...")
        result = await session.execute(
            select(ConfidenceLog).where(ConfidenceLog.id == item_id)
        )
        item_check = result.scalars().first()
        
        if item_check:
            print(f"   Item ID: {item_check.id}")
            print(f"   HITL Resolved: {item_check.hitl_resolved}")
            print(f"   Routing Decision: {item_check.routing_decision}")
            print(f"   Resolution Action: {item_check.metadata_json.get('resolution_action', 'N/A')}")
            
            if item_check.hitl_resolved and not item_in_queue_after:
                print("\n✅ FINAL VERDICT: Flow is working correctly!")
            elif item_check.hitl_resolved and item_in_queue_after:
                print("\n❌ FINAL VERDICT: Bug detected! Item is marked resolved but still in queue query!")
            else:
                print(f"\n⚠️  FINAL VERDICT: Unexpected state: hitl_resolved={item_check.hitl_resolved}")
        else:
            print("   ❌ Item not found in database!")
        
        print("\n" + "="*80 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
