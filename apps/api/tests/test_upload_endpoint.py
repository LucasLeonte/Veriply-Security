import io
import pytest
from fastapi.testclient import TestClient
from app.main import app
from uuid import uuid4


class FakeUser:
    def __init__(self, id, tenant_id):
        self.id = id
        self.tenant_id = tenant_id


class FakeAsyncSession:
    async def flush(self):
        return None

    async def commit(self):
        return None

    def add(self, obj):
        # simulate SQLAlchemy add
        self._last = obj


@pytest.fixture(autouse=True)
def override_dependencies():
    # Override auth and DB dependencies to return a fake user and tenant
    test_user = FakeUser(id=uuid4(), tenant_id=uuid4())

    async def _get_current_user():
        return test_user

    async def _get_current_tenant():
        return test_user.tenant_id

    async def _get_db():
        yield FakeAsyncSession()

    # Use FastAPI's dependency_overrides to replace the original dependency callables
    from app.api.v1.auth import get_current_user as orig_get_current_user, get_current_tenant as orig_get_current_tenant
    from app.core.database import get_db as orig_get_db

    app.dependency_overrides = {
        orig_get_current_user: _get_current_user,
        orig_get_current_tenant: _get_current_tenant,
        orig_get_db: _get_db,
    }


def test_upload_endpoint_monkeypatched(monkeypatch):
    # Patch storage.upload_bytes to avoid MinIO
    monkeypatch.setattr("app.lib.storage.upload_bytes", lambda path, data, content_type=None: f"file://{path}")

    client = TestClient(app)

    # create a sample file
    file_content = b"hello world"
    files = {"file": ("test.txt", io.BytesIO(file_content), "text/plain")}

    # Use a random bot_id (BotService.get_bot is used to validate bot; patch it to return truthy)
    async def _fake_get_bot(db, bot_id, tenant_id):
        return True

    monkeypatch.setattr("app.services.bot_service.BotService.get_bot", _fake_get_bot)

    resp = client.post(f"/api/v1/bots/{uuid4()}/documents", files=files)
    assert resp.status_code == 201
    body = resp.json()
    assert body.get("queued") is True
    assert "document_id" in body
