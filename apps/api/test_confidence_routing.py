import uuid
import pytest
from sqlalchemy import select

from app.api.v1.auth import get_current_user, get_current_tenant
from app.main import app as fastapi_app
from app.api.v1 import query as confidence_query_module
from app.models.bot import Bot, BotStatus
from app.models.confidence_log import ConfidenceLog, RoutingDecision
from app.models.tenant import Tenant
from app.models.user import User
from app.services.vector_search_service import SearchResult, VectorSearchService


async def _seed_bot(db_session):
    tenant_id = uuid.uuid4()
    user_id = uuid.uuid4()
    bot_id = uuid.uuid4()

    tenant = Tenant(id=tenant_id, name="Test Tenant", plan="free")
    user = User(
        id=user_id,
        email="test@example.com",
        password_hash="hashed",
        tenant_id=tenant_id,
        role="admin",
    )
    bot = Bot(
        id=bot_id,
        tenant_id=tenant_id,
        group_id=None,
        name="Test Bot",
        description="",
        confidence_threshold=80,
        status=BotStatus.READY,
        created_by=user_id,
    )

    db_session.add_all([tenant, user, bot])
    await db_session.commit()
    return bot, tenant_id, user_id


@pytest.mark.asyncio
async def test_confidence_auto_send(monkeypatch, client, db_session):
    # Ensure confidence router is registered (idempotent include)
    if not any("/api/v1/confidence" in r.path for r in fastapi_app.router.routes):
        fastapi_app.include_router(confidence_query_module.router)
    bot, tenant_id, user_id = await _seed_bot(db_session)

    fastapi_app.dependency_overrides[get_current_user] = lambda: {
        "sub": str(user_id),
        "tenant_id": str(tenant_id),
    }
    fastapi_app.dependency_overrides[get_current_tenant] = lambda: tenant_id

    async def fake_search(self, db, bot_id, tenant_id, query, k, similarity_threshold=0.5):
        results = [
            SearchResult(
                chunk_id="c1",
                document_id="d1",
                document_name="Doc1",
                section=None,
                text="content",
                similarity=0.95,
                position=0,
            ),
            SearchResult(
                chunk_id="c2",
                document_id="d2",
                document_name="Doc2",
                section=None,
                text="content",
                similarity=0.92,
                position=1,
            ),
        ]
        return results, 5

    monkeypatch.setattr(VectorSearchService, "search", fake_search)

    response = await client.post(
        f"/api/v1/confidence/bots/{bot.id}/query",
        json={"query": "hi", "k": 2},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "auto_sent"
    assert data["routing_info"]["decision"] == RoutingDecision.AUTO_SEND.value
    assert data["confidence"]["overall_confidence"] >= 80

    logs = (await db_session.execute(select(ConfidenceLog))).scalars().all()
    assert len(logs) == 1
    assert logs[0].routing_decision == RoutingDecision.AUTO_SEND


@pytest.mark.asyncio
async def test_confidence_hitl_low_score(monkeypatch, client, db_session):
    bot, tenant_id, user_id = await _seed_bot(db_session)

    fastapi_app.dependency_overrides[get_current_user] = lambda: {
        "sub": str(user_id),
        "tenant_id": str(tenant_id),
    }
    fastapi_app.dependency_overrides[get_current_tenant] = lambda: tenant_id

    async def fake_search(self, db, bot_id, tenant_id, query, k, similarity_threshold=0.5):
        results = [
            SearchResult(
                chunk_id="c1",
                document_id="d1",
                document_name="Doc1",
                section=None,
                text="content",
                similarity=0.2,
                position=0,
            )
        ]
        return results, 7

    monkeypatch.setattr(VectorSearchService, "search", fake_search)

    response = await client.post(
        f"/api/v1/confidence/bots/{bot.id}/query",
        json={"query": "hi"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "hitl_required"
    assert data["routing_info"]["decision"] == RoutingDecision.HITL.value
    assert data["confidence"]["overall_confidence"] < 80
    assert data["routing_info"].get("end_user_message")

    logs = (await db_session.execute(select(ConfidenceLog))).scalars().all()
    assert len(logs) == 1
    assert logs[0].routing_decision == RoutingDecision.HITL


@pytest.mark.asyncio
async def test_confidence_verified_kb_boost(monkeypatch, client, db_session):
    bot, tenant_id, user_id = await _seed_bot(db_session)

    fastapi_app.dependency_overrides[get_current_user] = lambda: {
        "sub": str(user_id),
        "tenant_id": str(tenant_id),
    }
    fastapi_app.dependency_overrides[get_current_tenant] = lambda: tenant_id

    async def fake_search(self, db, bot_id, tenant_id, query, k, similarity_threshold=0.5):
        results = [
            SearchResult(
                chunk_id="c1",
                document_id="d1",
                document_name="Doc1",
                section=None,
                text="content",
                similarity=0.6,
                position=0,
                is_verified=True,
            )
        ]
        return results, 6

    monkeypatch.setattr(VectorSearchService, "search", fake_search)

    response = await client.post(
        f"/api/v1/confidence/bots/{bot.id}/query",
        json={"query": "hi"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "auto_sent"
    assert data["routing_info"]["decision"] == RoutingDecision.AUTO_SEND.value
    assert data["confidence"]["overall_confidence"] >= 95

    logs = (await db_session.execute(select(ConfidenceLog))).scalars().all()
    assert len(logs) == 1
    assert logs[0].is_verified_kb is True


@pytest.mark.asyncio
async def test_confidence_no_context_routes_hitl(monkeypatch, client, db_session):
    bot, tenant_id, user_id = await _seed_bot(db_session)

    fastapi_app.dependency_overrides[get_current_user] = lambda: {
        "sub": str(user_id),
        "tenant_id": str(tenant_id),
    }
    fastapi_app.dependency_overrides[get_current_tenant] = lambda: tenant_id

    async def fake_search(self, db, bot_id, tenant_id, query, k, similarity_threshold=0.5):
        return [], 4

    monkeypatch.setattr(VectorSearchService, "search", fake_search)

    response = await client.post(
        f"/api/v1/confidence/bots/{bot.id}/query",
        json={"query": "hi"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "hitl_required"
    assert data["routing_info"]["decision"] == RoutingDecision.HITL.value
    assert data["confidence"]["overall_confidence"] == 0
    assert data["routing_info"].get("end_user_message")

    logs = (await db_session.execute(select(ConfidenceLog))).scalars().all()
    assert len(logs) == 1
    assert logs[0].overall_confidence <= 0.3


@pytest.mark.asyncio
async def test_confidence_threshold_override_allows_auto_send(monkeypatch, client, db_session):
    bot, tenant_id, user_id = await _seed_bot(db_session)

    fastapi_app.dependency_overrides[get_current_user] = lambda: {
        "sub": str(user_id),
        "tenant_id": str(tenant_id),
    }
    fastapi_app.dependency_overrides[get_current_tenant] = lambda: tenant_id

    async def fake_search(self, db, bot_id, tenant_id, query, k, similarity_threshold=0.5):
        results = [
            SearchResult(
                chunk_id="c1",
                document_id="d1",
                document_name="Doc1",
                section=None,
                text="content",
                similarity=0.9,
                position=0,
            )
        ]
        return results, 5

    monkeypatch.setattr(VectorSearchService, "search", fake_search)

    response = await client.post(
        f"/api/v1/confidence/bots/{bot.id}/query",
        json={"query": "hi", "confidence_threshold": 0.5},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "auto_sent"
    assert data["routing_info"]["decision"] == RoutingDecision.AUTO_SEND.value
    assert data["routing_info"]["threshold_used"] == 0.5

    logs = (await db_session.execute(select(ConfidenceLog))).scalars().all()
    assert len(logs) == 1
    assert logs[0].routing_decision == RoutingDecision.AUTO_SEND