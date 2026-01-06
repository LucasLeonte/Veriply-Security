"""Update existing confidence logs to recalculate based on AI draft content"""
import asyncio
import sys
import re
sys.path.insert(0, 'apps/api')
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.core.settings import settings

NO_ANSWER_PATTERNS = [
    "i don't have information",
    "i don't know",
    "i do not have information",
    "i do not know",
    "i'm not sure",
    "i am not sure",
    "i cannot find",
    "i can't find",
    "no information available",
    "not in the knowledge base",
    "checking with the team",
    "i'm checking with",
    "i am checking with",
    "you'll hear from us",
    "unable to answer",
    "cannot answer",
    "can't answer",
    "don't have enough information",
    "do not have enough information",
    "outside my knowledge",
    "beyond my knowledge",
    "not able to find",
]

def is_no_answer(ai_draft: str) -> bool:
    if not ai_draft:
        return True
    draft_lower = ai_draft.lower()
    for pattern in NO_ANSWER_PATTERNS:
        if pattern in draft_lower:
            return True
    return False

async def update():
    engine = create_async_engine(settings.get_database_url())
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        # Get all pending HITL items
        result = await session.execute(text("""
            SELECT id, metadata_json FROM confidence_logs WHERE hitl_resolved = false
        """))
        rows = result.fetchall()
        
        for row in rows:
            log_id = row[0]
            meta = row[1] or {}
            ai_draft = meta.get("ai_draft", "")
            
            if is_no_answer(ai_draft):
                print(f"Updating {log_id} - bot doesn't know answer -> 0% confidence")
                await session.execute(text("""
                    UPDATE confidence_logs SET overall_confidence = 0 WHERE id = :id
                """), {"id": log_id})
            else:
                print(f"Keeping {log_id} - bot gave substantive answer")
        
        await session.commit()
        print("Done!")

asyncio.run(update())
