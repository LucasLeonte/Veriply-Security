"""Tests for token encryption utilities."""

import pytest
import os
import base64
from app.utils.encryption import encrypt_token, decrypt_token, get_encryption_key


@pytest.fixture
def mock_encryption_key(monkeypatch):
    """Set a test encryption key."""
    # Generate a valid 32-byte key
    test_key = base64.b64encode(os.urandom(32)).decode()
    monkeypatch.setenv("EMAIL_TOKEN_ENCRYPTION_KEY", test_key)
    return test_key


def test_encrypt_decrypt_token(mock_encryption_key):
    """Test that a token can be encrypted and decrypted correctly."""
    original_token = "test_refresh_token_12345"
    
    # Encrypt
    encrypted = encrypt_token(original_token)
    assert encrypted != original_token
    assert isinstance(encrypted, str)
    
    # Decrypt
    decrypted = decrypt_token(encrypted)
    assert decrypted == original_token


def test_encrypt_token_empty_raises_error(mock_encryption_key):
    """Test that encrypting an empty token raises an error."""
    with pytest.raises(ValueError, match="Token cannot be empty"):
        encrypt_token("")


def test_decrypt_token_empty_raises_error(mock_encryption_key):
    """Test that decrypting an empty token raises an error."""
    with pytest.raises(ValueError, match="Encrypted token cannot be empty"):
        decrypt_token("")


def test_decrypt_invalid_token_raises_error(mock_encryption_key):
    """Test that decrypting an invalid token raises an error."""
    with pytest.raises(ValueError, match="Invalid or corrupted encrypted token"):
        decrypt_token("invalid_base64_!@#$")


def test_get_encryption_key_missing_env():
    """Test that missing encryption key environment variable raises an error."""
    # Temporarily remove the environment variable
    old_value = os.environ.pop("EMAIL_TOKEN_ENCRYPTION_KEY", None)
    
    try:
        with pytest.raises(ValueError, match="EMAIL_TOKEN_ENCRYPTION_KEY not set"):
            get_encryption_key()
    finally:
        # Restore if it existed
        if old_value:
            os.environ["EMAIL_TOKEN_ENCRYPTION_KEY"] = old_value


def test_get_encryption_key_invalid_length(monkeypatch):
    """Test that an encryption key with invalid length raises an error."""
    # Set a key that's not 32 bytes
    invalid_key = base64.b64encode(b"short").decode()
    monkeypatch.setenv("EMAIL_TOKEN_ENCRYPTION_KEY", invalid_key)
    
    with pytest.raises(ValueError, match="Encryption key must be 32 bytes"):
        get_encryption_key()


def test_encrypt_different_each_time(mock_encryption_key):
    """Test that encrypting the same token twice produces different ciphertexts (due to random nonce)."""
    token = "same_token"
    
    encrypted1 = encrypt_token(token)
    encrypted2 = encrypt_token(token)
    
    assert encrypted1 != encrypted2
    
    # But both should decrypt to the same value
    assert decrypt_token(encrypted1) == token
    assert decrypt_token(encrypted2) == token
