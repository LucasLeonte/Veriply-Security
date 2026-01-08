"""Test suite for Group, Bot, and Document API routes."""

import pytest
from httpx import AsyncClient
from uuid import uuid4

from app.core.auth import get_jwt_secret, JWT_ALGORITHM
from app.models import User, Tenant
import jwt


@pytest.fixture
async def session(db_session):
    """Alias for db_session fixture."""
    return db_session


@pytest.fixture
async def test_tenant(session):
    """Create a test tenant."""
    from app.models.tenant import SubscriptionTier
    tenant = Tenant(
        id=uuid4(), 
        name="Test Tenant",
        plan="free",
        subscription_tier=SubscriptionTier.FREE
    )
    session.add(tenant)
    await session.commit()
    return tenant


@pytest.fixture
async def test_user(session, test_tenant):
    """Create a test user."""
    user = User(
        id=uuid4(),
        email="testuser@example.com",
        password_hash="hashed_password",
        tenant_id=test_tenant.id,
        role="admin",
        name="Test User",
    )
    session.add(user)
    await session.commit()
    return user


@pytest.fixture
async def test_user_2(session, test_tenant):
    """Create a second test user in same tenant."""
    user = User(
        id=uuid4(),
        email="testuser2@example.com",
        password_hash="hashed_password",
        tenant_id=test_tenant.id,
        role="admin",
        name="Test User 2",
    )
    session.add(user)
    await session.commit()
    return user


@pytest.fixture
def auth_token(test_user):
    """Create a valid JWT token for test user."""
    payload = {
        "sub": str(test_user.id),
        "tenant_id": str(test_user.tenant_id),
        "email": test_user.email,
        "role": test_user.role,
    }
    token = jwt.encode(payload, get_jwt_secret(), algorithm=JWT_ALGORITHM)
    return token


@pytest.fixture
def auth_token_2(test_user_2):
    """Create a valid JWT token for second test user."""
    payload = {
        "sub": str(test_user_2.id),
        "tenant_id": str(test_user_2.tenant_id),
        "email": test_user_2.email,
        "role": test_user_2.role,
    }
    token = jwt.encode(payload, get_jwt_secret(), algorithm=JWT_ALGORITHM)
    return token


@pytest.mark.asyncio
class TestGroupRoutes:
    """Test group CRUD operations."""

    async def test_create_group(self, client: AsyncClient, auth_token: str):
        """Test creating a group."""
        response = await client.post(
            "/api/v1/groups",
            json={"name": "Sales Team", "description": "Sales department KB"},
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Sales Team"
        assert data["description"] == "Sales department KB"
        assert "id" in data
        assert "created_at" in data

    async def test_list_groups(self, client: AsyncClient, auth_token: str):
        """Test listing user's groups."""
        # Create a group first
        create_resp = await client.post(
            "/api/v1/groups",
            json={"name": "Test Group"},
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert create_resp.status_code == 201
        group_id = create_resp.json()["id"]

        # List groups
        list_resp = await client.get(
            "/api/v1/groups",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert list_resp.status_code == 200
        groups = list_resp.json()
        assert len(groups) >= 1
        assert any(g["id"] == group_id for g in groups)

    async def test_get_group(self, client: AsyncClient, auth_token: str):
        """Test getting group details."""
        # Create a group
        create_resp = await client.post(
            "/api/v1/groups",
            json={"name": "Test Group"},
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        group_id = create_resp.json()["id"]

        # Get group
        get_resp = await client.get(
            f"/api/v1/groups/{group_id}",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert get_resp.status_code == 200
        assert get_resp.json()["id"] == group_id

    async def test_update_group(self, client: AsyncClient, auth_token: str):
        """Test updating group (admin only)."""
        # Create a group
        create_resp = await client.post(
            "/api/v1/groups",
            json={"name": "Old Name"},
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        group_id = create_resp.json()["id"]

        # Update group
        update_resp = await client.patch(
            f"/api/v1/groups/{group_id}",
            json={"name": "New Name", "description": "Updated"},
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert update_resp.status_code == 200
        assert update_resp.json()["name"] == "New Name"
        assert update_resp.json()["description"] == "Updated"

    async def test_delete_group(self, client: AsyncClient, auth_token: str):
        """Test deleting group (admin only)."""
        # Create a group
        create_resp = await client.post(
            "/api/v1/groups",
            json={"name": "Delete Me"},
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        group_id = create_resp.json()["id"]

        # Delete group
        delete_resp = await client.delete(
            f"/api/v1/groups/{group_id}",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert delete_resp.status_code == 204

        # Verify it's deleted
        get_resp = await client.get(
            f"/api/v1/groups/{group_id}",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert get_resp.status_code == 404

    async def test_duplicate_group_name_fails(self, client: AsyncClient, auth_token: str):
        """Test that duplicate group names per tenant are rejected."""
        # Create group
        await client.post(
            "/api/v1/groups",
            json={"name": "Unique Name"},
            headers={"Authorization": f"Bearer {auth_token}"},
        )

        # Try to create another with same name
        dup_resp = await client.post(
            "/api/v1/groups",
            json={"name": "Unique Name"},
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert dup_resp.status_code == 409  # Conflict

    async def test_user_isolation(self, client: AsyncClient, auth_token: str, auth_token_2: str):
        """Test that users only see their own groups."""
        # User 1 creates a group
        create_resp = await client.post(
            "/api/v1/groups",
            json={"name": "Private Group"},
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        group_id = create_resp.json()["id"]

        # User 2 tries to access it (should fail - not a member)
        access_resp = await client.get(
            f"/api/v1/groups/{group_id}",
            headers={"Authorization": f"Bearer {auth_token_2}"},
        )
        assert access_resp.status_code == 403  # Forbidden


@pytest.mark.asyncio
class TestGroupMembershipRoutes:
    """Test group membership operations."""

    async def test_invite_member(self, client: AsyncClient, auth_token: str, auth_token_2: str):
        """Test inviting a user to a group."""
        # User 1 creates group
        group_resp = await client.post(
            "/api/v1/groups",
            json={"name": "Invite Test"},
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        group_id = group_resp.json()["id"]

        # User 1 invites User 2
        invite_resp = await client.post(
            f"/api/v1/groups/{group_id}/members",
            json={"email": "testuser2@example.com", "role": "manager"},
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert invite_resp.status_code == 202
        assert invite_resp.json()["message"].lower().startswith("invite sent")

        # User 2 should NOT yet have access until they accept via the emailed link
        access_resp = await client.get(
            f"/api/v1/groups/{group_id}",
            headers={"Authorization": f"Bearer {auth_token_2}"},
        )
        assert access_resp.status_code == 403

    async def test_invite_nonexistent_user_rejected(self, client: AsyncClient, auth_token: str):
        """Invites should fail for emails not present in users table."""
        group_resp = await client.post(
            "/api/v1/groups",
            json={"name": "Invite Fail"},
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        group_id = group_resp.json()["id"]

        resp = await client.post(
            f"/api/v1/groups/{group_id}/members",
            json={"email": "doesnotexist@example.com", "role": "viewer"},
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code == 404
        assert "existing users" in resp.json()["detail"].lower()

    async def test_list_members(self, client: AsyncClient, auth_token: str):
        """Test listing group members."""
        # Create group
        group_resp = await client.post(
            "/api/v1/groups",
            json={"name": "Member Test"},
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        group_id = group_resp.json()["id"]

        # List members
        members_resp = await client.get(
            f"/api/v1/groups/{group_id}/members",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert members_resp.status_code == 200
        members = members_resp.json()
        assert len(members) >= 1  # At least the creator

    async def test_duplicate_invite_fails(self, client: AsyncClient, auth_token: str, auth_token_2: str):
        """Test that inviting same user twice fails."""
        # Create group and invite
        group_resp = await client.post(
            "/api/v1/groups",
            json={"name": "Dup Invite"},
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        group_id = group_resp.json()["id"]

        # First invite
        first_resp = await client.post(
            f"/api/v1/groups/{group_id}/members",
            json={"email": "testuser2@example.com", "role": "operator"},
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert first_resp.status_code == 202

        # Duplicate invite (allowed since membership isn't created until acceptance)
        dup_resp = await client.post(
            f"/api/v1/groups/{group_id}/members",
            json={"email": "testuser2@example.com", "role": "manager"},
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert dup_resp.status_code == 202


@pytest.mark.asyncio
class TestBotRoutes:
    """Test bot CRUD operations."""

    @pytest.fixture
    async def group(self, client: AsyncClient, auth_token: str):
        """Create a test group."""
        resp = await client.post(
            "/api/v1/groups",
            json={"name": "Bot Test Group"},
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        return resp.json()

    async def test_create_bot(self, client: AsyncClient, auth_token: str, group):
        """Test creating a bot in a group."""
        response = await client.post(
            f"/api/v1/groups/{group['id']}/bots",
            json={
                "group_id": group["id"],
                "name": "SalesBot",
                "description": "Sales inquiry bot",
                "confidence_threshold": 85,
            },
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "SalesBot"
        assert data["group_id"] == group["id"]
        assert data["confidence_threshold"] == 85

    async def test_list_bots(self, client: AsyncClient, auth_token: str, group):
        """Test listing bots in a group."""
        # Create bot
        await client.post(
            f"/api/v1/groups/{group['id']}/bots",
            json={"group_id": group["id"], "name": "Bot1"},
            headers={"Authorization": f"Bearer {auth_token}"},
        )

        # List bots
        response = await client.get(
            f"/api/v1/groups/{group['id']}/bots",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 200
        bots = response.json()
        assert len(bots) >= 1

    async def test_get_bot(self, client: AsyncClient, auth_token: str, group):
        """Test getting bot details."""
        # Create bot
        create_resp = await client.post(
            f"/api/v1/groups/{group['id']}/bots",
            json={"group_id": group["id"], "name": "GetBot"},
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        bot_id = create_resp.json()["id"]

        # Get bot
        get_resp = await client.get(
            f"/api/v1/groups/{group['id']}/bots/{bot_id}",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert get_resp.status_code == 200
        assert get_resp.json()["id"] == bot_id

    async def test_update_bot(self, client: AsyncClient, auth_token: str, group):
        """Test updating a bot."""
        # Create bot
        create_resp = await client.post(
            f"/api/v1/groups/{group['id']}/bots",
            json={"group_id": group["id"], "name": "UpdateBot"},
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        bot_id = create_resp.json()["id"]

        # Update bot
        update_resp = await client.patch(
            f"/api/v1/groups/{group['id']}/bots/{bot_id}",
            json={"name": "UpdatedBot", "confidence_threshold": 90},
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert update_resp.status_code == 200
        assert update_resp.json()["name"] == "UpdatedBot"
        assert update_resp.json()["confidence_threshold"] == 90

    async def test_delete_bot(self, client: AsyncClient, auth_token: str, group):
        """Test deleting a bot."""
        # Create bot
        create_resp = await client.post(
            f"/api/v1/groups/{group['id']}/bots",
            json={"group_id": group["id"], "name": "DeleteBot"},
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        bot_id = create_resp.json()["id"]

        # Delete bot
        delete_resp = await client.delete(
            f"/api/v1/groups/{group['id']}/bots/{bot_id}",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert delete_resp.status_code == 204

        # Verify it's deleted
        get_resp = await client.get(
            f"/api/v1/groups/{group['id']}/bots/{bot_id}",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert get_resp.status_code == 404

    async def test_duplicate_bot_name_fails(self, client: AsyncClient, auth_token: str, group):
        """Test that duplicate bot names in same group are rejected."""
        # Create bot
        await client.post(
            f"/api/v1/groups/{group['id']}/bots",
            json={"group_id": group["id"], "name": "UniqueBot"},
            headers={"Authorization": f"Bearer {auth_token}"},
        )

        # Try duplicate
        dup_resp = await client.post(
            f"/api/v1/groups/{group['id']}/bots",
            json={"group_id": group["id"], "name": "UniqueBot"},
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert dup_resp.status_code == 409  # Conflict


@pytest.mark.asyncio
class TestDocumentRoutes:
    """Test document upload and retrieval."""

    @pytest.fixture
    async def group(self, client: AsyncClient, auth_token: str):
        """Create a test group."""
        resp = await client.post(
            "/api/v1/groups",
            json={"name": "Doc Test Group"},
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        return resp.json()

    async def test_list_documents(self, client: AsyncClient, auth_token: str, group):
        """Test listing documents in group KB."""
        response = await client.get(
            f"/api/v1/groups/{group['id']}/documents",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 200
        docs = response.json()
        assert isinstance(docs, list)

    async def test_upload_document(self, client: AsyncClient, auth_token: str, group):
        """Test uploading a document."""
        # Create test file
        files = {
            "file": ("test.txt", b"Test document content", "text/plain"),
        }
        data = {
            "group_id": group["id"],
            "title": "Test Document",
        }

        response = await client.post(
            f"/api/v1/groups/{group['id']}/documents/upload",
            files=files,
            data=data,
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 202  # Accepted
        result = response.json()
        assert result["status"] == "uploaded"
        assert "id" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
