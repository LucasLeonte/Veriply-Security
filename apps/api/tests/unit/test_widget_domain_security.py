import pytest
from uuid import uuid4
from httpx import AsyncClient

from app.models.bot import Bot
from app.models.group import Group
from app.models.tenant import Tenant, SubscriptionTier
from app.models import WidgetConfig


@pytest.mark.asyncio
async def test_public_widget_config_respects_whitelist(
    client: AsyncClient, db_session
):
    tenant = Tenant(id=uuid4(), name="Tenant", plan="free", subscription_tier=SubscriptionTier.FREE)
    group = Group(id=uuid4(), tenant_id=tenant.id, name="Group", created_by=uuid4())
    bot = Bot(
        id=uuid4(),
        tenant_id=tenant.id,
        group_id=group.id,
        name="Test Bot",
        description="Desc",
        created_by=uuid4(),
        is_public=True,
    )
    cfg = WidgetConfig(bot_id=bot.id, allowed_domains=["allowed.com"])

    db_session.add_all([tenant, group, bot, cfg])
    await db_session.commit()

    ok = await client.get(
        f"/api/v1/bots/{bot.id}/widget/config",
        headers={"x-embed-origin": "https://allowed.com"},
    )
    assert ok.status_code == 200
    body = ok.json()
    assert body["allowed_domains"] == ["allowed.com"]

    blocked = await client.get(
        f"/api/v1/bots/{bot.id}/widget/config",
        headers={"x-embed-origin": "https://bad.com"},
    )
    assert blocked.status_code == 403
    assert "not authorized" in blocked.json()["detail"].lower()


@pytest.mark.asyncio
async def test_chat_query_blocked_when_domain_not_allowed(
    client: AsyncClient, db_session
):
    tenant = Tenant(id=uuid4(), name="Tenant", plan="free", subscription_tier=SubscriptionTier.FREE)
    group = Group(id=uuid4(), tenant_id=tenant.id, name="Group", created_by=uuid4())
    bot = Bot(
        id=uuid4(),
        tenant_id=tenant.id,
        group_id=group.id,
        name="Test Bot",
        description="Desc",
        created_by=uuid4(),
        is_public=True,
    )
    cfg = WidgetConfig(bot_id=bot.id, allowed_domains=["allowed.com"])

    db_session.add_all([tenant, group, bot, cfg])
    await db_session.commit()

    blocked = await client.post(
        f"/api/v1/bots/{bot.id}/chat/query",
        json={"query": "hi"},
        headers={"x-embed-origin": "https://unauthorized.com"},
    )
    assert blocked.status_code == 403
    assert "not authorized" in blocked.json()["detail"].lower()

    allowed = await client.post(
        f"/api/v1/bots/{bot.id}/chat/query",
        json={"query": "hi"},
        headers={"x-embed-origin": "https://allowed.com"},
    )
    assert allowed.status_code == 200
