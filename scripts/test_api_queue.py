#!/usr/bin/env python3
"""Test the actual API response from /api/v1/hitl/queue"""

import asyncio
import sys
import json
import aiohttp
from datetime import datetime

sys.path.insert(0, 'apps/api')

from app.core.settings import settings
from app.core.database import AsyncSessionLocal
from app.models.user import User
from app.models.tenants import Tenant
from sqlalchemy import select


async def get_test_token():
    """Get a test JWT token for a user"""
    async with AsyncSessionLocal() as db:
        # Get first tenant and user
        result = await db.execute(select(Tenant).limit(1))
        tenant = result.scalars().first()
        
        if not tenant:
            print("No tenants found")
            return None, None
        
        result = await db.execute(
            select(User).where(User.tenant_id == tenant.id).limit(1)
        )
        user = result.scalars().first()
        
        if not user:
            print("No users found")
            return None, None
        
        print(f"Using tenant: {tenant.id}")
        print(f"Using user: {user.id}")
        
        return user, tenant


async def test_api():
    """Test the API endpoint"""
    user, tenant = await get_test_token()
    if not user or not tenant:
        return
    
    # Generate a test token
    import jwt
    from app.core.settings import settings
    
    payload = {
        "sub": str(user.id),
        "tenant_id": str(tenant.id),
        "role": "admin",
        "exp": 9999999999,
    }
    
    token = jwt.encode(payload, settings.JWT_SECRET, algorithm="HS256")
    
    # Call the endpoint
    async with aiohttp.ClientSession() as session:
        headers = {"Authorization": f"Bearer {token}"}
        
        print(f"\nCalling: http://localhost:8000/api/v1/hitl/queue")
        print(f"Authorization: Bearer {token[:50]}...")
        
        async with session.get(
            "http://localhost:8000/api/v1/hitl/queue",
            headers=headers,
            params={"sort_by": "oldest", "_t": str(int(datetime.now().timestamp() * 1000))}
        ) as resp:
            print(f"Status: {resp.status}")
            data = await resp.json()
            
            items = data.get("items", [])
            print(f"\nReturned {len(items)} items:")
            print("="*80)
            
            for i, item in enumerate(items, 1):
                status = item.get("status", "unknown")
                resolution = item.get("metadata", {}).get("resolution_action")
                print(f"\n{i}. [{status}] {item['userQuestion'][:60]}")
                print(f"   ID: {item['id']}")
                print(f"   resolution_action: {resolution}")
                
                if resolution:
                    print(f"   ^^^ THIS SHOULD NOT BE HERE! ^^^")
            
            print("\n" + "="*80)
            print(f"Stats: {data.get('stats')}")


if __name__ == "__main__":
    asyncio.run(test_api())
