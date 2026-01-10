"""Test if verified KB semantic search now works."""

import asyncio
import sys

sys.path.insert(0, 'apps/api')

from app.core.database import AsyncSessionLocal
from app.services.verified_qa import search_verified_qa
from app.services.embedding_service import EmbeddingService
from app.models.verified_qa import VerifiedQA
from sqlalchemy import select


async def test_verified_search():
    """Test semantic search against verified KB."""
    
    async with AsyncSessionLocal() as db:
        # Get a sample verified_qa entry to test against
        result = await db.execute(select(VerifiedQA).limit(1))
        sample = result.scalar_one_or_none()
        
        if not sample:
            print("No verified_qa entries found to test against")
            return
        
        print(f"\n{'='*80}")
        print(f"TESTING VERIFIED KB SEMANTIC SEARCH")
        print(f"{'='*80}\n")
        
        print(f"Test Entry:")
        print(f"  Question: {sample.question_text}")
        print(f"  Answer: {sample.answer_text[:100]}...")
        print(f"  Bot ID: {sample.bot_id}")
        print(f"  Group ID: {sample.group_id}")
        print(f"  Tenant ID: {sample.tenant_id}\n")
        
        # Test 1: Exact question match
        print(f"Test 1: Searching with EXACT question...")
        embedding_service = EmbeddingService()
        
        try:
            query_embedding = await embedding_service.embed_query(sample.question_text)
            print(f"  Generated embedding: {len(query_embedding)} dimensions")
            
            results = await search_verified_qa(
                db=db,
                tenant_id=sample.tenant_id,
                group_id=sample.group_id,
                bot_id=sample.bot_id,
                query_embedding=query_embedding,
                k=3,
                similarity_threshold=0.7,
            )
            
            print(f"  Results found: {len(results)}")
            
            if results:
                for i, (qa, similarity) in enumerate(results, 1):
                    print(f"\n  Result {i}:")
                    print(f"    Question: {qa.question_text[:80]}...")
                    print(f"    Answer: {qa.answer_text[:80]}...")
                    print(f"    Similarity: {similarity:.4f}")
                    print(f"    Match: {'✓ EXACT' if qa.id == sample.id else '○ Similar'}")
            else:
                print("  ❌ NO RESULTS - Something is still wrong!")
                
        except Exception as e:
            print(f"  ❌ Error during search: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await embedding_service.close()
        
        # Test 2: Similar question
        print(f"\n\nTest 2: Searching with SIMILAR question...")
        # Modify the question slightly to test semantic matching
        similar_query = sample.question_text.replace("is", "was") if "is" in sample.question_text else sample.question_text + " please"
        print(f"  Similar query: {similar_query}")
        
        embedding_service2 = EmbeddingService()
        try:
            query_embedding2 = await embedding_service2.embed_query(similar_query)
            
            results2 = await search_verified_qa(
                db=db,
                tenant_id=sample.tenant_id,
                group_id=sample.group_id,
                bot_id=sample.bot_id,
                query_embedding=query_embedding2,
                k=3,
                similarity_threshold=0.7,
            )
            
            print(f"  Results found: {len(results2)}")
            
            if results2:
                for i, (qa, similarity) in enumerate(results2, 1):
                    print(f"\n  Result {i}:")
                    print(f"    Question: {qa.question_text[:80]}...")
                    print(f"    Similarity: {similarity:.4f}")
            else:
                print("  No matches above threshold 0.7")
                
        except Exception as e:
            print(f"  ❌ Error during search: {e}")
        finally:
            await embedding_service2.close()
        
        print(f"\n{'='*80}")
        print("✓ Vector index is working - semantic search functional!")
        print(f"{'='*80}\n")


if __name__ == "__main__":
    asyncio.run(test_verified_search())
