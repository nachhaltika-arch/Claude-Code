"""
Fernet-based symmetric encryption for CMS passwords.
Key is read from env var CMS_ENCRYPTION_KEY.
Generate a key with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
"""
import os
import logging
from cryptography.fernet import Fernet, InvalidToken

logger = logging.getLogger(__name__)


def _get_fernet() -> Fernet:
    key = os.getenv("CMS_ENCRYPTION_KEY", "")
    if not key:
        raise RuntimeError("CMS_ENCRYPTION_KEY env variable is not set")
    raw = key.encode() if isinstance(key, str) else key
    return Fernet(raw)


def encrypt_password(plain: str) -> str:
    """Encrypt a plain-text password. Returns base64-encoded ciphertext string."""
    return _get_fernet().encrypt(plain.encode()).decode()


def decrypt_password(encrypted: str) -> str:
    """Decrypt a previously encrypted password. Returns plain text."""
    try:
        return _get_fernet().decrypt(encrypted.encode()).decode()
    except InvalidToken as e:
        logger.error("Failed to decrypt CMS password: %s", e)
        raise RuntimeError("Entschlüsselung fehlgeschlagen – CMS_ENCRYPTION_KEY stimmt nicht überein") from e
