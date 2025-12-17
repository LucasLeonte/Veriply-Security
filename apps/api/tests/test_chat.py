"""Tests for chat endpoints."""

import pytest
from uuid import uuid4
from httpx import AsyncClient
from app.models.bot import Bot
from app.models.group import Group
from app.models.tenant import Tenant


@pytest.mark.asyncio
async def test_get_public_bot_info_success(client: AsyncClient, test_db_session):
    """Test retrieving public bot information."""
    # Create test data
    tenant = Tenant(id=uuid4(), name="Test Tenant")
    group = Group(
        id=uuid4(),
        tenant_id=tenant.id,
        name="Test Group",
        created_by=uuid4(),
    )
    bot = Bot(
        id=uuid4(),
        tenant_id=tenant.id,
        group_id=group.id,
        name="Test Bot",
        description="Test bot for chat",
        created_by=uuid4(),
    )

    test_db_session.add(tenant)
    test_db_session.add(group)
    test_db_session.add(bot)
    await test_db_session.commit()

    # Make request
    response = await client.get(f"/api/v1/bots/{bot.id}/public")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(bot.id)
    assert data["name"] == "Test Bot"
    assert data["welcome_message"] == "Test bot for chat"
    assert data["is_public"] is True


@pytest.mark.asyncio
async def test_get_public_bot_info_not_found(client: AsyncClient):
    """Test retrieving non-existent bot returns 404."""
    fake_bot_id = uuid4()
    response = await client.get(f"/api/v1/bots/{fake_bot_id}/public")

    assert response.status_code == 404
    assert response.json()["detail"] == "Bot not found"


@pytest.mark.asyncio
async def test_chat_query_empty_query(client: AsyncClient, test_db_session):
    """Test chat query with empty query returns 400."""
    # Create test bot
    tenant = Tenant(id=uuid4(), name="Test Tenant")
    group = Group(
        id=uuid4(),
        tenant_id=tenant.id,
        name="Test Group",
        created_by=uuid4(),
    )
    bot = Bot(
        id=uuid4(),
        tenant_id=tenant.id,
        group_id=group.id,
        name="Test Bot",
        description="Test bot",
        created_by=uuid4(),
    )

    test_db_session.add(tenant)
    test_db_session.add(group)
    test_db_session.add(bot)
    await test_db_session.commit()

    # Make request with empty query
    response = await client.post(
        f"/api/v1/bots/{bot.id}/chat/query",
        json={"query": ""},
    )

    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_chat_query_too_long(client: AsyncClient, test_db_session):
    """Test chat query with too long query returns 400."""
    # Create test bot
    tenant = Tenant(id=uuid4(), name="Test Tenant")
    group = Group(
        id=uuid4(),
        tenant_id=tenant.id,
        name="Test Group",
        created_by=uuid4(),
    )
    bot = Bot(
        id=uuid4(),
        tenant_id=tenant.id,
        group_id=group.id,
        name="Test Bot",
        description="Test bot",
        created_by=uuid4(),
    )

    test_db_session.add(tenant)
    test_db_session.add(group)
    test_db_session.add(bot)
    await test_db_session.commit()

    # Make request with overly long query
    long_query = "a" * 5001
    response = await client.post(
        f"/api/v1/bots/{bot.id}/chat/query",
        json={"query": long_query},
    )

    assert response.status_code == 400
    assert "too long" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_chat_query_bot_not_found(client: AsyncClient):
    """Test chat query with non-existent bot returns 404."""
    fake_bot_id = uuid4()
    response = await client.post(
        f"/api/v1/bots/{fake_bot_id}/chat/query",
        json={"query": "Hello"},
    )

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_chat_query_streams_response(client: AsyncClient, test_db_session):
    """Test chat query returns SSE stream."""
    # Create test bot with documents
    tenant = Tenant(id=uuid4(), name="Test Tenant")
    group = Group(
        id=uuid4(),
        tenant_id=tenant.id,
        name="Test Group",
        created_by=uuid4(),
    )
    bot = Bot(
        id=uuid4(),
        tenant_id=tenant.id,
        group_id=group.id,
        name="Test Bot",
        description="Test bot",
        created_by=uuid4(),
    )

    test_db_session.add(tenant)
    test_db_session.add(group)
    test_db_session.add(bot)
    await test_db_session.commit()

    # Make request
    response = await client.post(
        f"/api/v1/bots/{bot.id}/chat/query",
        json={"query": "What is the weather?"},
    )

    # Should return 200 with SSE content type
    assert response.status_code == 200
    assert "text/event-stream" in response.headers["content-type"]

    # Parse SSE stream
    content = response.text
    assert "data:" in content  # SSE format


@pytest.mark.asyncio
async def test_chat_query_with_conversation_history(
    client: AsyncClient, test_db_session
):
    """Test chat query with conversation history."""
    # Create test bot
    tenant = Tenant(id=uuid4(), name="Test Tenant")
    group = Group(
        id=uuid4(),
        tenant_id=tenant.id,
        name="Test Group",
        created_by=uuid4(),
    )
    bot = Bot(
        id=uuid4(),
        tenant_id=tenant.id,
        group_id=group.id,
        name="Test Bot",
        description="Test bot",
        created_by=uuid4(),
    )

    test_db_session.add(tenant)
    test_db_session.add(group)
    test_db_session.add(bot)
    await test_db_session.commit()

    # Make request with conversation history
    response = await client.post(
        f"/api/v1/bots/{bot.id}/chat/query",
        json={
            "query": "What did I just ask?",
            "conversation_history": [
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi there!"},
            ],
        },
    )

    assert response.status_code == 200
