"""Security tests for HITL review interface endpoints."""

import pytest
import pytest_asyncio
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch
from fastapi import status

from app.models.confidence_log import ConfidenceLog, RoutingDecision
from app.models.bot import Bot
from app.models.group_member import GroupMember, GroupRole
from app.models.group import Group
from app.models.tenant import Tenant
from app.models.user import User


@pytest_asyncio.fixture
async def test_tenant(db_session):
    """Create a test tenant."""
    tenant = Tenant(
        id=uuid.uuid4(),
        name="Test Tenant",
        plan="test",
    )
    db_session.add(tenant)
    await db_session.commit()
    await db_session.refresh(tenant)
    return tenant


@pytest_asyncio.fixture
async def test_user(db_session, test_tenant):
    """Create a test user."""
    user = User(
        id=uuid.uuid4(),
        tenant_id=test_tenant.id,
        email="test@example.com",
        name="Test User",
        password_hash="hashed_password",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def test_bot(db_session, test_tenant):
    """Create a test bot."""
    bot = Bot(
        id=uuid.uuid4(),
        tenant_id=test_tenant.id,
        name="Test Bot",
        confidence_threshold=0.8,
    )
    db_session.add(bot)
    await db_session.commit()
    await db_session.refresh(bot)
    return bot


@pytest.fixture
def auth_headers(test_user):
    """Create authorization headers with mock JWT."""
    return {
        "Authorization": f"Bearer mock_token_for_{test_user.id}",
        "X-User-ID": str(test_user.id),
    }


@pytest.mark.asyncio
async def test_get_queue_item_cross_group_access_denied(db_session, client, test_tenant, test_user, test_bot, auth_headers):
    """Test that users cannot access HITL items from groups they don't belong to."""
    # Create a group the user is NOT a member of
    other_group = Group(
        id=uuid.uuid4(),
        tenant_id=test_tenant.id,
        name="Other Group",
    )
    db_session.add(other_group)
    
    # Create HITL item in that group
    item = ConfidenceLog(
        id=uuid.uuid4(),
        bot_id=test_bot.id,
        tenant_id=test_tenant.id,
        group_id=other_group.id,
        query_id=uuid.uuid4(),
        query_text="Test question",
        retrieval_confidence=0.5,
        overall_confidence=0.5,
        threshold_used=0.8,
        routing_decision=RoutingDecision.HITL,
        hitl_resolved=False,
        created_at=datetime.now(timezone.utc),
        metadata_json={"ai_draft": "Test draft"},
    )
    db_session.add(item)
    await db_session.commit()
    
    response = await client.get(
        f"/api/v1/hitl/queue/{item.id}",
        headers=auth_headers,
    )
    
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert "access denied" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_approve_cross_group_access_denied(db_session, client, test_tenant, test_user, test_bot, auth_headers):
    """Test that users cannot approve HITL items from groups they don't belong to."""
    # Create a group the user is NOT a member of
    other_group = Group(
        id=uuid.uuid4(),
        tenant_id=test_tenant.id,
        name="Other Group",
    )
    db_session.add(other_group)
    
    # Create HITL item in that group
    item = ConfidenceLog(
        id=uuid.uuid4(),
        bot_id=test_bot.id,
        tenant_id=test_tenant.id,
        group_id=other_group.id,
        query_id=uuid.uuid4(),
        query_text="Test question",
        retrieval_confidence=0.5,
        overall_confidence=0.5,
        threshold_used=0.8,
        routing_decision=RoutingDecision.HITL,
        hitl_resolved=False,
        created_at=datetime.now(timezone.utc),
        metadata_json={"ai_draft": "Test draft"},
    )
    db_session.add(item)
    await db_session.commit()
    
    with patch('app.api.routes.hitl.aioredis.from_url', return_value=AsyncMock()):
        response = await client.post(
            f"/api/v1/hitl/queue/{item.id}/approve",
            headers=auth_headers,
            json={"edits": "Edited draft"},
        )
    
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert "access denied" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_reject_cross_group_access_denied(db_session, client, test_tenant, test_user, test_bot, auth_headers):
    """Test that users cannot reject HITL items from groups they don't belong to."""
    # Create a group the user is NOT a member of
    other_group = Group(
        id=uuid.uuid4(),
        tenant_id=test_tenant.id,
        name="Other Group",
    )
    db_session.add(other_group)
    
    # Create HITL item in that group
    item = ConfidenceLog(
        id=uuid.uuid4(),
        bot_id=test_bot.id,
        tenant_id=test_tenant.id,
        group_id=other_group.id,
        query_id=uuid.uuid4(),
        query_text="Test question",
        retrieval_confidence=0.5,
        overall_confidence=0.5,
        threshold_used=0.8,
        routing_decision=RoutingDecision.HITL,
        hitl_resolved=False,
        created_at=datetime.now(timezone.utc),
        metadata_json={"ai_draft": "Test draft"},
    )
    db_session.add(item)
    await db_session.commit()
    
    with patch('app.api.routes.hitl.aioredis.from_url', return_value=AsyncMock()):
        response = await client.post(
            f"/api/v1/hitl/queue/{item.id}/reject",
            headers=auth_headers,
            json={"reason": "Rejection reason"},
        )
    
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert "access denied" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_approve_already_resolved_conflict(db_session, client, test_tenant, test_user, test_bot, auth_headers):
    """Test that approving an already-resolved item returns 409 Conflict."""
    # Create a group and add user as member
    group = Group(
        id=uuid.uuid4(),
        tenant_id=test_tenant.id,
        name="Test Group",
    )
    db_session.add(group)
    
    membership = GroupMember(
        id=uuid.uuid4(),
        group_id=group.id,
        user_id=test_user.id,
        role=GroupRole.MANAGER,
        invited_at=datetime.now(timezone.utc),
    )
    db_session.add(membership)
    
    # Create already-resolved HITL item
    other_user_id = uuid.uuid4()
    item = ConfidenceLog(
        id=uuid.uuid4(),
        bot_id=test_bot.id,
        tenant_id=test_tenant.id,
        group_id=group.id,
        query_id=uuid.uuid4(),
        query_text="Test question",
        retrieval_confidence=0.5,
        overall_confidence=0.5,
        threshold_used=0.8,
        routing_decision=RoutingDecision.HITL,
        hitl_resolved=True,  # Already resolved
        resolution_user_id=other_user_id,
        resolution_timestamp=datetime.now(timezone.utc),
        created_at=datetime.now(timezone.utc),
        metadata_json={"ai_draft": "Test draft"},
    )
    db_session.add(item)
    await db_session.commit()
    
    response = await client.post(
        f"/api/v1/hitl/queue/{item.id}/approve",
        headers=auth_headers,
        json={"edits": "Edited draft"},
    )
    
    assert response.status_code == status.HTTP_409_CONFLICT
    assert "already been resolved" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_approve_with_empty_edits_rejected(db_session, client, test_tenant, test_user, test_bot, auth_headers):
    """Test that approving with empty/whitespace-only edits returns 400."""
    # Create a group and add user as member
    group = Group(
        id=uuid.uuid4(),
        tenant_id=test_tenant.id,
        name="Test Group",
    )
    db_session.add(group)
    
    membership = GroupMember(
        id=uuid.uuid4(),
        group_id=group.id,
        user_id=test_user.id,
        role=GroupRole.MANAGER,
        invited_at=datetime.now(timezone.utc),
    )
    db_session.add(membership)
    
    # Create HITL item
    item = ConfidenceLog(
        id=uuid.uuid4(),
        bot_id=test_bot.id,
        tenant_id=test_tenant.id,
        group_id=group.id,
        query_id=uuid.uuid4(),
        query_text="Test question",
        retrieval_confidence=0.5,
        overall_confidence=0.5,
        threshold_used=0.8,
        routing_decision=RoutingDecision.HITL,
        hitl_resolved=False,
        created_at=datetime.now(timezone.utc),
        metadata_json={"ai_draft": "Test draft"},
    )
    db_session.add(item)
    await db_session.commit()
    
    response = await client.post(
        f"/api/v1/hitl/queue/{item.id}/approve",
        headers=auth_headers,
        json={"edits": "   "},  # Only whitespace
    )
    
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "cannot be empty" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_approve_with_oversized_edits_rejected(db_session, client, test_tenant, test_user, test_bot, auth_headers):
    """Test that approving with excessively long edits returns 400."""
    # Create a group and add user as member
    group = Group(
        id=uuid.uuid4(),
        tenant_id=test_tenant.id,
        name="Test Group",
    )
    db_session.add(group)
    
    membership = GroupMember(
        id=uuid.uuid4(),
        group_id=group.id,
        user_id=test_user.id,
        role=GroupRole.MANAGER,
        invited_at=datetime.now(timezone.utc),
    )
    db_session.add(membership)
    
    # Create HITL item
    item = ConfidenceLog(
        id=uuid.uuid4(),
        bot_id=test_bot.id,
        tenant_id=test_tenant.id,
        group_id=group.id,
        query_id=uuid.uuid4(),
        query_text="Test question",
        retrieval_confidence=0.5,
        overall_confidence=0.5,
        threshold_used=0.8,
        routing_decision=RoutingDecision.HITL,
        hitl_resolved=False,
        created_at=datetime.now(timezone.utc),
        metadata_json={"ai_draft": "Test draft"},
    )
    db_session.add(item)
    await db_session.commit()
    
    response = await client.post(
        f"/api/v1/hitl/queue/{item.id}/approve",
        headers=auth_headers,
        json={"edits": "x" * 10001},  # Exceeds 10000 char limit
    )
    
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "exceeds maximum length" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_approve_with_valid_group_membership_succeeds(db_session, client, test_tenant, test_user, test_bot, auth_headers):
    """Test that users with valid group membership can approve items."""
    # Create a group and add user as member
    group = Group(
        id=uuid.uuid4(),
        tenant_id=test_tenant.id,
        name="Test Group",
    )
    db_session.add(group)
    
    membership = GroupMember(
        id=uuid.uuid4(),
        group_id=group.id,
        user_id=test_user.id,
        role=GroupRole.MANAGER,
        invited_at=datetime.now(timezone.utc),
    )
    db_session.add(membership)
    
    # Create HITL item
    item = ConfidenceLog(
        id=uuid.uuid4(),
        bot_id=test_bot.id,
        tenant_id=test_tenant.id,
        group_id=group.id,
        query_id=uuid.uuid4(),
        query_text="Test question",
        retrieval_confidence=0.5,
        overall_confidence=0.5,
        threshold_used=0.8,
        routing_decision=RoutingDecision.HITL,
        hitl_resolved=False,
        created_at=datetime.now(timezone.utc),
        metadata_json={"ai_draft": "Test draft"},
    )
    db_session.add(item)
    await db_session.commit()
    
    with patch('app.api.routes.hitl.aioredis.from_url', return_value=AsyncMock()):
        response = await client.post(
            f"/api/v1/hitl/queue/{item.id}/approve",
            headers=auth_headers,
            json={"edits": "Valid edited draft"},
        )
    
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["status"] == "approved"
