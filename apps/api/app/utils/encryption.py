"""Token encryption/decryption utilities using AES-256-GCM."""

import os
import base64
import logging
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.backends import default_backend

logger = logging.getLogger(__name__)


def get_encryption_key() -> bytes:
    """
    Get encryption key from environment variable.
    
    Expected format: 32-byte base64-encoded string.
    Generate with: python -c "import os, base64; print(base64.b64encode(os.urandom(32)).decode())"
    """
    key_b64 = os.environ.get("EMAIL_TOKEN_ENCRYPTION_KEY")
    if not key_b64:
        raise ValueError(
            "EMAIL_TOKEN_ENCRYPTION_KEY not set. Generate with: "
            "python -c \"import os, base64; print(base64.b64encode(os.urandom(32)).decode())\""
        )
    
    try:
        key = base64.b64decode(key_b64)
        if len(key) != 32:
            raise ValueError("Encryption key must be 32 bytes")
        return key
    except Exception as e:
        raise ValueError(f"Invalid EMAIL_TOKEN_ENCRYPTION_KEY format: {e}")


def encrypt_token(token: str) -> str:
    """
    Encrypt a token using AES-256-GCM.
    
    Args:
        token: Plain text token to encrypt
        
    Returns:
        Base64-encoded string: nonce (12 bytes) + ciphertext + tag (16 bytes)
    """
    if not token:
        raise ValueError("Token cannot be empty")
    
    key = get_encryption_key()
    aesgcm = AESGCM(key)
    
    # Generate random 12-byte nonce
    nonce = os.urandom(12)
    
    # Encrypt (returns ciphertext + tag)
    ciphertext = aesgcm.encrypt(nonce, token.encode('utf-8'), None)
    
    # Combine nonce + ciphertext and encode
    encrypted = nonce + ciphertext
    return base64.b64encode(encrypted).decode('utf-8')


def decrypt_token(encrypted_token: str) -> str:
    """
    Decrypt a token using AES-256-GCM.
    
    Args:
        encrypted_token: Base64-encoded encrypted token
        
    Returns:
        Plain text token
    """
    if not encrypted_token:
        raise ValueError("Encrypted token cannot be empty")
    
    try:
        key = get_encryption_key()
        aesgcm = AESGCM(key)
        
        # Decode from base64
        encrypted = base64.b64decode(encrypted_token)
        
        # Split nonce (first 12 bytes) and ciphertext+tag (rest)
        nonce = encrypted[:12]
        ciphertext = encrypted[12:]
        
        # Decrypt
        plaintext = aesgcm.decrypt(nonce, ciphertext, None)
        return plaintext.decode('utf-8')
    except Exception as e:
        logger.error(f"Failed to decrypt token: {e}")
        raise ValueError("Invalid or corrupted encrypted token")
