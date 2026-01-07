import asyncio
from sqlalchemy import text
from app.core.database import AsyncSessionLocal

async def check():
    async with AsyncSessionLocal() as db:
        # Find the entry with the CORRECT ai_draft (not placeholder)
        result = await db.execute(text("""
            SELECT id, query_text, 
                   metadata_json->>'ai_draft' as ai_draft,
                   hitl_resolved,
                   created_at
            FROM confidence_logs
            WHERE query_text = 'what is usability'
              AND metadata_json->>'ai_draft' NOT LIKE '%checking with the team%'
            ORDER BY created_at DESC
            LIMIT 5
        """))
        
        logs = result.fetchall()
        print(f'=== ENTRIES WITH CORRECT AI_DRAFT ===')
        for log in logs:
            ai_draft = log[2] or ''
            print(f'ID: {log[0]}')
            print(f'  Created: {log[4]}')
            print(f'  Resolved: {log[3]}')
            print(f'  AI Draft (full): {ai_draft}')
            print()

asyncio.run(check())
