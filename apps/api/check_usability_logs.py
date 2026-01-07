"""Check confidence logs for usability queries."""
import asyncio
from sqlalchemy import text
from app.core.database import AsyncSessionLocal

async def check():
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            text("""
                SELECT id, query_text, 
                       metadata_json->>'ai_draft' as ai_draft,
                       metadata_json->>'source' as source,
                       hitl_resolved,
                       created_at
                FROM confidence_logs 
                WHERE query_text LIKE :pattern
                ORDER BY created_at DESC 
            """),
            {"pattern": "%usability%"}
        )
        rows = result.fetchall()
        print("Confidence logs with usability in query:")
        print("-"*100)
        for row in rows:
            ai_draft = row[2] or ''
            ai_draft_preview = ai_draft[:100] + '...' if len(ai_draft) > 100 else ai_draft
            print(f"ID: {row[0]}")
            print(f"  Query: {row[1]}")
            print(f"  Source: {row[3]}")
            print(f"  Resolved: {row[4]}")
            print(f"  ai_draft: {ai_draft_preview}")
            print(f"  Created: {row[5]}")
            print()

asyncio.run(check())
