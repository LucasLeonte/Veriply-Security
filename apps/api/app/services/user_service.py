from app.core.database import AsyncSessionLocal
from app.models import Tenant, User
from app.services.auth_service import hash_password, generate_uuid
from sqlalchemy import select

async def register_user_and_tenant(email: str, password: str, tenant_name: str):
    """Register a new user and create a tenant."""
    async with AsyncSessionLocal() as session:
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
        
        return {"user_id": user_id, "tenant_id": tenant_id, "email": email}

async def get_user_by_email(email: str):
    """Fetch user by email."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()
