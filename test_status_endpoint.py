#!/usr/bin/env python3
"""
Test to simulate what the frontend does:
1. Get a message_id from HITL response
2. Poll the status endpoint
3. See what it returns
"""

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from uuid import UUID
import sys
from pathlib import Path
import json

sys.path.insert(0, str(Path('.') / 'apps' / 'api'))

from app.core.settings import settings
from app.models.confidence_log import ConfidenceLog, RoutingDecision


async def simulate_frontend_polling():
    """Simulate what frontend does when polling for status."""
    
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as db:
        print("\n" + "="*80)
        print("FRONTEND STATUS POLLING SIMULATION")
        print("="*80 + "\n")
        
        # Get a pending HITL item
        stmt = select(ConfidenceLog).where(
            ConfidenceLog.routing_decision == RoutingDecision.HITL,
            ConfidenceLog.hitl_resolved == False,
        ).limit(1)
        
        result = await db.execute(stmt)
        item = result.scalars().first()
        
        if not item:
            print("❌ No pending HITL items found")
            return False
        
        bot_id = item.bot_id
        query_id = item.query_id
        
        print(f"📍 SIMULATING FRONTEND BEHAVIOR")
        print(f"   Bot ID: {bot_id}")
        print(f"   Message ID (query_id): {query_id}")
        print(f"   Item ID: {item.id}\n")
        
        # Step 1: User submits query, gets message_id back
        print(f"STEP 1: User submits query")
        print(f"  → Frontend receives metadata with message_id: {query_id}")
        print(f"  → Starts polling: /bots/{bot_id}/chat/{query_id}/status\n")
        
        # Step 2: Frontend makes the status check (simulate it)
        print(f"STEP 2: Frontend polls status endpoint")
        print(f"  Looking for: ConfidenceLog WHERE")
        print(f"    bot_id = {bot_id}")
        print(f"    query_id = {query_id}")
        
        # This is what the endpoint does
        stmt_status = select(ConfidenceLog).where(
            ConfidenceLog.bot_id == bot_id,
            ConfidenceLog.query_id == query_id,
        )
        
        result_status = await db.execute(stmt_status)
        found_item = result_status.scalars().first()
        
        if not found_item:
            print(f"\n  ❌ ERROR: Item not found by status endpoint!")
            print(f"     This explains why frontend is stuck!")
            print(f"\n  Checking what SHOULD match:")
            
            # Debug: check all fields
            print(f"    Actual bot_id in DB: {item.bot_id}")
            print(f"    Actual query_id in DB: {item.query_id}")
            print(f"    Item ID: {item.id}")
            
            return False
        
        print(f"  ✓ Found item in database")
        
        # Step 3: Check the response
        print(f"\nSTEP 3: Check endpoint response")
        if found_item.hitl_resolved:
            print(f"  Item is RESOLVED ✓")
            raw_metadata = found_item.metadata_json or {}
            resolved_answer = (
                raw_metadata.get("human_final_answer")
                or raw_metadata.get("human_edits")
                or raw_metadata.get("ai_draft")
                or ""
            )
            response = {
                "status": "resolved",
                "message_id": str(found_item.query_id),
                "response": {
                    "answer": resolved_answer[:50] + "...",
                    "citations": raw_metadata.get("citations", []),
                    "resolved_at": (
                        found_item.resolution_timestamp.isoformat()
                        if found_item.resolution_timestamp
                        else None
                    ),
                },
            }
            print(f"  Response: {json.dumps(response, indent=2)}")
        else:
            print(f"  Item is PENDING ⏳")
            response = {
                "status": "pending",
                "message_id": str(found_item.query_id),
            }
            print(f"  Response: {json.dumps(response, indent=2)}")
            print(f"\n  → Frontend will call this endpoint again in 5 seconds")
            print(f"  → Until hitl_resolved becomes True")
        
        print(f"\n" + "="*80 + "\n")
        return True
    
    await engine.dispose()


if __name__ == "__main__":
    result = asyncio.run(simulate_frontend_polling())
    sys.exit(0 if result else 1)
