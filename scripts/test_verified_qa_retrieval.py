"""Test script to verify that approved HITL items are searchable via verified Q&A.

This script:
1. Checks if there are any verified Q&A entries in the database
2. Tests the search_verified_qa function directly
3. Verifies embeddings are present
"""

import asyncio
import sys
import os

# Add the apps/api directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'apps', 'api'))

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import AsyncSessionLocal
from app.models.verified_qa import VerifiedQA
from app.models.bot import Bot


async def check_verified_qa():
    """Check all verified Q&A entries in the database."""
    print("\n" + "="*60)
    print("VERIFIED Q&A DATABASE CHECK")
    print("="*60)
    
    async with AsyncSessionLocal() as db:
        # Count total entries
        count_result = await db.execute(
            text("SELECT COUNT(*) FROM verified_qa")
        )
        total = count_result.scalar()
        print(f"\nTotal verified_qa entries: {total}")
        
        if total == 0:
            print("\n⚠️  No verified Q&A entries found!")
            print("   This means no HITL items have been approved yet,")
            print("   or the approval process isn't creating verified Q&A entries.")
            return
        
        # Get entries with embedding info
        result = await db.execute(
            select(VerifiedQA).limit(10)
        )
        entries = result.scalars().all()
        
        print(f"\nFirst {len(entries)} entries:")
        print("-"*60)
        
        for entry in entries:
            has_embedding = entry.question_embedding is not None
            embedding_dims = len(entry.question_embedding) if has_embedding else 0
            
            print(f"\nID: {entry.id}")
            print(f"  Bot ID: {entry.bot_id}")
            print(f"  Group ID: {entry.group_id}")
            print(f"  Tenant ID: {entry.tenant_id}")
            print(f"  Question: {entry.question_text[:80]}...")
            print(f"  Answer: {entry.answer_text[:80]}...")
            print(f"  Has Embedding: {has_embedding}")
            if has_embedding:
                print(f"  Embedding Dims: {embedding_dims}")
            print(f"  Approved At: {entry.approved_at}")


async def test_search_verified_qa():
    """Test the search_verified_qa function."""
    print("\n" + "="*60)
    print("TESTING SEARCH VERIFIED Q&A")
    print("="*60)
    
    from app.services.verified_qa import search_verified_qa
    from app.services.embedding_service import EmbeddingService
    
    async with AsyncSessionLocal() as db:
        # First get a verified QA entry to test with
        result = await db.execute(
            select(VerifiedQA).where(
                VerifiedQA.question_embedding.isnot(None)
            ).limit(1)
        )
        entry = result.scalar_one_or_none()
        
        if not entry:
            print("\n⚠️  No verified Q&A entries with embeddings found!")
            return
        
        print(f"\nUsing verified Q&A entry: {entry.id}")
        print(f"  Question: {entry.question_text[:80]}...")
        print(f"  Bot ID: {entry.bot_id}")
        print(f"  Group ID: {entry.group_id}")
        print(f"  Tenant ID: {entry.tenant_id}")
        
        # Generate embedding for the same question to test exact match
        print("\nGenerating embedding for test query...")
        embedding_service = EmbeddingService()
        test_query = entry.question_text
        query_embedding = await embedding_service.embed_query(test_query)
        await embedding_service.close()
        
        print(f"  Query embedding dims: {len(query_embedding)}")
        
        # Test search
        print("\nTesting search_verified_qa()...")
        try:
            results = await search_verified_qa(
                db=db,
                tenant_id=entry.tenant_id,
                group_id=entry.group_id,
                bot_id=entry.bot_id,
                query_embedding=query_embedding,
                k=5,
                similarity_threshold=0.5,  # Lower threshold for testing
            )
            
            print(f"\nSearch returned {len(results)} results:")
            for qa, similarity in results:
                print(f"  - {qa.question_text[:60]}... (similarity: {similarity:.4f})")
                
            if not results:
                print("\n⚠️  No results returned!")
                print("   This could indicate:")
                print("   - RLS policy blocking access")
                print("   - Embedding mismatch")
                print("   - Similarity threshold too high")
        except Exception as e:
            print(f"\n❌ Search failed with error: {e}")
            import traceback
            traceback.print_exc()


async def check_rls_settings():
    """Check if RLS is enabled on verified_qa table."""
    print("\n" + "="*60)
    print("RLS CONFIGURATION CHECK")
    print("="*60)
    
    async with AsyncSessionLocal() as db:
        # Check if RLS is enabled
        result = await db.execute(text("""
            SELECT relrowsecurity, relforcerowsecurity 
            FROM pg_class 
            WHERE relname = 'verified_qa'
        """))
        row = result.first()
        
        if row:
            print(f"\nRLS enabled: {row[0]}")
            print(f"RLS forced: {row[1]}")
        else:
            print("\n⚠️  Table verified_qa not found!")
            return
        
        # Check RLS policies
        result = await db.execute(text("""
            SELECT policyname, cmd, qual 
            FROM pg_policies 
            WHERE tablename = 'verified_qa'
        """))
        policies = result.fetchall()
        
        print(f"\nRLS policies ({len(policies)}):")
        for policy in policies:
            print(f"  - {policy[0]} ({policy[1]})")
            print(f"    Condition: {policy[2][:80] if policy[2] else 'N/A'}...")


async def main():
    print("\n" + "="*60)
    print("VERIFIED Q&A KNOWLEDGE BASE TEST")
    print("="*60)
    print("\nThis script tests if approved HITL items are properly")
    print("stored and searchable in the verified Q&A knowledge base.")
    
    await check_rls_settings()
    await check_verified_qa()
    await test_search_verified_qa()
    
    print("\n" + "="*60)
    print("TEST COMPLETE")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())
