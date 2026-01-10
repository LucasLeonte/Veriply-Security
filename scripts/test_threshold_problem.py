"""Test to demonstrate the threshold problem with semantic matching."""

import asyncio
import sys

sys.path.insert(0, 'apps/api')

from app.services.embedding_service import EmbeddingService
from app.models.verified_qa import VerifiedQA
from sqlalchemy import select
from app.core.database import AsyncSessionLocal


async def test_semantic_thresholds():
    """Test different question variations against verified entries."""
    
    embedding_service = EmbeddingService()
    
    async with AsyncSessionLocal() as db:
        # Get all verified questions
        result = await db.execute(select(VerifiedQA))
        verified_entries = result.scalars().all()
        
        if not verified_entries:
            print("No verified_qa entries found")
            return
        
        print(f"\n{'='*90}")
        print(f"TESTING SIMILARITY THRESHOLDS - Current setting: 0.95")
        print(f"{'='*90}\n")
        
        # Test with the "holiday" question which exists in the DB
        test_questions = [
            ("what holiday is 1 january?", "Exact match from DB"),
            ("what holiday is january 1?", "Word order changed"),
            ("what is the holiday on January 1st?", "Slightly different phrasing"),
            ("which holiday falls on the first of january?", "Very different phrasing"),
            ("january 1st holiday", "Shortened version"),
            ("what do we celebrate on jan 1", "Informal version"),
        ]
        
        print("Target: Finding matches for questions about January 1st holiday\n")
        
        # Find the "january 1" entry in verified_qa
        jan1_entry = None
        for entry in verified_entries:
            if "january" in entry.question_text.lower() or "jan" in entry.question_text.lower():
                jan1_entry = entry
                print(f"✓ Found verified entry:")
                print(f"  Question: {entry.question_text}")
                print(f"  Answer: {entry.answer_text}\n")
                break
        
        if not jan1_entry:
            print("No January holiday entry found. Using first entry.")
            jan1_entry = verified_entries[0]
            print(f"Test entry: {jan1_entry.question_text}\n")
        
        print(f"{'='*90}")
        print(f"SIMILARITY SCORES FOR DIFFERENT PHRASINGS:")
        print(f"{'='*90}\n")
        
        for test_q, description in test_questions:
            try:
                # Generate embedding for test question
                test_embedding = await embedding_service.embed_query(test_q)
                
                # Calculate similarity using the search function
                from app.services.verified_qa import search_verified_qa
                results = await search_verified_qa(
                    db=db,
                    tenant_id=jan1_entry.tenant_id,
                    group_id=jan1_entry.group_id,
                    bot_id=jan1_entry.bot_id,
                    query_embedding=test_embedding,
                    k=1,
                    similarity_threshold=0.0,  # Get all matches to see scores
                )
                
                # Find our target entry in results
                similarity = 0.0
                for qa, score in results:
                    if qa.id == jan1_entry.id:
                        similarity = score
                        break
                
                # Check against threshold
                threshold_status = "✓ PASS" if similarity >= 0.95 else "✗ FAIL"
                recommended_status = "✓ GOOD" if similarity >= 0.80 else "○ LOW"
                
                print(f"Question: {test_q}")
                print(f"  Description: {description}")
                print(f"  Similarity: {similarity:.4f}")
                print(f"  Current threshold (0.95): {threshold_status}")
                print(f"  Recommended threshold (0.80): {recommended_status}")
                print()
                
            except Exception as e:
                print(f"Error testing '{test_q}': {e}\n")
    
    await embedding_service.close()
    
    print(f"{'='*90}")
    print("RECOMMENDATION:")
    print(f"{'='*90}")
    print("Lower VERIFIED_KB_SIMILARITY_THRESHOLD from 0.95 to 0.80-0.85")
    print("This allows semantic matching while still maintaining quality.")
    print("\nWhy:")
    print("  • 0.95 = Only catches near-exact wording (defeats semantic search)")
    print("  • 0.85 = Good balance between precision and recall")
    print("  • 0.80 = More lenient, catches more variations")
    print("  • 0.70 = Standard for document search (too loose for verified KB)")
    print()


if __name__ == "__main__":
    asyncio.run(test_semantic_thresholds())
