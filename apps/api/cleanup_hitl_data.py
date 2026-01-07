"""
Cleanup script to fix the HITL approval data corruption issue.

This script:
1. Deletes ConfidenceLog entries with placeholder ai_draft messages
2. Deletes failed documents created from bad HITL approvals
3. Updates the verified_qa entry with the correct answer from the good entry
"""
import asyncio
from sqlalchemy import text, update, delete
from app.core.database import AsyncSessionLocal
from app.models.verified_qa import VerifiedQA
from app.models.confidence_log import ConfidenceLog
from app.models.document import Document

# The correct AI response from the good entry
CORRECT_ANSWER = """Usability refers to how easy and efficient it is for users to achieve their goals when interacting with a product or system. According to [Source: les5_usability_2223_v3.pdf], usability involves testing designs through various methods such as usability tests and creating personas, which are representations of key user segments based on research.

Usability also encompasses the use of prototypes—both low-fidelity (hand-drawn mock-ups or printouts) and high-fidelity (computer-based with interactive features)—to identify issues early in the design process. These prototypes help in visualizing alternative solutions and collecting performance data from users, aiding in the development and refinement of the final product.

Additionally, usability involves aligning user expectations through effective onboarding and marketing to ensure that products are intuitive and easy to use. According to [Source: les3_usability_v2.pdf], this can be achieved by leveraging affordances—perceptual characteristics of objects or interfaces that suggest their intended uses—to guide users in the correct actions without needing explicit instructions.

In summary, usability is about designing products that are user-friendly and efficient, ensuring that users can easily achieve their goals through well-designed interfaces and clear indications of how to use them."""


async def cleanup():
    async with AsyncSessionLocal() as db:
        print("=== HITL DATA CLEANUP ===\n")
        
        # 1. Delete bad confidence_log entries (with placeholder)
        result = await db.execute(text("""
            DELETE FROM confidence_logs
            WHERE query_text = 'what is usability'
              AND metadata_json->>'ai_draft' LIKE '%checking with the team%'
            RETURNING id
        """))
        deleted_logs = result.fetchall()
        print(f"1. Deleted {len(deleted_logs)} bad ConfidenceLog entries with placeholder text")
        
        # 2. Delete failed documents from HITL approvals
        result = await db.execute(text("""
            DELETE FROM documents
            WHERE title LIKE 'Verified Q&A: what is usability%'
              AND status IN ('failed', 'error', 'uploaded')
            RETURNING id, title
        """))
        deleted_docs = result.fetchall()
        print(f"2. Deleted {len(deleted_docs)} failed/error documents:")
        for doc in deleted_docs:
            print(f"   - {doc[1]}")
        
        # 3. Update the verified_qa entry with the correct answer
        result = await db.execute(text("""
            UPDATE verified_qa
            SET answer_text = :correct_answer
            WHERE question_text = 'what is usability'
            RETURNING id, question_text
        """), {"correct_answer": CORRECT_ANSWER})
        updated_qa = result.fetchall()
        print(f"\n3. Updated {len(updated_qa)} VerifiedQA entries with correct answer")
        for qa in updated_qa:
            print(f"   - {qa[0]}: {qa[1]}")
        
        # Commit all changes
        await db.commit()
        print("\n✅ Cleanup complete!")
        
        # Verify the results
        print("\n=== VERIFICATION ===")
        
        # Check remaining confidence_logs
        result = await db.execute(text("""
            SELECT id, metadata_json->>'ai_draft' as ai_draft
            FROM confidence_logs
            WHERE query_text = 'what is usability'
        """))
        remaining = result.fetchall()
        print(f"\nRemaining ConfidenceLog entries: {len(remaining)}")
        for entry in remaining:
            ai_draft = entry[1] or ''
            print(f"  {entry[0]}: {ai_draft[:60]}...")
        
        # Check verified_qa
        result = await db.execute(text("""
            SELECT id, question_text, answer_text
            FROM verified_qa
            WHERE question_text = 'what is usability'
        """))
        qa_entries = result.fetchall()
        print(f"\nVerifiedQA entries: {len(qa_entries)}")
        for qa in qa_entries:
            print(f"  {qa[0]}")
            print(f"    Question: {qa[1]}")
            print(f"    Answer: {qa[2][:80]}...")

asyncio.run(cleanup())
