#!/usr/bin/env python3
"""Test the review queue GET endpoint to verify it filters resolved items correctly."""

import asyncio
import sys
import json
from uuid import UUID

sys.path.insert(0, 'apps/api')

from app.core.database import AsyncSessionLocal, set_tenant_context
from app.models.confidence_log import ConfidenceLog, RoutingDecision
from sqlalchemy import select, and_


async def test_queue_filtering():
    """Test that GET endpoint would correctly filter resolved items."""
    async with AsyncSessionLocal() as db:
        # Get a tenant with some items
        result = await db.execute(
            select(ConfidenceLog).where(
                ConfidenceLog.routing_decision == RoutingDecision.hitl
            ).order_by(ConfidenceLog.created_at.desc()).limit(1)
        )
        sample_item = result.scalars().first()
        
        if not sample_item:
            print("No HITL items found")
            return
        
        tenant_id = sample_item.tenant_id
        print(f"Using tenant: {tenant_id}\n")
        
        # Set RLS context like the endpoint does
        await set_tenant_context(db, tenant_id)
        
        # Run the same query as the endpoint
        query_stmt = select(ConfidenceLog).where(
            and_(
                ConfidenceLog.routing_decision == RoutingDecision.hitl,
                ConfidenceLog.hitl_resolved.is_(False),
                ConfidenceLog.tenant_id == tenant_id,
            )
        ).order_by(ConfidenceLog.created_at.asc()).limit(20)
        
        result = await db.execute(query_stmt)
        pending_items = result.scalars().all()
        
        print("="*80)
        print("PENDING ITEMS (hitl_resolved=False) - This is what should show in queue")
        print("="*80 + "\n")
        
        if not pending_items:
            print("NO PENDING ITEMS FOUND!")
            print("\nThis is the problem - queue is empty even though there should be pending items")
            
            # Let's check what ALL items exist
            print("\n" + "="*80)
            print("Checking ALL HITL items for this tenant:")
            print("="*80 + "\n")
            
            all_result = await db.execute(
                select(ConfidenceLog).where(
                    and_(
                        ConfidenceLog.routing_decision == RoutingDecision.hitl,
                        ConfidenceLog.tenant_id == tenant_id,
                    )
                ).order_by(ConfidenceLog.created_at.desc()).limit(10)
            )
            all_items = all_result.scalars().all()
            
            for item in all_items:
                status = "RESOLVED" if item.hitl_resolved else "PENDING"
                print(f"{status} - {item.query_text[:50] if item.query_text else 'N/A'}")
        else:
            print(f"FOUND {len(pending_items)} pending items:\n")
            for item in pending_items:
                print(f"PENDING")
                print(f"  ID: {item.id}")
                print(f"  Query: {(item.query_text or 'N/A')[:60]}...")
                print(f"  hitl_resolved: {item.hitl_resolved}")
                print()


if __name__ == "__main__":
    asyncio.run(test_queue_filtering())
