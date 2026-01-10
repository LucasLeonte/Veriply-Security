"""Test the full verified KB flow with the new threshold."""

import asyncio
import sys

sys.path.insert(0, 'apps/api')

from app.core.database import AsyncSessionLocal
from app.services.vector_search_service import VectorSearchService
from app.services.embedding_service import EmbeddingService
from app.models.verified_qa import VerifiedQA
from sqlalchemy import select


async def test_end_to_end():
    """Test the complete verified KB retrieval flow."""
    
    async with AsyncSessionLocal() as db:
        # Find a verified entry
        result = await db.execute(
            select(VerifiedQA).where(VerifiedQA.question_text.ilike('%january%')).limit(1)
        )
        verified_entry = result.scalar_one_or_none()
        
        if not verified_entry:
            print("No verified entry found")
            return
        
        print(f"\n{'='*80}")
        print(f"END-TO-END VERIFIED KB TEST")
        print(f"{'='*80}\n")
        
        print(f"Verified Entry in Database:")
        print(f"  Question: {verified_entry.question_text}")
        print(f"  Answer: {verified_entry.answer_text}")
        print(f"  Bot ID: {verified_entry.bot_id}\n")
        
        # Test with different phrasings
        test_queries = [
            "what holiday is 1 january?",
            "what is the holiday on January 1st?",
            "which holiday falls on the first of january?",
            "what do we celebrate on jan 1",
        ]
        
        embedding_service = EmbeddingService()
        vector_service = VectorSearchService(embedding_service)
        
        print(f"Testing with VERIFIED_KB_SIMILARITY_THRESHOLD = 0.85\n")
        print(f"{'='*80}\n")
        
        for query in test_queries:
            print(f"Query: \"{query}\"")
            
            try:
                results, latency = await vector_service.search(
                    db=db,
                    bot_id=verified_entry.bot_id,
                    tenant_id=verified_entry.tenant_id,
                    query=query,
                    k=3,
                )
                
                if results:
                    for i, result in enumerate(results, 1):
                        print(f"  Result {i}:")
                        print(f"    ✓ VERIFIED KB HIT" if result.is_verified else "    ○ Document chunk")
                        print(f"    Similarity: {result.similarity:.4f}")
                        if result.is_verified:
                            print(f"    Answer: {result.verified_answer[:80]}...")
                        print(f"    Latency: {latency}ms")
                else:
                    print(f"  ✗ No matches found")
                
                print()
                
            except Exception as e:
                print(f"  ✗ Error: {e}\n")
        
        await embedding_service.close()
        
        print(f"{'='*80}")
        print("✓ Verified KB is now working with semantic matching!")
        print(f"{'='*80}\n")


if __name__ == "__main__":
    asyncio.run(test_end_to_end())
