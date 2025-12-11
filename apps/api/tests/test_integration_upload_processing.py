import os
import time
import asyncio
from fastapi.testclient import TestClient
from app.main import app
from app.core.settings import settings
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import select
from app.models.chunk import Chunk
from app.models.tenant import Tenant
from app.models.user import User
from app.models.bot import Bot
import uuid


def test_upload_and_background_processing(tmp_path, monkeypatch):
    """End-to-end (sync): upload a small text file and assert chunks are created."""
    os.environ.setdefault("JWT_SECRET", "test-secret-for-integ-tests-should-be-32chars!!")

    # Monkeypatch auth dependency to allow upload without real JWT
    def _fake_user():
        return {"sub": None, "id": None}

    def _fake_tenant():
        return settings.DEFAULT_TENANT_ID if hasattr(settings, 'DEFAULT_TENANT_ID') else "00000000-0000-0000-0000-000000000001"

    try:
        from app.api.v1.auth import get_current_user, get_current_tenant
        app.dependency_overrides[get_current_user] = _fake_user
        app.dependency_overrides[get_current_tenant] = _fake_tenant
    except Exception:
        pass

    # Ensure tenant, user, and bot exist in DB for FK constraints
    engine = create_async_engine(settings.get_database_url(), future=True)
    async_session = async_sessionmaker(engine, expire_on_commit=False)

    bot_id = "00000000-0000-0000-0000-000000000001"

    async def _setup_fixture():
        async with async_session() as session:
            tenant_id = uuid.UUID(_fake_tenant())
            # create tenant if not exists
            t = await session.get(Tenant, tenant_id)
            if not t:
                t = Tenant(id=tenant_id, name='test-tenant', plan='dev')
                session.add(t)
            # create user
            user_id = uuid.uuid4()
            u = User(id=user_id, email='test@example.com', password_hash='x', tenant_id=tenant_id, role='agent')
            session.add(u)
            # create bot
            bot = await session.get(Bot, uuid.UUID(bot_id))
            if not bot:
                b = Bot(id=uuid.UUID(bot_id), tenant_id=tenant_id, name='test-bot', created_by=user_id)
                session.add(b)
            await session.commit()

    asyncio.get_event_loop().run_until_complete(_setup_fixture())

    with TestClient(app) as client:
        file_content = b"Hello world. This is a small document for testing chunking and embedding. " * 5
        files = {"file": ("small.txt", file_content, "text/plain")}
        bot_id = "00000000-0000-0000-0000-000000000001"
        r = client.post(f"/api/v1/bots/{bot_id}/documents", files=files)
        assert r.status_code == 201
        body = r.json()
        assert "document_id" in body
        doc_id = body["document_id"]

        # Wait briefly for background task to run (in-process enqueuer schedules a task)
        time.sleep(1.0)

    # Query DB for chunks using async session
    engine = create_async_engine(settings.get_database_url(), future=True)
    async_session = async_sessionmaker(engine, expire_on_commit=False)

    async def _check():
        async with async_session() as session:
            q = await session.execute(select(Chunk).where(Chunk.document_id == doc_id))
            rows = q.scalars().all()
            assert len(rows) > 0

    asyncio.get_event_loop().run_until_complete(_check())


