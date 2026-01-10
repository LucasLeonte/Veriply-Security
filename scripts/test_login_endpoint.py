#!/usr/bin/env python3
"""
Test the login endpoint to diagnose the issue
"""
import httpx
import asyncio
import sys

async def test_login():
    """Test login endpoint"""
    async with httpx.AsyncClient() as client:
        try:
            print("Testing login endpoint...")
            print("=" * 60)
            
            # Test with the test user created earlier
            response = await client.post(
                "http://127.0.0.1:8000/api/v1/auth/login",
                json={
                    "email": "testuser@veriply.app",
                    "password": "TestPassword123!",
                    "tenant_name": "test"  # Required by schema
                },
                timeout=10.0
            )
            
            print(f"Status Code: {response.status_code}")
            print(f"Response Headers: {dict(response.headers)}")
            print(f"Response Body: {response.json()}")
            
            if response.status_code == 200:
                data = response.json()
                if "access_token" in data:
                    print("\n✓ LOGIN SUCCESSFUL!")
                    print(f"Access Token: {data['access_token'][:50]}...")
                    return True
                else:
                    print("\n✗ No access token in response")
                    return False
            else:
                print(f"\n✗ Login failed with status {response.status_code}")
                return False
                
        except httpx.ConnectError as e:
            print(f"✗ Connection Error: {e}")
            print("Is the backend running? (npm run dev)")
            return False
        except httpx.TimeoutException as e:
            print(f"✗ Timeout Error: {e}")
            print("The endpoint is taking too long to respond - possible infinite loop!")
            return False
        except Exception as e:
            print(f"✗ Error: {e}")
            return False

if __name__ == "__main__":
    success = asyncio.run(test_login())
    sys.exit(0 if success else 1)
