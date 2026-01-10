"""
Test to verify HITL input is received and processed by the bot.
This test simulates the complete HITL flow:
1. Chat query triggers HITL routing (low confidence)
2. Frontend polls status endpoint
3. HITL reviewer approves/rejects item
4. Status endpoint returns resolved answer
"""

import asyncio
import json
import logging
from uuid import UUID, uuid4
from decimal import Decimal
import sys
from pathlib import Path

# Add apps/api to path
sys.path.insert(0, str(Path(__file__).parent / "apps" / "api"))

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import required modules
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from app.core.settings import settings
from app.models.bot import Bot
from app.models.user import User
from app.models.confidence_log import ConfidenceLog, RoutingDecision
from app.core.database import Base
from app.services.confidence_service import ConfidenceCalculatorService
from app.services.vector_search_service import SearchResult


async def test_hitl_flow():
    """Test the complete HITL flow."""
    
    print("\n" + "="*80)
    print("HITL FLOW DIAGNOSTIC TEST")
    print("="*80 + "\n")
    
    # Create async engine
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    try:
        async with async_session() as db:
            print("✓ Database connection established")
            
            # Step 1: Create a test bot
            print("\n--- Step 1: Creating test bot ---")
            bot_id = uuid4()
            tenant_id = uuid4()
            user_id = uuid4()
            
            # Check if test bot exists
            existing_bot = await db.get(Bot, bot_id)
            if existing_bot:
                print(f"  Using existing bot: {bot_id}")
            else:
                print(f"  Creating new bot: {bot_id}")
                bot = Bot(
                    id=bot_id,
                    tenant_id=tenant_id,
                    name="TestBot",
                    description="Test bot for HITL flow",
                    status="active",
                    confidence_threshold=80,  # 80% threshold
                )
                db.add(bot)
                await db.commit()
                print(f"  ✓ Bot created with 80% confidence threshold")
            
            # Step 2: Test confidence calculation with low confidence (should route to HITL)
            print("\n--- Step 2: Testing confidence calculation (low confidence) ---")
            
            confidence_service = ConfidenceCalculatorService()
            
            # Create mock search results with low similarity (will result in low confidence)
            mock_results = [
                SearchResult(
                    document_id=uuid4(),
                    chunk_id=1,
                    document_name="test_doc.pdf",
                    text="Some test content",
                    similarity=0.45,  # Low similarity
                    page_number=1,
                    section="Introduction",
                    position=0,
                    is_verified=False,
                )
            ]
            
            query_text = "What is the meaning of life?"
            
            # Calculate confidence with low similarity
            result = await confidence_service.calculate_confidence(
                db=db,
                bot_id=bot_id,
                tenant_id=tenant_id,
                query=query_text,
                search_results=mock_results,
                confidence_threshold=80,  # 80% threshold
                is_verified_kb=False,
                metadata_json={
                    "ai_draft": "The meaning of life is 42.",
                    "citations": [{"source": "test_doc.pdf", "similarity": 0.45}],
                }
            )
            
            print(f"  Confidence score: {result.overall_score:.2%}")
            print(f"  Threshold: 80%")
            print(f"  Routing decision: {result.routing_decision.value}")
            print(f"  Query ID: {result.query_id}")
            
            if result.routing_decision == RoutingDecision.HITL:
                print("  ✓ HITL routing triggered (confidence < threshold)")
            else:
                print("  ✗ ERROR: Expected HITL routing but got AUTO_SEND")
                return False
            
            # Step 3: Verify HITL entry was created in database
            print("\n--- Step 3: Verifying HITL entry in database ---")
            
            stmt = select(ConfidenceLog).where(
                ConfidenceLog.query_id == result.query_id
            )
            db_result = await db.execute(stmt)
            hitl_entry = db_result.scalars().first()
            
            if hitl_entry:
                print(f"  ✓ HITL entry found in database")
                print(f"    - ID: {hitl_entry.id}")
                print(f"    - Query: {hitl_entry.query_text}")
                print(f"    - Routing: {hitl_entry.routing_decision.value}")
                print(f"    - Resolved: {hitl_entry.hitl_resolved}")
                print(f"    - Confidence: {hitl_entry.overall_confidence}")
            else:
                print(f"  ✗ ERROR: No HITL entry found for query_id {result.query_id}")
                return False
            
            # Step 4: Simulate HITL approval (frontend approves the response)
            print("\n--- Step 4: Simulating HITL approval ---")
            
            hitl_entry.hitl_resolved = True
            hitl_entry.resolution_user_id = user_id
            hitl_entry.metadata_json = hitl_entry.metadata_json or {}
            hitl_entry.metadata_json["human_edits"] = "Updated response: The meaning of life is subjective."
            hitl_entry.metadata_json["human_final_answer"] = "Updated response: The meaning of life is subjective."
            hitl_entry.metadata_json["resolution_action"] = "approved_with_edits"
            
            await db.commit()
            print(f"  ✓ HITL entry marked as resolved with edits")
            
            # Step 5: Verify the resolved status
            print("\n--- Step 5: Verifying resolved status ---")
            
            # Refresh from DB
            stmt = select(ConfidenceLog).where(
                ConfidenceLog.query_id == result.query_id
            )
            db_result = await db.execute(stmt)
            resolved_entry = db_result.scalars().first()
            
            if resolved_entry:
                print(f"  ✓ Entry still found in database")
                print(f"    - Resolved: {resolved_entry.hitl_resolved}")
                print(f"    - Final answer: {resolved_entry.metadata_json.get('human_final_answer')}")
                
                if resolved_entry.hitl_resolved:
                    print("  ✓ Entry is marked as resolved")
                else:
                    print("  ✗ ERROR: Entry is not marked as resolved")
                    return False
            else:
                print(f"  ✗ ERROR: Entry not found after update")
                return False
            
            # Step 6: Test the polling endpoint scenario
            print("\n--- Step 6: Testing polling endpoint flow ---")
            
            # Simulate what the status endpoint does
            print(f"  Checking status for message_id: {result.query_id}")
            
            stmt = select(ConfidenceLog).where(
                ConfidenceLog.bot_id == bot_id,
                ConfidenceLog.query_id == result.query_id,
            )
            db_result = await db.execute(stmt)
            log_entry = db_result.scalars().first()
            
            if not log_entry:
                print(f"  ✗ ERROR: Message not found")
                return False
            
            if log_entry.hitl_resolved:
                print(f"  ✓ Message is resolved")
                resolved_answer = (
                    log_entry.metadata_json.get("human_final_answer")
                    or log_entry.metadata_json.get("human_edits")
                    or log_entry.metadata_json.get("ai_draft")
                    or ""
                )
                print(f"  ✓ Resolved answer retrieved: {resolved_answer}")
                
                return True
            else:
                print(f"  ✗ ERROR: Message is still pending")
                return False
    
    except Exception as e:
        logger.error(f"Test failed with error: {e}", exc_info=True)
        return False
    finally:
        await engine.dispose()


async def test_hitl_queue_retrieval():
    """Test retrieving HITL queue items."""
    
    print("\n" + "="*80)
    print("HITL QUEUE RETRIEVAL TEST")
    print("="*80 + "\n")
    
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    try:
        async with async_session() as db:
            print("✓ Database connection established")
            
            # Get first tenant
            stmt = select(ConfidenceLog).where(
                ConfidenceLog.routing_decision == RoutingDecision.HITL,
                ConfidenceLog.hitl_resolved == False,
            ).limit(5)
            
            result = await db.execute(stmt)
            hitl_items = result.scalars().all()
            
            print(f"\nFound {len(hitl_items)} unresolved HITL items:")
            for item in hitl_items:
                print(f"  - ID: {item.id}")
                print(f"    Query: {item.query_text[:50]}...")
                print(f"    Confidence: {item.overall_confidence}")
                print(f"    Bot: {item.bot_id}")
                print(f"    Resolved: {item.hitl_resolved}")
                print()
            
            if len(hitl_items) > 0:
                print("✓ HITL queue has pending items")
                return True
            else:
                print("⚠ No unresolved HITL items found")
                return True
    
    except Exception as e:
        logger.error(f"Queue retrieval test failed: {e}", exc_info=True)
        return False
    finally:
        await engine.dispose()


async def main():
    """Run all diagnostic tests."""
    
    print("\nStarting HITL diagnostic tests...\n")
    
    # Run tests
    test1_result = await test_hitl_flow()
    test2_result = await test_hitl_queue_retrieval()
    
    # Print summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    print(f"HITL Flow Test: {'PASSED ✓' if test1_result else 'FAILED ✗'}")
    print(f"Queue Retrieval Test: {'PASSED ✓' if test2_result else 'FAILED ✗'}")
    print("="*80 + "\n")
    
    return test1_result and test2_result


if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result else 1)
