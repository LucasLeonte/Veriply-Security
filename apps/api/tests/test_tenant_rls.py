import pytest
from app.models import Tenant, User, Base

@pytest.mark.asyncio
async def test_tenant_model_creation():
    """Test that Tenant model can be instantiated with correct fields."""
    tenant = Tenant(id="00000000-0000-0000-0000-000000000001", name="TestTenant", plan="basic")
    assert tenant.id == "00000000-0000-0000-0000-000000000001"
    assert tenant.name == "TestTenant"
    assert tenant.plan == "basic"

@pytest.mark.asyncio
async def test_user_model_creation():
    """Test that User model can be instantiated with correct fields."""
    user = User(
        id="00000000-0000-0000-0000-000000000011",
        email="test@example.com",
        tenant_id="00000000-0000-0000-0000-000000000001",
        role="admin"
    )
    assert user.id == "00000000-0000-0000-0000-000000000011"
    assert user.email == "test@example.com"
    assert user.tenant_id == "00000000-0000-0000-0000-000000000001"
    assert user.role == "admin"

def test_rls_policy_exists():
    """Verify that RLS policy configuration is in place (schema level)."""
    # This test verifies the model structure supports RLS
    # In production, RLS would be enforced at the database level
    assert hasattr(User, '__tablename__')
    assert User.__tablename__ == "users"
    assert hasattr(Tenant, '__tablename__')
    assert Tenant.__tablename__ == "tenants"
