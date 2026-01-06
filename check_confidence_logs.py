"""Check confidence logs with details"""
import asyncio
import sys
sys.path.insert(0, 'apps/api')
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.core.settings import settings

async def check():
    engine = create_async_engine(settings.get_database_url())
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        # Check pending HITL items
        result = await session.execute(text("""
            SELECT cl.id, cl.query_text, cl.overall_confidence, cl.metadata_json, 
                   b.name as bot_name, b.confidence_threshold
            FROM confidence_logs cl
            LEFT JOIN bots b ON cl.bot_id = b.id
            WHERE cl.hitl_resolved = false
            ORDER BY cl.created_at DESC
            LIMIT 5
        """))
        print("Pending HITL items:")
        for row in result.fetchall():
            print(f"ID: {row[0]}")
            print(f"User Question: {row[1]}")
            conf_pct = float(row[2]) * 100
            print(f"Confidence: {conf_pct:.1f}%")
            print(f"Bot: {row[4]} (threshold: {row[5]}%)")
            meta = row[3]
            if meta:
                draft = meta.get("ai_draft", "N/A")
                print(f"AI Draft: {draft[:100]}..." if len(draft) > 100 else f"AI Draft: {draft}")
            print("---")

asyncio.run(check())
