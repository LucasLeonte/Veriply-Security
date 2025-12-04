from app.models import User
from app.services.auth_service import hash_password, verify_password, generate_uuid

def test_password_hashing():
    """Test password hashing and verification."""
    plain = "test_password_123"
    hashed = hash_password(plain)
    assert hashed != plain
    assert verify_password(plain, hashed)
    assert not verify_password("wrong_password", hashed)

def test_generate_uuid():
    """Test UUID generation."""
    uuid1 = generate_uuid()
    uuid2 = generate_uuid()
    assert uuid1 != uuid2
    assert len(uuid1) == 36  # UUID string format

def test_user_model_with_password():
    """Test User model with password_hash."""
    user = User(
        id="00000000-0000-0000-0000-000000000001",
        email="test@example.com",
        password_hash="hashed_password",
        tenant_id="00000000-0000-0000-0000-000000000002",
        role="owner"
    )
    assert user.email == "test@example.com"
    assert user.password_hash == "hashed_password"
    assert user.role == "owner"
