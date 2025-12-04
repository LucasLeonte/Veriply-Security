import pytest
import uuid
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.models.tenant import Tenant
from app.services.profile_service import (
    get_user_profile,
    update_user_profile,
    upload_avatar_url,
    get_team_members,
    remove_team_member,
    change_team_member_role,
    count_owners_in_tenant
)
from fastapi import HTTPException


@pytest.fixture
async def mock_session(mocker):
    """Mock AsyncSession."""
    session = mocker.MagicMock(spec=AsyncSession)
    return session


@pytest.mark.asyncio
async def test_get_user_profile_success(mocker):
    """Test successful user profile retrieval."""
    user_id = str(uuid.uuid4())
    tenant_id = str(uuid.uuid4())
    
    mock_user = User(
        id=uuid.UUID(user_id),
        email="test@example.com",
        password_hash="hash",
        tenant_id=uuid.UUID(tenant_id),
        role="agent",
        name="Test User",
        avatar_url="https://example.com/avatar.jpg",
        notification_frequency="weekly"
    )
    
    session = mocker.MagicMock(spec=AsyncSession)
    mock_result = mocker.MagicMock()
    mock_result.scalars.return_value.first.return_value = mock_user
    session.execute.return_value = mock_result
    
    user = await get_user_profile(user_id, session)
    
    assert user.email == "test@example.com"
    assert user.name == "Test User"


@pytest.mark.asyncio
async def test_get_user_profile_not_found(mocker):
    """Test get_user_profile when user doesn't exist."""
    user_id = str(uuid.uuid4())
    
    session = mocker.MagicMock(spec=AsyncSession)
    mock_result = mocker.MagicMock()
    mock_result.scalars.return_value.first.return_value = None
    session.execute.return_value = mock_result
    
    with pytest.raises(HTTPException) as exc_info:
        await get_user_profile(user_id, session)
    
    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_update_user_profile_name(mocker):
    """Test updating user name."""
    user_id = str(uuid.uuid4())
    tenant_id = str(uuid.uuid4())
    
    mock_user = User(
        id=uuid.UUID(user_id),
        email="test@example.com",
        password_hash="hash",
        tenant_id=uuid.UUID(tenant_id),
        role="agent",
        name=None,
        notification_frequency="weekly"
    )
    
    session = mocker.MagicMock(spec=AsyncSession)
    mock_result = mocker.MagicMock()
    mock_result.scalars.return_value.first.return_value = mock_user
    session.execute.return_value = mock_result
    session.refresh = mocker.AsyncMock()
    session.add = mocker.MagicMock()
    session.commit = mocker.AsyncMock()
    
    updated_user = await update_user_profile(
        user_id=user_id,
        name="John Doe",
        session=session
    )
    
    assert updated_user.name == "John Doe"
    session.add.assert_called()
    session.commit.assert_called()


@pytest.mark.asyncio
async def test_update_user_profile_invalid_name_length(mocker):
    """Test update with invalid name length."""
    user_id = str(uuid.uuid4())
    tenant_id = str(uuid.uuid4())
    
    mock_user = User(
        id=uuid.UUID(user_id),
        email="test@example.com",
        password_hash="hash",
        tenant_id=uuid.UUID(tenant_id),
        role="agent"
    )
    
    session = mocker.MagicMock(spec=AsyncSession)
    mock_result = mocker.MagicMock()
    mock_result.scalars.return_value.first.return_value = mock_user
    session.execute.return_value = mock_result
    
    with pytest.raises(HTTPException) as exc_info:
        await update_user_profile(
            user_id=user_id,
            name="X",  # Too short
            session=session
        )
    
    assert exc_info.value.status_code == 400


@pytest.mark.asyncio
async def test_remove_team_member_success(mocker):
    """Test successful team member removal."""
    actor_id = str(uuid.uuid4())
    target_id = str(uuid.uuid4())
    tenant_id = str(uuid.uuid4())
    
    mock_actor = User(
        id=uuid.UUID(actor_id),
        email="admin@example.com",
        password_hash="hash",
        tenant_id=uuid.UUID(tenant_id),
        role="owner",
        is_active="active"
    )
    
    mock_target = User(
        id=uuid.UUID(target_id),
        email="member@example.com",
        password_hash="hash",
        tenant_id=uuid.UUID(tenant_id),
        role="agent",
        is_active="active"
    )
    
    session = mocker.MagicMock(spec=AsyncSession)
    mock_result_actor = mocker.MagicMock()
    mock_result_actor.scalars.return_value.first.return_value = mock_actor
    mock_result_target = mocker.MagicMock()
    mock_result_target.scalars.return_value.first.return_value = mock_target
    mock_result_owners = mocker.MagicMock()
    mock_result_owners.scalars.return_value.all.return_value = [mock_actor]
    
    session.execute.side_effect = [mock_result_actor, mock_result_target, mock_result_owners]
    session.add = mocker.MagicMock()
    session.commit = mocker.AsyncMock()
    
    await remove_team_member(
        actor_id=actor_id,
        target_user_id=target_id,
        tenant_id=tenant_id,
        session=session
    )
    
    assert mock_target.is_active == "inactive"


@pytest.mark.asyncio
async def test_remove_team_member_cannot_remove_self(mocker):
    """Test preventing self-removal."""
    user_id = str(uuid.uuid4())
    tenant_id = str(uuid.uuid4())
    
    mock_user = User(
        id=uuid.UUID(user_id),
        email="user@example.com",
        password_hash="hash",
        tenant_id=uuid.UUID(tenant_id),
        role="owner"
    )
    
    session = mocker.MagicMock(spec=AsyncSession)
    mock_result = mocker.MagicMock()
    mock_result.scalars.return_value.first.return_value = mock_user
    session.execute.return_value = mock_result
    
    with pytest.raises(HTTPException) as exc_info:
        await remove_team_member(
            actor_id=user_id,
            target_user_id=user_id,
            tenant_id=tenant_id,
            session=session
        )
    
    assert exc_info.value.status_code == 400


@pytest.mark.asyncio
async def test_change_team_member_role_success(mocker):
    """Test successful role change."""
    actor_id = str(uuid.uuid4())
    target_id = str(uuid.uuid4())
    tenant_id = str(uuid.uuid4())
    
    mock_actor = User(
        id=uuid.UUID(actor_id),
        email="owner@example.com",
        password_hash="hash",
        tenant_id=uuid.UUID(tenant_id),
        role="owner"
    )
    
    mock_target = User(
        id=uuid.UUID(target_id),
        email="member@example.com",
        password_hash="hash",
        tenant_id=uuid.UUID(tenant_id),
        role="agent"
    )
    
    session = mocker.MagicMock(spec=AsyncSession)
    mock_result_actor = mocker.MagicMock()
    mock_result_actor.scalars.return_value.first.return_value = mock_actor
    mock_result_target = mocker.MagicMock()
    mock_result_target.scalars.return_value.first.return_value = mock_target
    
    session.execute.side_effect = [mock_result_actor, mock_result_target]
    session.add = mocker.MagicMock()
    session.commit = mocker.AsyncMock()
    session.refresh = mocker.AsyncMock()
    
    updated_user = await change_team_member_role(
        actor_id=actor_id,
        target_user_id=target_id,
        new_role="admin",
        tenant_id=tenant_id,
        session=session
    )
    
    assert updated_user.role == "admin"


@pytest.mark.asyncio
async def test_change_team_member_role_non_owner_cannot_change(mocker):
    """Test that non-owners cannot change roles."""
    actor_id = str(uuid.uuid4())
    target_id = str(uuid.uuid4())
    tenant_id = str(uuid.uuid4())
    
    mock_actor = User(
        id=uuid.UUID(actor_id),
        email="admin@example.com",
        password_hash="hash",
        tenant_id=uuid.UUID(tenant_id),
        role="admin"  # Not owner
    )
    
    mock_target = User(
        id=uuid.UUID(target_id),
        email="member@example.com",
        password_hash="hash",
        tenant_id=uuid.UUID(tenant_id),
        role="agent"
    )
    
    session = mocker.MagicMock(spec=AsyncSession)
    mock_result_actor = mocker.MagicMock()
    mock_result_actor.scalars.return_value.first.return_value = mock_actor
    mock_result_target = mocker.MagicMock()
    mock_result_target.scalars.return_value.first.return_value = mock_target
    session.execute.side_effect = [mock_result_actor, mock_result_target]
    
    with pytest.raises(HTTPException) as exc_info:
        await change_team_member_role(
            actor_id=actor_id,
            target_user_id=target_id,
            new_role="admin",
            tenant_id=tenant_id,
            session=session
        )
    
    assert exc_info.value.status_code == 403
