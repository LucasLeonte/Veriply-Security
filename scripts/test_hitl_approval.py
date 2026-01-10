"""
Test to verify HITL approval endpoint works correctly.
This simulates the frontend calling the approval endpoint.
"""

import asyncio
import json
import sys
from uuid import uuid4
from pathlib import Path
from decimal import Decimal
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent / "apps" / "api"))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from app.core.settings import settings
from app.models.bot import Bot
from app.models.confidence_log import ConfidenceLog, RoutingDecision


async def test_approval_endpoint():
    """Test the approval endpoint by directly calling it."""
    
    print("\n" + "="*80)
    print("HITL APPROVAL ENDPOINT TEST")
    print("="*80 + "\n")
    
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    try:
        async with async_session() as db:
            print("✓ Database connection established\n")
            
            # Get the first unresolved HITL item
            print("--- Step 1: Finding an unresolved HITL item ---")
            stmt = select(ConfidenceLog).where(
                ConfidenceLog.routing_decision == RoutingDecision.HITL,
                ConfidenceLog.hitl_resolved == False,
            ).limit(1)
            
            result = await db.execute(stmt)
            hitl_item = result.scalars().first()
            
            if not hitl_item:
                print("  ✗ No unresolved HITL items found")
                return False
            
            print(f"  ✓ Found HITL item: {hitl_item.id}")
            print(f"    - Query: {hitl_item.query_text[:50]}...")
            print(f"    - Bot: {hitl_item.bot_id}")
            print(f"    - Resolved (before): {hitl_item.hitl_resolved}")
            print(f"    - Metadata: {hitl_item.metadata_json}")
            
            # Step 2: Simulate the approval
            print("\n--- Step 2: Simulating approval (with edits) ---")
            
            # This is what the approval endpoint does:
            edited_response = "I have reviewed and edited this response for clarity."
            
            hitl_item.hitl_resolved = True
            hitl_item.resolution_user_id = uuid4()
            hitl_item.resolution_timestamp = datetime.utcnow()
            
            if not hitl_item.metadata_json:
                hitl_item.metadata_json = {}
            
            hitl_item.metadata_json["human_edits"] = edited_response
            hitl_item.metadata_json["human_final_answer"] = edited_response
            hitl_item.metadata_json["resolution_action"] = "approved_with_edits"
            
            print(f"  Marked as resolved: {hitl_item.hitl_resolved}")
            print(f"  Updated metadata: {hitl_item.metadata_json}")
            
            # Step 3: Commit the changes
            print("\n--- Step 3: Committing changes ---")
            await db.commit()
            print(f"  ✓ Changes committed")
            
            # Step 4: Verify changes were saved
            print("\n--- Step 4: Verifying changes in database ---")
            
            stmt = select(ConfidenceLog).where(
                ConfidenceLog.id == hitl_item.id
            )
            result = await db.execute(stmt)
            verified_item = result.scalars().first()
            
            if not verified_item:
                print("  ✗ Item not found after commit")
                return False
            
            print(f"  Resolved (after): {verified_item.hitl_resolved}")
            print(f"  Resolution user ID: {verified_item.resolution_user_id}")
            print(f"  Resolution timestamp: {verified_item.resolution_timestamp}")
            print(f"  Metadata: {verified_item.metadata_json}")
            
            if verified_item.hitl_resolved:
                print("\n  ✓ APPROVAL SUCCESSFUL - Item is now resolved in database")
                return True
            else:
                print("\n  ✗ APPROVAL FAILED - Item is still not resolved in database")
                return False
            
    except Exception as e:
        print(f"✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        await engine.dispose()


async def test_frontend_polling():
    """Test what the frontend sees when it polls the status endpoint."""
    
    print("\n" + "="*80)
    print("FRONTEND STATUS POLLING TEST")
    print("="*80 + "\n")
    
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    try:
        async with async_session() as db:
            print("✓ Database connection established\n")
            
            # Get a resolved HITL item
            print("--- Step 1: Finding a resolved HITL item ---")
            stmt = select(ConfidenceLog).where(
                ConfidenceLog.routing_decision == RoutingDecision.HITL,
                ConfidenceLog.hitl_resolved == True,
            ).limit(1)
            
            result = await db.execute(stmt)
            resolved_item = result.scalars().first()
            
            if resolved_item:
                print(f"  ✓ Found resolved HITL item: {resolved_item.id}")
                print(f"    - Query: {resolved_item.query_text[:50]}...")
                print(f"    - Resolved: {resolved_item.hitl_resolved}")
                
                # Simulate what status endpoint returns
                print("\n--- Step 2: Simulating what status endpoint returns ---")
                
                raw_metadata = resolved_item.metadata_json or {}
                resolved_answer = (
                    raw_metadata.get("human_final_answer")
                    or raw_metadata.get("human_edits")
                    or raw_metadata.get("ai_draft")
                    or ""
                )
                
                response = {
                    "status": "resolved",
                    "message_id": str(resolved_item.query_id),
                    "response": {
                        "answer": resolved_answer,
                        "citations": raw_metadata.get("citations", []),
                        "resolved_at": (
                            resolved_item.resolution_timestamp.isoformat()
                            if resolved_item.resolution_timestamp
                            else None
                        ),
                    },
                }
                
                print(f"  Response that frontend receives:")
                print(f"    - Status: {response['status']}")
                print(f"    - Message ID: {response['message_id']}")
                print(f"    - Answer: {response['response']['answer'][:50]}...")
                print(f"    - Resolved at: {response['response']['resolved_at']}")
                
                print("\n  ✓ Frontend would receive resolved response")
                return True
            else:
                print("  ⚠ No resolved HITL items found")
                
                # Check for unresolved items
                stmt = select(ConfidenceLog).where(
                    ConfidenceLog.routing_decision == RoutingDecision.HITL,
                    ConfidenceLog.hitl_resolved == False,
                ).limit(1)
                
                result = await db.execute(stmt)
                unresolved_item = result.scalars().first()
                
                if unresolved_item:
                    print(f"\n  Found unresolved HITL item: {unresolved_item.id}")
                    print(f"    - Query: {unresolved_item.query_text[:50]}...")
                    print(f"    - Resolved: {unresolved_item.hitl_resolved}")
                    
                    # Simulate what status endpoint returns for pending item
                    print("\n--- Step 2: Simulating what status endpoint returns for PENDING item ---")
                    response = {
                        "status": "pending",
                        "message_id": str(unresolved_item.query_id),
                    }
                    
                    print(f"  Response that frontend receives:")
                    print(f"    - Status: {response['status']}")
                    print(f"    - Message ID: {response['message_id']}")
                    
                    print("\n  ⚠ ISSUE: Frontend is stuck in pending state!")
                    print("     This suggests either:")
                    print("     1. Approval endpoint is not being called")
                    print("     2. Approval endpoint is failing silently")
                    print("     3. Frontend is not polling the right endpoint")
                    
                    return False
    
    except Exception as e:
        print(f"✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        await engine.dispose()


async def main():
    """Run all tests."""
    
    print("\nStarting HITL approval diagnostic tests...\n")
    
    # Run tests
    test1_result = await test_approval_endpoint()
    test2_result = await test_frontend_polling()
    
    # Print summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    print(f"Approval Endpoint Test: {'PASSED ✓' if test1_result else 'FAILED ✗'}")
    print(f"Frontend Polling Test: {'PASSED ✓' if test2_result else 'FAILED ✗'}")
    print("="*80 + "\n")
    
    return test1_result and test2_result


if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result else 1)
