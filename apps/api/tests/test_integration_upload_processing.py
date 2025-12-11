import os
import asyncio
import pytest_asyncio
from httpx import AsyncClient
from app.main import app
from app.core.settings import settings
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import select
from app.models.chunk import Chunk
from app.models.tenant import Tenant
from app.models.user import User
from app.models.bot import Bot
import uuid


@pytest_asyncio.fixture
async def setup_test_data():
    """Setup test tenant, user, and bot"""
    os.environ.setdefault("JWT_SECRET", "test-secret-for-integ-tests-should-be-32chars!!")
    
    engine = create_async_engine(settings.get_database_url(), future=True)
    async_session = async_sessionmaker(engine, expire_on_commit=False)
    
    tenant_id = uuid.UUID("00000000-0000-0000-0000-000000000001")
    bot_id = uuid.UUID("00000000-0000-0000-0000-000000000001")
    
    async with async_session() as session:
        # create tenant if not exists
        t = await session.get(Tenant, tenant_id)
        if not t:
            t = Tenant(id=tenant_id, name='test-tenant', plan='dev')
            session.add(t)
            await session.flush()
        
        # create user if not exists
        from sqlalchemy import select
        user_stmt = select(User).where(User.email == 'test@example.com')
        result = await session.execute(user_stmt)
        existing_user = result.scalars().first()
        
        if not existing_user:
            user_id = uuid.uuid4()
            u = User(id=user_id, email='test@example.com', password_hash='x', tenant_id=tenant_id, role='agent')
            session.add(u)
            await session.flush()
        
        # create bot if not exists
        bot = await session.get(Bot, bot_id)
        if not bot:
            b = Bot(id=bot_id, tenant_id=tenant_id, name='test-bot', created_by=existing_user.id if existing_user else user_id)
            session.add(b)
        await session.commit()
    
    await engine.dispose()
    
    return bot_id, tenant_id


async def test_upload_and_background_processing(setup_test_data):
    """End-to-end (async): upload a small text file and assert chunks are created."""
    bot_id, tenant_id = setup_test_data
    
    # Monkeypatch auth dependency to allow upload without real JWT
    def _fake_user():
        return {"sub": None, "id": None}

    def _fake_tenant():
        return tenant_id

    from app.api.v1.auth import get_current_user, get_current_tenant
    app.dependency_overrides[get_current_user] = _fake_user
    app.dependency_overrides[get_current_tenant] = _fake_tenant

    async with AsyncClient(app=app, base_url="http://test") as client:
        file_content = b"Hello world. This is a small document for testing chunking and embedding. " * 5
        files = {"files": ("small.txt", file_content, "text/plain")}
        r = await client.post(f"/api/v1/bots/{bot_id}/documents", files=files)
        assert r.status_code == 201
        body = r.json()
        assert "documents" in body
        doc_id = body["documents"][0]["id"]

        # Wait briefly for background task to run (in-process enqueuer schedules a task)
        await asyncio.sleep(1.0)

    # Query DB for chunks using async session
    engine = create_async_engine(settings.get_database_url(), future=True)
    async_session = async_sessionmaker(engine, expire_on_commit=False)

    async with async_session() as session:
        q = await session.execute(select(Chunk).where(Chunk.document_id == doc_id))
        rows = q.scalars().all()
        assert len(rows) > 0
    
    await engine.dispose()
    
    # Clean up overrides
    app.dependency_overrides.clear()

