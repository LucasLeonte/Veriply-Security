"""
Diagnostic script to troubleshoot login issues
Checks: database connection, user existence, password hashing, JWT generation
"""

import asyncio
import sys
from pathlib import Path

# Add apps/api to path
sys.path.insert(0, str(Path(__file__).parent / "apps" / "api"))

from app.core.database import AsyncSessionLocal
from app.core.settings import settings
from app.models.user import User
from app.services.auth_service import hash_password, verify_password
from sqlalchemy import select
import jwt
from datetime import datetime, timedelta


async def main():
    print("\n" + "=" * 70)
    print("LOGIN DIAGNOSTIC REPORT")
    print("=" * 70)

    # Step 1: Check database connection
    print("\n[1] Database Connection Test")
    print("-" * 70)
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(User))
            users = result.scalars().all()
            print(f"✓ Connected to database")
            print(f"  Database URL: {settings.DATABASE_URL[:50]}...")
            print(f"  Total users in database: {len(users)}")
            
            if users:
                print("\n  Existing users:")
                for user in users[:5]:  # Show first 5
                    print(f"    - {user.email} (role: {user.role}, tenant: {user.tenant_id})")
            else:
                print("  ⚠ NO USERS FOUND IN DATABASE")
                print("  This is likely why login is failing!")
    except Exception as e:
        print(f"✗ Database connection failed: {e}")
        return

    # Step 2: Test password hashing and verification
    print("\n[2] Password Hashing Test")
    print("-" * 70)
    test_password = "TestPassword123!"
    try:
        hashed = hash_password(test_password)
        print(f"✓ Password hashed successfully")
        print(f"  Original: {test_password}")
        print(f"  Hashed: {hashed[:50]}...")
        
        # Test verification
        verified = verify_password(test_password, hashed)
        print(f"✓ Password verification: {'SUCCESS' if verified else 'FAILED'}")
        
        # Test with wrong password
        wrong_verified = verify_password("WrongPassword123!", hashed)
        print(f"✓ Wrong password rejected: {'SUCCESS' if not wrong_verified else 'FAILED'}")
    except Exception as e:
        print(f"✗ Password hashing failed: {e}")

    # Step 3: Test JWT token generation
    print("\n[3] JWT Token Generation Test")
    print("-" * 70)
    try:
        token_payload = {
            "sub": "test-user-id",
            "tenant_id": "test-tenant-id",
            "role": "owner",
            "exp": datetime.utcnow() + timedelta(hours=24)
        }
        token = jwt.encode(token_payload, settings.JWT_SECRET, algorithm="HS256")
        print(f"✓ Token generated successfully")
        print(f"  Token: {token[:50]}...")
        
        # Test token decoding
        decoded = jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])
        print(f"✓ Token decoded successfully")
        print(f"  User ID: {decoded['sub']}")
        print(f"  Tenant ID: {decoded['tenant_id']}")
        print(f"  Role: {decoded['role']}")
    except Exception as e:
        print(f"✗ JWT token failed: {e}")

    # Step 4: Test login with actual user
    print("\n[4] Login Test with Existing Users")
    print("-" * 70)
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(User))
            users = result.scalars().all()
            
            if not users:
                print("✗ No users in database to test with")
                print("\n  Solution: Create a test user with this command:")
                print("  python apps/api/create_test_user.py")
            else:
                # Try to simulate login with first user
                user = users[0]
                print(f"\nTesting with user: {user.email}")
                
                # Test password verification
                test_pwd = "TestPassword123!"
                is_correct = verify_password(test_pwd, user.password_hash)
                print(f"  Password match with test password: {is_correct}")
                
                if is_correct:
                    print(f"  ✓ This user CAN login with password: {test_pwd}")
                else:
                    print(f"  ✗ This user CANNOT login with password: {test_pwd}")
                    print(f"  Password hash: {user.password_hash[:50]}...")
                    
    except Exception as e:
        print(f"✗ Login test failed: {e}")

    # Step 5: Recommended actions
    print("\n[5] Recommended Actions")
    print("-" * 70)
    print("""
If you're still unable to login:

1. CREATE A TEST USER:
   python apps/api/create_test_user.py

2. VERIFY DATABASE IS ACCESSIBLE:
   python fix_connection_pool.py

3. CHECK API SERVER IS RUNNING:
   npm run dev (in terminal)

4. TEST LOGIN ENDPOINT:
   python apps/api/test_auth_endpoint.py

5. CHECK BROWSER CONSOLE FOR ERRORS:
   - Open your browser DevTools (F12)
   - Go to Console tab
   - Try logging in and check for error messages

6. CHECK NETWORK TAB:
   - Go to Network tab
   - Try logging in
   - Check the POST /api/v1/auth/login response
   - Look for error details
""")

    print("\n" + "=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
