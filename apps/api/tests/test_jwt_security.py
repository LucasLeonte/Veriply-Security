"""
Test JWT secret validation (SECURITY TESTS)
Ensures that weak or missing JWT secrets are caught at startup
"""

import pytest
from unittest.mock import patch, MagicMock
from app.core import auth

@pytest.fixture(autouse=True)
def clear_jwt_cache():
    """Reset the JWT secret cache before and after each test."""
    auth._jwt_secret_cache = None
    yield
    auth._jwt_secret_cache = None


def test_jwt_secret_not_set():
    """Test that missing JWT_SECRET raises RuntimeError at startup."""
    # Patch the settings object directly since get_jwt_secret reads from it
    with patch("app.core.settings.settings.JWT_SECRET", None):
        with pytest.raises(RuntimeError) as exc_info:
            auth.get_jwt_secret()
        
        assert "JWT_SECRET not configured" in str(exc_info.value)
        assert "CRITICAL" in str(exc_info.value)


def test_jwt_secret_too_short():
    """Test that JWT_SECRET shorter than 32 chars raises RuntimeError."""
    with patch("app.core.settings.settings.JWT_SECRET", "short-secret"):
        with pytest.raises(RuntimeError) as exc_info:
            auth.get_jwt_secret()
        
        assert "JWT_SECRET is too short" in str(exc_info.value)
        assert "CRITICAL" in str(exc_info.value)


def test_jwt_secret_weak_values():
    """Test that predictable/weak JWT secrets are rejected."""
    weak_secrets = [
        "please-change-me",  # Old default
        "password123",
        "1234567890123456789012345",  # Just barely under 32
        "secret",
        "",
    ]
    
    for weak_secret in weak_secrets:
        with patch("app.core.settings.settings.JWT_SECRET", weak_secret):
            if not weak_secret:  # Empty string or None
                with pytest.raises(RuntimeError) as exc_info:
                    auth.get_jwt_secret()
                assert "not configured" in str(exc_info.value)
            elif len(weak_secret) < 32:
                with pytest.raises(RuntimeError) as exc_info:
                    auth.get_jwt_secret()
                assert "too short" in str(exc_info.value)


def test_jwt_secret_valid():
    """Test that valid JWT secrets (32+ chars, random) are accepted."""
    # Generate a valid random secret
    valid_secret = "x" * 32  # Exactly 32 characters
    
    with patch("app.core.settings.settings.JWT_SECRET", valid_secret):
        secret = auth.get_jwt_secret()
        assert secret == valid_secret


def test_jwt_secret_strong():
    """Test with cryptographically strong secret."""
    import secrets
    strong_secret = secrets.token_urlsafe(32)
    
    with patch("app.core.settings.settings.JWT_SECRET", strong_secret):
        secret = auth.get_jwt_secret()
        assert secret == strong_secret
        assert len(secret) >= 32


def test_no_default_secret_fallback():
    """Test that there is NO default 'please-change-me' fallback."""
    with patch("app.core.settings.settings.JWT_SECRET", None):
        with pytest.raises(RuntimeError) as exc_info:
            auth.get_jwt_secret()
        
        error_msg = str(exc_info.value)
        assert "not configured" in error_msg
        assert "please-change-me" not in error_msg
