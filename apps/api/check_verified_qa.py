"""Check verified_qa table entries."""
import asyncio
from sqlalchemy import text
from app.core.database import engine

async def check_verified_qa():
    async with engine.begin() as conn:
        result = await conn.execute(text(
            """
            SELECT 
                id, 
                question_text, 
                LEFT(answer_text, 50) as answer_preview,
                created_at,
                approved_by_user_id,
                bot_id
            FROM verified_qa 
            ORDER BY created_at DESC 
            LIMIT 5
            """
        ))
        
        rows = result.fetchall()
        
        if not rows:
            print("\n❌ No verified_qa entries found!")
            print("Story 7.1 integration not working yet.\n")
        else:
            print(f"\n✅ Found {len(rows)} verified_qa entries:\n")
            print(f"{'ID':<36} | {'Question':<40} | {'Answer Preview':<50} | {'Approved By':<36} | {'Created At'}")
            print("-" * 200)
            for row in rows:
                print(f"{row[0]} | {row[1][:40]:<40} | {row[2]:<50} | {row[4]} | {row[3]}")
            print("\n✅ Story 7.1 is working! Verified Q&A entries are being created.\n")

if __name__ == "__main__":
    asyncio.run(check_verified_qa())
