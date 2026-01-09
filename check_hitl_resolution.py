#!/usr/bin/env python3
"""Check HITL items to verify resolution flags are being set correctly."""

import asyncio
import sys
from uuid import UUID
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

# Add apps/api to path
sys.path.insert(0, 'apps/api')

from app.core.database import AsyncSessionLocal
from app.models.confidence_log import ConfidenceLog, RoutingDecision


async def check_hitl_items():
    """Check HITL items in database to verify resolution flags."""
    async with AsyncSessionLocal() as db:
        # Get all HITL items
        result = await db.execute(
            select(ConfidenceLog)
            .where(ConfidenceLog.routing_decision == RoutingDecision.hitl)
            .order_by(ConfidenceLog.created_at.desc())
            .limit(20)
        )
        items = result.scalars().all()
        
        print(f"\n{'='*80}")
        print(f"HITL ITEMS CHECK - Last 20 items")
        print(f"{'='*80}\n")
        
        if not items:
            print("❌ No HITL items found in database")
            return
        
        unresolved_count = 0
        resolved_count = 0
        
        for item in items:
            status = "✅ RESOLVED" if item.hitl_resolved else "⏳ PENDING"
            if item.hitl_resolved:
                resolved_count += 1
            else:
                unresolved_count += 1
            
            metadata = item.metadata_json or {}
            resolution_action = metadata.get('resolution_action', 'NONE')
            
            print(f"{status}")
            print(f"  ID: {item.id}")
            print(f"  Query: {(item.query_text or 'N/A')[:60]}...")
            print(f"  hitl_resolved: {item.hitl_resolved}")
            print(f"  resolution_action: {resolution_action}")
            print(f"  resolution_user_id: {item.resolution_user_id}")
            print(f"  resolution_timestamp: {item.resolution_timestamp}")
            print(f"  Created: {item.created_at}")
            print(f"  Tenant: {item.tenant_id}")
            print()
        
        print(f"{'='*80}")
        print(f"Summary: {unresolved_count} pending, {resolved_count} resolved (total {len(items)})")
        print(f"{'='*80}\n")
        
        # Check if there are items with resolution_action but hitl_resolved=False
        print("Checking for inconsistent states...")
        inconsistent = []
        for item in items:
            metadata = item.metadata_json or {}
            has_resolution = metadata.get('resolution_action') in ['approved', 'rejected', 'approved_with_edits']
            if has_resolution and not item.hitl_resolved:
                inconsistent.append(item)
        
        if inconsistent:
            print(f"\n⚠️  Found {len(inconsistent)} items with resolution_action but hitl_resolved=False:")
            for item in inconsistent:
                metadata = item.metadata_json or {}
                print(f"  - {item.id}: resolution_action={metadata.get('resolution_action')}, hitl_resolved={item.hitl_resolved}")
        else:
            print("✅ No inconsistent states found")


if __name__ == "__main__":
    asyncio.run(check_hitl_items())
