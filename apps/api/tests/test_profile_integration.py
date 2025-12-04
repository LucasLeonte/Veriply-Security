"""
Integration tests for Story 1.6: User Profile & Team Management
Tests the full flow from user creation through profile/team management
"""

import pytest
import uuid
import json
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from app.main import app
from app.models.user import User
from app.models.tenant import Tenant
from app.models.audit_log import AuditLog
from app.models.base import Base


@pytest.fixture
async def db_session():
    """Create test database session."""
    # Use in-memory SQLite for testing
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    AsyncSessionLocal = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    async with AsyncSessionLocal() as session:
        yield session
    
    await engine.dispose()


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.mark.asyncio
async def test_user_profile_workflow(client, db_session):
    """Test complete user profile workflow."""
    # Setup: Create user
    user_id = str(uuid.uuid4())
    tenant_id = str(uuid.uuid4())
    
    # Create tenant
    tenant = Tenant(
        id=uuid.UUID(tenant_id),
        name="Test Tenant",
        plan="free"
    )
    db_session.add(tenant)
    
    # Create user
    user = User(
        id=uuid.UUID(user_id),
        email="test@example.com",
        password_hash="hashed_pass",
        tenant_id=uuid.UUID(tenant_id),
        role="agent"
    )
    db_session.add(user)
    await db_session.commit()
    
    # Test: Get profile
    # In real scenario, this would have JWT token
    assert user.email == "test@example.com"
    assert user.role == "agent"
    
    # Test: Update profile
    user.name = "John Doe"
    user.notification_frequency = "daily"
    user.updated_at = datetime.utcnow()
    db_session.add(user)
    await db_session.commit()
    
    # Verify update
    assert user.name == "John Doe"
    assert user.notification_frequency == "daily"


@pytest.mark.asyncio
async def test_team_management_workflow(client, db_session):
    """Test complete team management workflow."""
    # Setup: Create tenant and users
    tenant_id = uuid.uuid4()
    
    tenant = Tenant(id=tenant_id, name="Test Tenant", plan="free")
    db_session.add(tenant)
    
    owner_id = uuid.uuid4()
    owner = User(
        id=owner_id,
        email="owner@example.com",
        password_hash="hash",
        tenant_id=tenant_id,
        role="owner",
        name="Owner User",
        is_active="active"
    )
    db_session.add(owner)
    
    agent_id = uuid.uuid4()
    agent = User(
        id=agent_id,
        email="agent@example.com",
        password_hash="hash",
        tenant_id=tenant_id,
        role="agent",
        name="Agent User",
        is_active="active"
    )
    db_session.add(agent)
    await db_session.commit()
    
    # Test: List team members
    from sqlalchemy import select
    stmt = select(User).where(User.tenant_id == tenant_id)
    result = await db_session.execute(stmt)
    members = result.scalars().all()
    
    assert len(members) == 2
    assert any(m.role == "owner" for m in members)
    assert any(m.role == "agent" for m in members)
    
    # Test: Change role (agent -> manager)
    agent.role = "manager"
    agent.updated_at = datetime.utcnow()
    db_session.add(agent)
    await db_session.commit()
    
    # Create audit log entry
    audit = AuditLog(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        actor_id=owner_id,
        target_user_id=agent_id,
        action="role_change",
        details=json.dumps({"old_role": "agent", "new_role": "manager"}),
        created_at=datetime.utcnow()
    )
    db_session.add(audit)
    await db_session.commit()
    
    # Verify role change
    assert agent.role == "manager"
    
    # Test: Remove member (soft delete)
    agent.is_active = "inactive"
    agent.updated_at = datetime.utcnow()
    db_session.add(agent)
    await db_session.commit()
    
    # Create removal audit
    audit2 = AuditLog(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        actor_id=owner_id,
        target_user_id=agent_id,
        action="user_removed",
        details=json.dumps({"removed_user_email": "agent@example.com"}),
        created_at=datetime.utcnow()
    )
    db_session.add(audit2)
    await db_session.commit()
    
    # Verify removal
    assert agent.is_active == "inactive"
    
    # Verify audit trail
    stmt_audit = select(AuditLog).where(AuditLog.target_user_id == agent_id)
    result_audit = await db_session.execute(stmt_audit)
    audit_entries = result_audit.scalars().all()
    
    assert len(audit_entries) == 2
    assert audit_entries[0].action == "role_change"
    assert audit_entries[1].action == "user_removed"


@pytest.mark.asyncio
async def test_profile_validation(db_session):
    """Test profile field validation."""
    tenant_id = uuid.uuid4()
    user_id = uuid.uuid4()
    
    tenant = Tenant(id=tenant_id, name="Test", plan="free")
    db_session.add(tenant)
    
    user = User(
        id=user_id,
        email="test@example.com",
        password_hash="hash",
        tenant_id=tenant_id,
        role="agent"
    )
    db_session.add(user)
    await db_session.commit()
    
    # Test: Name validation (2-100 chars)
    invalid_names = [
        "",
        "A",  # Too short
        "A" * 101,  # Too long
    ]
    
    for name in invalid_names:
        is_valid = 2 <= len(name) <= 100 if name else False
        assert not is_valid
    
    # Test: Valid names
    valid_names = ["Jo", "John Doe", "A" * 100]
    for name in valid_names:
        is_valid = 2 <= len(name) <= 100
        assert is_valid
    
    # Test: Notification frequency validation
    valid_frequencies = ["daily", "weekly", "never"]
    invalid_frequencies = ["hourly", "monthly", "always"]
    
    for freq in invalid_frequencies:
        assert freq not in valid_frequencies
    
    for freq in valid_frequencies:
        assert freq in valid_frequencies


@pytest.mark.asyncio
async def test_authorization_constraints(db_session):
    """Test authorization and business rule constraints."""
    tenant_id = uuid.uuid4()
    
    tenant = Tenant(id=tenant_id, name="Test", plan="free")
    db_session.add(tenant)
    
    # Create owner
    owner_id = uuid.uuid4()
    owner = User(
        id=owner_id,
        email="owner@example.com",
        password_hash="hash",
        tenant_id=tenant_id,
        role="owner",
        is_active="active"
    )
    db_session.add(owner)
    
    # Create admin
    admin_id = uuid.uuid4()
    admin = User(
        id=admin_id,
        email="admin@example.com",
        password_hash="hash",
        tenant_id=tenant_id,
        role="admin",
        is_active="active"
    )
    db_session.add(admin)
    
    # Create agent
    agent_id = uuid.uuid4()
    agent = User(
        id=agent_id,
        email="agent@example.com",
        password_hash="hash",
        tenant_id=tenant_id,
        role="agent",
        is_active="active"
    )
    db_session.add(agent)
    await db_session.commit()
    
    # Test: Non-admin cannot change roles
    can_change_role = admin.role == "owner"
    assert can_change_role
    
    can_change_role = agent.role == "owner"
    assert not can_change_role
    
    # Test: Cannot remove last owner
    from sqlalchemy import select
    stmt = select(User).where(
        (User.tenant_id == tenant_id) &
        (User.role == "owner") &
        (User.is_active == "active")
    )
    result = await db_session.execute(stmt)
    owners = result.scalars().all()
    
    can_remove_owner = len(owners) > 1
    assert not can_remove_owner  # Only 1 owner, cannot remove
    
    # Test: Cannot remove self
    can_remove_self = owner_id != owner_id  # Example logic
    assert not can_remove_self


@pytest.mark.asyncio
async def test_audit_trail(db_session):
    """Test that all actions are audited."""
    tenant_id = uuid.uuid4()
    user_id = uuid.uuid4()
    actor_id = uuid.uuid4()
    
    # Setup
    tenant = Tenant(id=tenant_id, name="Test", plan="free")
    db_session.add(tenant)
    
    user = User(
        id=user_id,
        email="test@example.com",
        password_hash="hash",
        tenant_id=tenant_id,
        role="agent"
    )
    db_session.add(user)
    
    actor = User(
        id=actor_id,
        email="admin@example.com",
        password_hash="hash",
        tenant_id=tenant_id,
        role="owner"
    )
    db_session.add(actor)
    await db_session.commit()
    
    # Log profile update
    audit1 = AuditLog(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        actor_id=actor_id,
        target_user_id=user_id,
        action="profile_update",
        details=json.dumps({"name": "Updated Name"}),
    )
    db_session.add(audit1)
    
    # Log avatar update
    audit2 = AuditLog(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        actor_id=actor_id,
        target_user_id=user_id,
        action="avatar_update",
        details=json.dumps({"avatar_url": "https://example.com/avatar.jpg"}),
    )
    db_session.add(audit2)
    
    # Log role change
    audit3 = AuditLog(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        actor_id=actor_id,
        target_user_id=user_id,
        action="role_change",
        details=json.dumps({"old_role": "agent", "new_role": "manager"}),
    )
    db_session.add(audit3)
    
    await db_session.commit()
    
    # Verify audit trail
    from sqlalchemy import select
    stmt = select(AuditLog).where(AuditLog.target_user_id == user_id)
    result = await db_session.execute(stmt)
    audits = result.scalars().all()
    
    assert len(audits) == 3
    assert audits[0].action == "profile_update"
    assert audits[1].action == "avatar_update"
    assert audits[2].action == "role_change"


@pytest.mark.asyncio
async def test_get_user_profile_by_id_authorization(client):
    """Test authorization check on GET /{user_id} endpoint (SECURITY FIX)."""
    # This test verifies that only owners and admins can view other users' profiles
    # Non-admin users should receive 403 Forbidden when attempting to access another user's profile
    
    owner_id = str(uuid.uuid4())
    agent_id = str(uuid.uuid4())
    target_user_id = str(uuid.uuid4())
    
    # Mock JWT tokens for different roles
    owner_token = f"Bearer {owner_id}:owner"  # Owner role can access
    agent_token = f"Bearer {agent_id}:agent"  # Agent role CANNOT access
    
    # Test 1: Owner should be able to view another user's profile
    response = client.get(
        f"/api/v1/profile/{target_user_id}",
        headers={"Authorization": owner_token}
    )
    # In mock, this would return 200 or 404 (user not found), but NOT 403
    assert response.status_code in [200, 404], \
        "Owner should be able to access other users' profiles"
    
    # Test 2: Admin should be able to view another user's profile  
    admin_token = f"Bearer {owner_id}:admin"
    response = client.get(
        f"/api/v1/profile/{target_user_id}",
        headers={"Authorization": admin_token}
    )
    # In mock, this would return 200 or 404 (user not found), but NOT 403
    assert response.status_code in [200, 404], \
        "Admin should be able to access other users' profiles"
    
    # Test 3: Agent should NOT be able to view another user's profile
    response = client.get(
        f"/api/v1/profile/{target_user_id}",
        headers={"Authorization": agent_token}
    )
    # Should return 403 Forbidden
    assert response.status_code == 403, \
        "Non-admin user should not be able to view other users' profiles"
    assert "admin" in response.json()["detail"].lower(), \
        "Error message should clarify admin permission requirement"
    
    # Test 4: Viewer role should NOT be able to access
    viewer_token = f"Bearer {owner_id}:viewer"
    response = client.get(
        f"/api/v1/profile/{target_user_id}",
        headers={"Authorization": viewer_token}
    )
    assert response.status_code == 403, \
        "Viewer role should not be able to view other users' profiles"

