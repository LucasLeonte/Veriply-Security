import asyncio
from sqlalchemy import text
from app.core.database import AsyncSessionLocal

async def check():
    async with AsyncSessionLocal() as db:
        result = await db.execute(text("""
            SELECT id, query_text, 
                   metadata_json->>'ai_draft' as ai_draft,
                   hitl_resolved,
                   created_at
            FROM confidence_logs
            WHERE query_text = 'what is usability'
            ORDER BY created_at DESC
        """))
        
        logs = result.fetchall()
        print(f'=== ALL LOGS ({len(logs)} total) ===')
        for log in logs:
            ai_draft = log[2] or ''
            print(f'ID: {log[0]}')
            print(f'  Created: {log[4]}')
            print(f'  Resolved: {log[3]}')
            print(f'  AI Draft: {ai_draft[:80]}')
            print()

asyncio.run(check())
