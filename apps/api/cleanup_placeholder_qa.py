"""Clean up verified_qa entries with placeholder messages.

This script removes verified_qa entries where the answer_text is the placeholder
"I'm checking with the team for the best answer. You'll hear from us shortly."
These entries were created due to a bug where the frontend was submitting to the
review queue with the placeholder message instead of the actual AI draft.
"""

import asyncio
from sqlalchemy import text, delete
from app.core.database import AsyncSessionLocal
from app.models.verified_qa import VerifiedQA

PLACEHOLDER_MSG = "I'm checking with the team for the best answer. You'll hear from us shortly."

async def cleanup():
    async with AsyncSessionLocal() as db:
        # First show what will be deleted
        result = await db.execute(
            text("""
                SELECT id, question_text, answer_text, approved_at
                FROM verified_qa 
                WHERE answer_text = :placeholder
            """),
            {"placeholder": PLACEHOLDER_MSG}
        )
        rows = result.fetchall()
        
        print(f"\nFound {len(rows)} verified_qa entries with placeholder message:")
        print("-"*80)
        for row in rows:
            print(f"  ID: {row[0]}")
            print(f"  Question: {row[1][:60]}...")
            print(f"  Approved: {row[3]}")
            print()
        
        if not rows:
            print("No entries to delete.")
            return
        
        # Confirm deletion
        confirm = input("\nDelete these entries? (yes/no): ")
        if confirm.lower() != "yes":
            print("Aborted.")
            return
        
        # Delete the entries
        result = await db.execute(
            text("""
                DELETE FROM verified_qa 
                WHERE answer_text = :placeholder
                RETURNING id
            """),
            {"placeholder": PLACEHOLDER_MSG}
        )
        deleted_ids = result.fetchall()
        await db.commit()
        
        print(f"\n✓ Deleted {len(deleted_ids)} entries.")

if __name__ == "__main__":
    asyncio.run(cleanup())
