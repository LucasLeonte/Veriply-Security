import pytest
from sqlalchemy.ext.asyncio import AsyncSession
try:
    from apps.api.app.models import Tenant, User, Base
    from apps.api.app.core.database import engine, AsyncSessionLocal
except ImportError:
    import sys
    import os
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "app")))
    from models import Tenant, User, Base
    from core.database import engine, AsyncSessionLocal
import asyncio

@pytest.mark.asyncio
async def test_rls_tenant_isolation():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
        await conn.execute("SET app.current_tenant_id TO '00000000-0000-0000-0000-000000000001';")
    async with AsyncSessionLocal() as session:
        tenant_a = Tenant(id="00000000-0000-0000-0000-000000000001", name="A", plan="basic")
        tenant_b = Tenant(id="00000000-0000-0000-0000-000000000002", name="B", plan="basic")
        user_a = User(id="00000000-0000-0000-0000-000000000011", email="a@a.com", tenant_id=tenant_a.id, role="admin")
        user_b = User(id="00000000-0000-0000-0000-000000000021", email="b@b.com", tenant_id=tenant_b.id, role="admin")
        session.add_all([tenant_a, tenant_b, user_a, user_b])
        await session.commit()
        # Should only see user_a
        result = await session.execute("SELECT * FROM users;")
        rows = result.fetchall()
        assert len(rows) == 1
        assert rows[0][1] == "a@a.com"
