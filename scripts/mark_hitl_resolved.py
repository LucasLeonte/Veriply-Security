#!/usr/bin/env python3
"""Mark specific HITL items as resolved with their AI drafts.

Usage:
  python scripts/mark_hitl_resolved.py

This script marks the specified confidence_logs (by query_id) as resolved,
using the stored ai_draft as the human_final_answer. It sets hitl_resolved,
resolution_timestamp, and resolution_action, leaving resolution_user_id null.
"""

import asyncio
from datetime import datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select

import sys
from pathlib import Path

# Ensure app modules are importable
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "apps" / "api"))

from app.core.settings import settings  # type: ignore
from app.models.confidence_log import ConfidenceLog  # type: ignore

# Query IDs to resolve (pending items)
QUERY_IDS = [
    "c5baf89e-6d94-4496-abbc-5511bad2cd90",  # professional email
    "36241a1c-a1d6-4608-8500-8190488a28b7",  # leg uit wat usability is ?
    "ded3a36c-16a5-4a63-831a-7e4749914225",  # what is usability
]


async def main() -> None:
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as db:
        for qid in QUERY_IDS:
            query_uuid = UUID(qid)
            result = await db.execute(
                select(ConfidenceLog).where(ConfidenceLog.query_id == query_uuid)
            )
            item = result.scalars().first()
            if not item:
                print(f"❌ Not found: {qid}")
                continue

            if not item.metadata_json:
                item.metadata_json = {}

            ai_draft = item.metadata_json.get("ai_draft", "")
            # Apply resolution
            item.hitl_resolved = True
            item.resolution_timestamp = datetime.utcnow()
            item.metadata_json["human_final_answer"] = ai_draft
            item.metadata_json["resolution_action"] = "approved"

            await db.commit()
            print(f"✅ Marked resolved: {qid} (answer length={len(ai_draft)})")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
