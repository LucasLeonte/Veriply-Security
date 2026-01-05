#!/usr/bin/env python3
"""
Detailed trace of a single HITL item through the entire processing flow.
This shows exactly what happens at each step.
"""

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, text
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent / "apps" / "api"))

from app.core.settings import settings
from app.models.confidence_log import ConfidenceLog, RoutingDecision


async def trace_single_hitl_item():
    """Trace a single HITL item through the system."""
    
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as db:
        print("\n" + "="*80)
        print("HITL ITEM PROCESSING TRACE")
        print("="*80 + "\n")
        
        # Get an unresolved item
        stmt = select(ConfidenceLog).where(
            ConfidenceLog.routing_decision == RoutingDecision.HITL,
            ConfidenceLog.hitl_resolved == False,
        ).limit(1)
        
        result = await db.execute(stmt)
        item = result.scalars().first()
        
        if not item:
            print("❌ No unresolved HITL items found to trace")
            return False
        
        print(f"📍 SELECTED ITEM TO TRACE: {item.id}\n")
        
        # Step 1: Item Created
        print("STEP 1: Item Created")
        print(f"  ├─ ID: {item.id}")
        print(f"  ├─ Created at: {item.created_at}")
        print(f"  ├─ Time in queue: {(datetime.utcnow() - item.created_at.replace(tzinfo=None)).total_seconds() / 3600:.1f} hours ago")
        print()
        
        # Step 2: Query Processing
        print("STEP 2: Query Processing")
        print(f"  ├─ Query text: {item.query_text[:60]}..." if item.query_text else "  ├─ Query text: N/A")
        print(f"  ├─ Bot ID: {item.bot_id}")
        print(f"  ├─ Tenant ID: {item.tenant_id}")
        print(f"  ├─ Query ID: {item.query_id}")
        print()
        
        # Step 3: Confidence Calculation
        print("STEP 3: Confidence Calculation")
        print(f"  ├─ Retrieval confidence: {float(item.retrieval_confidence):.2%}" if item.retrieval_confidence else "  ├─ Retrieval confidence: N/A")
        print(f"  ├─ Overall confidence: {float(item.overall_confidence):.2%}")
        print(f"  ├─ Threshold used: {float(item.threshold_used):.2%}")
        print(f"  └─ Confidence < Threshold? {float(item.overall_confidence) < float(item.threshold_used)} ✓")
        print()
        
        # Step 4: Routing Decision
        print("STEP 4: Routing Decision")
        print(f"  ├─ Decision: {item.routing_decision.value.upper()}")
        print(f"  ├─ Reason: {float(item.overall_confidence):.2%} < {float(item.threshold_used):.2%}")
        print(f"  └─ Status: Routed to human review ✓")
        print()
        
        # Step 5: Queue Status
        print("STEP 5: Current Queue Status")
        print(f"  ├─ HITL Resolved? {item.hitl_resolved}")
        if item.hitl_resolved:
            print(f"  ├─ Resolved by user: {item.resolution_user_id}")
            print(f"  ├─ Resolution timestamp: {item.resolution_timestamp}")
            print(f"  └─ Status: RESOLVED ✓")
        else:
            print(f"  ├─ Awaiting human review...")
            print(f"  └─ Status: PENDING ⏳")
        print()
        
        # Step 6: Metadata
        print("STEP 6: Stored Metadata")
        if item.metadata_json:
            metadata = item.metadata_json
            print(f"  ├─ AI Draft: {metadata.get('ai_draft', 'N/A')[:50]}..." if metadata.get('ai_draft') else "  ├─ AI Draft: N/A")
            print(f"  ├─ Citations: {len(metadata.get('citations', []))} sources")
            print(f"  ├─ Resolution action: {metadata.get('resolution_action', 'N/A')}")
            print(f"  ├─ Human final answer: {metadata.get('human_final_answer', 'N/A')[:50]}..." if metadata.get('human_final_answer') else "  ├─ Human final answer: N/A")
            print(f"  └─ Rejection reason: {metadata.get('rejection_reason', 'N/A')}")
        else:
            print(f"  └─ No metadata stored")
        print()
        
        # Step 7: Frontend Experience
        print("STEP 7: What Frontend Sees")
        if item.hitl_resolved:
            print(f"  ├─ Status response: {{ 'status': 'resolved', ... }}")
            answer = (
                item.metadata_json.get("human_final_answer")
                if item.metadata_json
                else item.metadata_json.get("ai_draft") if item.metadata_json else ""
            )
            print(f"  ├─ Final answer: {answer[:50]}..." if answer else "  ├─ Final answer: N/A")
            print(f"  └─ User sees: RESOLVED RESPONSE ✓")
        else:
            print(f"  ├─ Status response: {{ 'status': 'pending', 'message_id': '{item.query_id}' }}")
            print(f"  ├─ Frontend message: 'Waiting for team...'")
            print(f"  └─ User sees: PENDING STATE ⏳")
        print()
        
        # Step 8: Next Action
        print("STEP 8: Next Action")
        if item.hitl_resolved:
            print(f"  └─ ✓ Item resolved - awaiting user to refresh")
        else:
            print(f"  ├─ Waiting for human reviewer to:")
            print(f"  │  ├─ Click 'Approve' or 'Reject'")
            print(f"  │  ├─ Optionally provide edits")
            print(f"  │  └─ Submit the approval/rejection")
            print(f"  └─ Then system will:")
            print(f"     ├─ Mark hitl_resolved = True")
            print(f"     ├─ Store resolution metadata")
            print(f"     ├─ Frontend polls and gets resolved status")
            print(f"     └─ User sees final answer")
        
        print("\n" + "="*80)
        return True
    
    await engine.dispose()


async def show_queue_summary():
    """Show overall queue health."""
    
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as db:
        print("\n📊 OVERALL HITL QUEUE HEALTH\n")
        
        # Count by status
        stmt_unresolved = select(ConfidenceLog).where(
            ConfidenceLog.routing_decision == RoutingDecision.HITL,
            ConfidenceLog.hitl_resolved == False,
        )
        result_unresolved = await db.execute(stmt_unresolved)
        unresolved = result_unresolved.scalars().all()
        
        stmt_resolved = select(ConfidenceLog).where(
            ConfidenceLog.routing_decision == RoutingDecision.HITL,
            ConfidenceLog.hitl_resolved == True,
        )
        result_resolved = await db.execute(stmt_resolved)
        resolved = result_resolved.scalars().all()
        
        total = len(unresolved) + len(resolved)
        resolution_rate = (len(resolved) / total * 100) if total > 0 else 0
        
        print(f"  Total HITL items: {total}")
        print(f"  Unresolved (pending): {len(unresolved)}")
        print(f"  Resolved (approved/rejected): {len(resolved)}")
        print(f"  Resolution rate: {resolution_rate:.1f}%")
        print()
        
        if len(unresolved) > 0:
            print(f"  ⏳ Items waiting for review:")
            for item in sorted(unresolved, key=lambda x: x.overall_confidence)[:3]:
                print(f"     - Confidence {float(item.overall_confidence):.1%}: {item.query_text[:40] if item.query_text else 'N/A'}...")
        
        print("\n" + "="*80 + "\n")
    
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(show_queue_summary())
    result = asyncio.run(trace_single_hitl_item())
    
    if result:
        print("✓ Trace complete\n")
        sys.exit(0)
    else:
        print("✗ Trace failed\n")
        sys.exit(1)
