"""
Fernet-based symmetric encryption for CMS passwords.
Key is read from env var CMS_ENCRYPTION_KEY.
Generate a key with:
  python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

This module re-exports from utils.encryption so both
  from utils.encryption import ...
  from app.utils.encryption import ...
resolve to the same implementation.
"""
from utils.encryption import encrypt_password, decrypt_password  # noqa: F401

__all__ = ["encrypt_password", "decrypt_password"]
