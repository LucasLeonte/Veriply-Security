"""Test to check if verified_qa entries are being stored correctly."""

import asyncio
import sys
from sqlalchemy import select, text
from sqlalchemy.orm import selectinload

# Add api directory to path
sys.path.insert(0, 'apps/api')

from app.core.database import AsyncSessionLocal
from app.models.verified_qa import VerifiedQA
from app.models.confidence_log import ConfidenceLog, RoutingDecision


async def check_verified_qa_storage():
    """Check if verified_qa entries exist and are queryable."""
    
    async with AsyncSessionLocal() as db:
        # 1. Count total verified_qa entries
        count_result = await db.execute(select(VerifiedQA))
        verified_entries = count_result.scalars().all()
        
        print(f"\n{'='*60}")
        print(f"VERIFIED KB STATUS CHECK")
        print(f"{'='*60}")
        print(f"\nTotal verified_qa entries: {len(verified_entries)}")
        
        if verified_entries:
            print("\n--- Sample Verified Q&A Entries ---")
            for idx, entry in enumerate(verified_entries[:5], 1):
                print(f"\n{idx}. Verified Q&A ID: {entry.id}")
                print(f"   Question: {entry.question_text[:100]}...")
                print(f"   Answer: {entry.answer_text[:100]}...")
                print(f"   Bot ID: {entry.bot_id}")
                print(f"   Group ID: {entry.group_id}")
                print(f"   Tenant ID: {entry.tenant_id}")
                print(f"   Has Embedding: {entry.question_embedding is not None}")
                if entry.question_embedding is not None:
                    print(f"   Embedding dimensions: {len(entry.question_embedding)}")
                print(f"   Approved at: {entry.approved_at}")
                print(f"   Approved by: {entry.approved_by_user_id}")
        else:
            print("\n⚠️  NO VERIFIED_QA ENTRIES FOUND!")
            print("\nThis means approved HITL items are NOT being saved to the verified KB.")
        
        # 2. Check HITL items that should have created verified_qa entries
        print(f"\n{'='*60}")
        print(f"CHECKING HITL APPROVALS")
        print(f"{'='*60}")
        
        hitl_result = await db.execute(
            select(ConfidenceLog)
            .where(ConfidenceLog.hitl_resolved == True)
            .order_by(ConfidenceLog.resolution_timestamp.desc())
            .limit(10)
        )
        hitl_items = hitl_result.scalars().all()
        
        print(f"\nTotal HITL items marked as resolved: {len(hitl_items)}")
        
        if hitl_items:
            print("\n--- Recent HITL Approvals ---")
            for idx, item in enumerate(hitl_items, 1):
                print(f"\n{idx}. HITL Item ID: {item.id}")
                print(f"   Query: {item.query_text[:100] if item.query_text else 'N/A'}...")
                print(f"   Resolved: {item.hitl_resolved}")
                print(f"   Resolved by: {item.resolution_user_id}")
                print(f"   Resolved at: {item.resolution_timestamp}")
                print(f"   Bot ID: {item.bot_id}")
                
                # Check metadata for verified_qa_id
                metadata = item.metadata_json or {}
                verified_qa_id = metadata.get("verified_qa_id")
                if verified_qa_id:
                    print(f"   ✓ Metadata has verified_qa_id: {verified_qa_id}")
                    
                    # Verify it actually exists in the database
                    check = await db.execute(
                        select(VerifiedQA).where(VerifiedQA.id == verified_qa_id)
                    )
                    verified_entry = check.scalar_one_or_none()
                    if verified_entry:
                        print(f"   ✓ VerifiedQA entry EXISTS in database")
                    else:
                        print(f"   ✗ VerifiedQA entry NOT FOUND in database!")
                else:
                    print(f"   ✗ NO verified_qa_id in metadata")
                    print(f"   Metadata keys: {list(metadata.keys())}")
        else:
            print("\n⚠️  No resolved HITL items found.")
        
        # 3. Check the vector index on verified_qa
        print(f"\n{'='*60}")
        print(f"CHECKING VECTOR INDEX")
        print(f"{'='*60}")
        
        try:
            index_result = await db.execute(
                text("""
                    SELECT indexname, indexdef 
                    FROM pg_indexes 
                    WHERE tablename = 'verified_qa' 
                    AND indexdef LIKE '%vector%'
                """)
            )
            indexes = index_result.fetchall()
            
            if indexes:
                print("\n✓ Vector indexes found on verified_qa:")
                for index_name, index_def in indexes:
                    print(f"\n   - {index_name}")
                    print(f"     {index_def[:100]}...")
            else:
                print("\n✗ NO vector indexes found on verified_qa table!")
                print("   This could prevent semantic search from working.")
        except Exception as e:
            print(f"\n✗ Error checking indexes: {e}")


if __name__ == "__main__":
    asyncio.run(check_verified_qa_storage())
