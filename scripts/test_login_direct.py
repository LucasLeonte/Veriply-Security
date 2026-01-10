#!/usr/bin/env python3
"""
Direct test of login endpoint
"""

import asyncio
import aiohttp
import json

async def test_login():
    """Test login endpoint directly"""
    url = "http://localhost:8000/api/v1/auth/login"
    payload = {
        "email": "testuser@veriply.app",
        "password": "TestPassword123!",
        "tenant_name": "Test Tenant"
    }
    
    print(f"Testing login to {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    print()
    
    try:
        async with aiohttp.ClientSession() as session:
            print("Sending request...")
            async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                print(f"Status: {resp.status}")
                data = await resp.json()
                print(f"Response: {json.dumps(data, indent=2)}")
    except asyncio.TimeoutError:
        print("ERROR: Request timed out after 10 seconds!")
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    asyncio.run(test_login())
