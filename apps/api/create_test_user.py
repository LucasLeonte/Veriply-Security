"""
Create a test user with known credentials for testing login
"""

import asyncio
import sys
from pathlib import Path

# Add apps/api to path
sys.path.insert(0, str(Path(__file__).parent / "apps" / "api"))

from app.core.database import AsyncSessionLocal
from app.models.user import User
from app.models.tenant import Tenant
from app.services.auth_service import hash_password, generate_uuid
from sqlalchemy import select


async def create_test_user():
    print("\n" + "=" * 70)
    print("CREATE TEST USER")
    print("=" * 70)
    
    email = "testuser@veriply.app"
    password = "TestPassword123!"
    tenant_name = "Test Tenant"
    
    async with AsyncSessionLocal() as session:
        # Check if user already exists
        result = await session.execute(
            select(User).where(User.email == email)
        )
        existing_user = result.scalar_one_or_none()
        
        if existing_user:
            print(f"\n✓ User already exists: {email}")
            print(f"  Use these credentials to login:")
            print(f"  Email: {email}")
            print(f"  Password: (the password you used during registration)")
            return
        
        # Create new tenant and user
        tenant_id = generate_uuid()
        user_id = generate_uuid()
        
        tenant = Tenant(id=tenant_id, name=tenant_name, plan="free")
        user = User(
            id=user_id,
            email=email,
            tenant_id=tenant_id,
            role="owner",
            password_hash=hash_password(password)
        )
        
        session.add(tenant)
        session.add(user)
        await session.commit()
        
        print(f"\n✓ Test user created successfully!")
        print(f"\n  Email:    {email}")
        print(f"  Password: {password}")
        print(f"  Role:     owner")
        print(f"  Tenant:   {tenant_name}")
        print(f"\n  Use these credentials to login in the app")


if __name__ == "__main__":
    asyncio.run(create_test_user())
