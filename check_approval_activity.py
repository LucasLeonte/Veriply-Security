#!/usr/bin/env python3
"""Check recent approval activity and frontend polling."""

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from datetime import datetime, timedelta
import sys
from pathlib import Path

sys.path.insert(0, str(Path('.') / 'apps' / 'api'))

from app.core.settings import settings
from app.models.confidence_log import ConfidenceLog, RoutingDecision


async def check_approval_activity():
    """Check if approvals are actually working."""
    
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as db:
        print("\n" + "="*80)
        print("APPROVAL ACTIVITY CHECK")
        print("="*80 + "\n")
        
        # Check recently resolved items
        one_hour_ago = datetime.utcnow() - timedelta(hours=1)
        
        stmt_recent = select(ConfidenceLog).where(
            ConfidenceLog.hitl_resolved == True,
            ConfidenceLog.resolution_timestamp >= one_hour_ago
        ).order_by(ConfidenceLog.resolution_timestamp.desc()).limit(5)
        
        result_recent = await db.execute(stmt_recent)
        recent = result_recent.scalars().all()
        
        print("📊 APPROVALS IN LAST HOUR")
        print("-" * 80)
        if recent:
            print(f"✅ Found {len(recent)} items resolved:\n")
            for item in recent:
                query_text = item.query_text[:40] + "..." if item.query_text else "N/A"
                print(f"  ✓ {query_text}")
                print(f"    Resolved: {item.resolution_timestamp}")
                print(f"    By user: {item.resolution_user_id}")
                print()
        else:
            print("❌ NO approvals in the last hour\n")
            print("⚠️  This means:")
            print("   1. No one has approved items yet, OR")
            print("   2. Approval endpoint is failing silently, OR")
            print("   3. Frontend is not calling the approval endpoint\n")
        
        # Check ALL pending items
        stmt_pending = select(ConfidenceLog).where(
            ConfidenceLog.hitl_resolved == False,
            ConfidenceLog.routing_decision == RoutingDecision.hitl
        ).order_by(ConfidenceLog.created_at.desc())
        
        result_pending = await db.execute(stmt_pending)
        pending = result_pending.scalars().all()
        
        print("\n📋 PENDING ITEMS (Still Awaiting Approval)")
        print("-" * 80)
        print(f"Total: {len(pending)} items\n")
        
        for i, item in enumerate(pending[:3], 1):
            age_hours = (datetime.utcnow() - item.created_at.replace(tzinfo=None)).total_seconds() / 3600
            query_text = item.query_text[:50] + "..." if item.query_text else "N/A"
            print(f"{i}. {query_text}")
            print(f"   ID: {item.id}")
            print(f"   Query ID: {item.query_id}")
            print(f"   In queue: {age_hours:.1f} hours")
            print(f"   Status: ⏳ STILL PENDING")
            print()
        
        # Check status endpoint response
        print("\n🔍 WHAT FRONTEND POLLING SEES")
        print("-" * 80)
        if pending:
            first_pending = pending[0]
            print(f"When frontend polls: /bots/{first_pending.bot_id}/chat/{first_pending.query_id}/status")
            print(f"\nResponse should be:")
            print(f'  {{"status": "pending", "message_id": "{first_pending.query_id}"}}')
            print(f"\nFrontend keeps showing: 'Waiting for team...'\n")
        
        print("="*80 + "\n")
    
    await engine.dispose()


async def check_database_constraints():
    """Check if database constraints are the issue."""
    
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as db:
        print("\n" + "="*80)
        print("DATABASE CONSTRAINT CHECK")
        print("="*80 + "\n")
        
        # Get a resolved item and check its user
        stmt_resolved = select(ConfidenceLog).where(
            ConfidenceLog.hitl_resolved == True,
            ConfidenceLog.resolution_user_id.isnot(None)
        ).limit(1)
        
        result_resolved = await db.execute(stmt_resolved)
        resolved_item = result_resolved.scalars().first()
        
        if resolved_item:
            print("✓ Found resolved item with user_id:")
            print(f"  Resolution user ID: {resolved_item.resolution_user_id}")
            print(f"  This proves: Foreign key constraint CAN pass with valid user\n")
        
        print("="*80 + "\n")
    
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(check_approval_activity())
    asyncio.run(check_database_constraints())
