"""
Test JWT secret validation (SECURITY TESTS)
Ensures that weak or missing JWT secrets are caught at startup
"""

import pytest
import os
from unittest.mock import patch
from fastapi import HTTPException


def test_jwt_secret_not_set():
    """Test that missing JWT_SECRET raises RuntimeError at startup."""
    with patch.dict(os.environ, {}, clear=True):
        # Remove JWT_SECRET from environment
        with pytest.raises(RuntimeError) as exc_info:
            from app.core.auth import _get_jwt_secret
            _get_jwt_secret()
        
        assert "JWT_SECRET environment variable is not set" in str(exc_info.value)
        assert "CRITICAL" in str(exc_info.value)
        assert "production security" in str(exc_info.value)


def test_jwt_secret_too_short():
    """Test that JWT_SECRET shorter than 32 chars raises RuntimeError."""
    with patch.dict(os.environ, {"JWT_SECRET": "short-secret"}):
        with pytest.raises(RuntimeError) as exc_info:
            from app.core.auth import _get_jwt_secret
            _get_jwt_secret()
        
        assert "JWT_SECRET is too short" in str(exc_info.value)
        assert "CRITICAL" in str(exc_info.value)
        assert "32 characters" in str(exc_info.value)
        assert "token forgery" in str(exc_info.value)


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
        with patch.dict(os.environ, {"JWT_SECRET": weak_secret}, clear=False):
            if not weak_secret:  # Empty string
                with pytest.raises(RuntimeError) as exc_info:
                    from app.core.auth import _get_jwt_secret
                    _get_jwt_secret()
                assert "not set" in str(exc_info.value)
            elif len(weak_secret) < 32:
                with pytest.raises(RuntimeError) as exc_info:
                    from app.core.auth import _get_jwt_secret
                    _get_jwt_secret()
                assert "too short" in str(exc_info.value)


def test_jwt_secret_valid():
    """Test that valid JWT secrets (32+ chars, random) are accepted."""
    # Generate a valid random secret
    valid_secret = "x" * 32  # Exactly 32 characters
    
    with patch.dict(os.environ, {"JWT_SECRET": valid_secret}):
        # This should not raise an exception
        from app.core.auth import _get_jwt_secret
        secret = _get_jwt_secret()
        assert secret == valid_secret


def test_jwt_secret_strong():
    """Test with cryptographically strong secret."""
    import secrets
    strong_secret = secrets.token_urlsafe(32)
    
    with patch.dict(os.environ, {"JWT_SECRET": strong_secret}):
        from app.core.auth import _get_jwt_secret
        secret = _get_jwt_secret()
        assert secret == strong_secret
        assert len(secret) >= 32


def test_no_default_secret_fallback():
    """Test that there is NO default 'please-change-me' fallback."""
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(RuntimeError) as exc_info:
            from app.core.auth import _get_jwt_secret
            _get_jwt_secret()
        
        # Ensure the error is about missing secret, not about a default
        error_msg = str(exc_info.value)
        assert "not set" in error_msg
        assert "please-change-me" not in error_msg
        assert "default" not in error_msg.lower() or "not" in error_msg.lower()
