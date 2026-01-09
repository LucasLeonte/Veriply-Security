#!/usr/bin/env python3
"""Test API queue endpoint directly"""
import asyncio
import json
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'apps/api'))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from app.models.confidence_log import ConfidenceLog
from app.core.config import settings

async def test_api_response():
    # Create async engine and session
    engine = create_async_engine(
        settings.database_url,
        echo=False,
        pool_pre_ping=True,
    )
    
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # Query pending items with hitl_resolved = False
        query = select(ConfidenceLog).where(ConfidenceLog.hitl_resolved.is_(False))
        result = await session.execute(query)
        pending_items = result.scalars().all()
        
        print(f"✅ PENDING ITEMS: {len(pending_items)}")
        for item in pending_items[:3]:  # Show first 3
            metadata = item.metadata_json or {}
            resolution = metadata.get("resolution_action", "NONE")
            print(f"   - ID:{item.id}, Resolved:{item.hitl_resolved}, Resolution:{resolution}, Status:{item.status}")
        
        # Query resolved items
        query2 = select(ConfidenceLog).where(ConfidenceLog.hitl_resolved.is_(True))
        result2 = await session.execute(query2)
        resolved_items = result2.scalars().all()
        
        print(f"✅ RESOLVED ITEMS: {len(resolved_items)}")
        for item in resolved_items[:3]:  # Show first 3
            metadata = item.metadata_json or {}
            resolution = metadata.get("resolution_action", "NONE")
            print(f"   - ID:{item.id}, Resolved:{item.hitl_resolved}, Resolution:{resolution}")
    
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(test_api_response())
