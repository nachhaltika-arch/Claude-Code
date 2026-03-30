"""
Authentication module for KOMPAGNON.
JWT tokens, password hashing, TOTP 2FA, OAuth helpers.
"""
import os
import io
import base64
import secrets
from datetime import datetime, timedelta
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

try:
    import pyotp
    import qrcode
    HAS_TOTP = True
except ImportError:
    HAS_TOTP = False

SECRET_KEY = os.getenv("SECRET_KEY", "kompagnon-secret-2025-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 8  # 8 hours

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


def hash_password(password: str) -> str:
    password = password.encode("utf-8")[:72].decode("utf-8", errors="ignore")
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    plain = plain.encode("utf-8")[:72].decode("utf-8", errors="ignore")
    return pwd_context.verify(plain, hashed)


def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token ungueltig oder abgelaufen",
            headers={"WWW-Authenticate": "Bearer"},
        )


def generate_totp_secret() -> str:
    if not HAS_TOTP:
        raise HTTPException(500, "2FA nicht verfuegbar (pyotp nicht installiert)")
    return pyotp.random_base32()


def generate_totp_qr(secret: str, email: str) -> str:
    if not HAS_TOTP:
        return ""
    totp = pyotp.TOTP(secret)
    uri = totp.provisioning_uri(email, issuer_name="KOMPAGNON")
    img = qrcode.make(uri)
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode()


def verify_totp(secret: str, code: str) -> bool:
    if not HAS_TOTP:
        return False
    totp = pyotp.TOTP(secret)
    return totp.verify(code, valid_window=1)


def generate_backup_codes(count: int = 8) -> list:
    return [f"{secrets.token_hex(2).upper()}-{secrets.token_hex(2).upper()}" for _ in range(count)]


def generate_temp_token(user_id: int) -> str:
    return create_access_token(
        {"user_id": user_id, "type": "2fa_temp"},
        expires_delta=timedelta(minutes=5),
    )


def generate_reset_token() -> str:
    return secrets.token_urlsafe(32)
