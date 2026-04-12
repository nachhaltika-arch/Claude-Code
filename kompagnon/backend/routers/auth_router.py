"""
Authentication API routes.
Login, register, 2FA, OAuth, password reset, profile, admin user management.
"""
import os
import json
import logging
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel
from slowapi import Limiter
from slowapi.util import get_remote_address

from database import User, UserSession, get_db
from auth import (
    hash_password, verify_password, create_access_token, decode_token,
    generate_totp_secret, generate_totp_qr, verify_totp,
    generate_backup_codes, generate_temp_token, generate_reset_token,
    oauth2_scheme,
)

logger = logging.getLogger(__name__)

# Rate limiter — uses same key_func (IP-based) as main.py instance
limiter = Limiter(key_func=get_remote_address)

router = APIRouter(prefix="/api/auth", tags=["auth"])
admin_router = APIRouter(prefix="/api/admin", tags=["admin"])


# ═══════════════════════════════════════════════════════════
# Dependencies
# ═══════════════════════════════════════════════════════════

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    if not token:
        raise HTTPException(401, "Nicht autorisiert")
    payload = decode_token(token)
    if payload.get("type") == "2fa_temp":
        raise HTTPException(401, "2FA-Verifizierung erforderlich")
    user = db.query(User).filter(User.id == payload.get("user_id")).first()
    if not user or not user.is_active:
        raise HTTPException(401, "Nicht autorisiert")
    return user


def require_admin(user: User = Depends(get_current_user)):
    """Admin und Superadmin haben Admin-Rechte."""
    if user.role not in ("admin", "superadmin"):
        raise HTTPException(403, "Admin-Rechte erforderlich")
    return user


def require_superadmin(user: User = Depends(get_current_user)):
    """Nur Superadmin darf diese Aktion ausfuehren."""
    if user.role != "superadmin":
        raise HTTPException(
            status_code=403,
            detail="Diese Aktion erfordert Superadmin-Rechte."
        )
    return user


def require_auditor(user: User = Depends(get_current_user)):
    if user.role not in ("admin", "superadmin", "auditor"):
        raise HTTPException(403, "Nur fuer Auditoren und Admins")
    return user


def require_any_auth(user: User = Depends(get_current_user)):
    return user


def require_kunde(user: User = Depends(get_current_user)):
    if user.role != "kunde":
        raise HTTPException(403, "Nur Kunden können Freigaben erteilen")
    return user


def optional_auth(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """Returns user if authenticated, None otherwise."""
    if not token:
        return None
    try:
        payload = decode_token(token)
        if payload.get("type") == "2fa_temp":
            return None
        user = db.query(User).filter(User.id == payload.get("user_id")).first()
        return user if user and user.is_active else None
    except Exception:
        return None


# ═══════════════════════════════════════════════════════════
# Request Models
# ═══════════════════════════════════════════════════════════

class RegisterRequest(BaseModel):
    email: str
    password: str
    first_name: str = ""
    last_name: str = ""


class LoginRequest(BaseModel):
    email: str
    password: str


class TwoFARequest(BaseModel):
    temp_token: str
    totp_code: str


class TwoFASetupVerify(BaseModel):
    totp_code: str


class TwoFADisable(BaseModel):
    totp_code: str
    password: str


class ForgotPasswordRequest(BaseModel):
    email: str


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


class ProfileUpdate(BaseModel):
    first_name: str = None
    last_name: str = None
    phone: str = None
    position: str = None


class SignatureUpdate(BaseModel):
    signature_data: str


class AdminCreateUser(BaseModel):
    email: str
    first_name: str = ""
    last_name: str = ""
    role: str = "nutzer"
    position: str = ""
    send_invite: bool = False


class AdminUpdateUser(BaseModel):
    role: str = None
    is_active: bool = None
    position: str = None


# ═══════════════════════════════════════════════════════════
# Registration
# ═══════════════════════════════════════════════════════════

@router.post("/register")
@limiter.limit("3/minute")
def register(request: Request, req: RegisterRequest, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == req.email.lower().strip()).first():
        # Keine Info ob E-Mail existiert — immer gleiche Antwort
        return {"message": "Falls diese E-Mail neu ist, erhalten Sie eine Bestätigung."}
    if len(req.password) < 8:
        raise HTTPException(400, "Passwort muss mindestens 8 Zeichen haben")

    user = User(
        email=req.email.lower().strip(),
        password_hash=hash_password(req.password),
        first_name=req.first_name.strip(),
        last_name=req.last_name.strip(),
        role="nutzer",
        is_active=True,
        is_verified=False,
        email_verify_token=generate_reset_token(),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return {"user_id": user.id, "message": "Konto erstellt. Bitte E-Mail bestaetigen."}


@router.post("/verify-email")
def verify_email(token: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email_verify_token == token).first()
    if not user:
        raise HTTPException(400, "Ungueltiger Verifizierungstoken")
    user.is_verified = True
    user.email_verify_token = None
    db.commit()
    return {"message": "E-Mail erfolgreich verifiziert"}


# ═══════════════════════════════════════════════════════════
# Login
# ═══════════════════════════════════════════════════════════

@router.post("/login")
@limiter.limit("5/minute")
def login(request: Request, req: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == req.email.lower().strip()).first()
    if not user or not user.password_hash:
        raise HTTPException(401, "E-Mail oder Passwort falsch")
    if not verify_password(req.password, user.password_hash):
        raise HTTPException(401, "E-Mail oder Passwort falsch")
    if not user.is_active:
        raise HTTPException(403, "Konto deaktiviert")

    # 2FA check
    if user.totp_enabled:
        temp_token = generate_temp_token(user.id)
        return {"require_2fa": True, "temp_token": temp_token}

    # Create full token
    token = create_access_token({"user_id": user.id, "role": user.role})
    user.last_login = datetime.utcnow()
    db.commit()

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": _user_dict(user),
    }


@router.post("/login/2fa")
@limiter.limit("5/minute")
def login_2fa(request: Request, req: TwoFARequest, db: Session = Depends(get_db)):
    payload = decode_token(req.temp_token)
    if payload.get("type") != "2fa_temp":
        raise HTTPException(401, "Ungueltiger 2FA-Token")

    user = db.query(User).filter(User.id == payload.get("user_id")).first()
    if not user:
        raise HTTPException(401, "Benutzer nicht gefunden")

    if not verify_totp(user.totp_secret, req.totp_code):
        # Check backup codes
        codes = json.loads(user.backup_codes) if user.backup_codes else []
        if req.totp_code in codes:
            codes.remove(req.totp_code)
            user.backup_codes = json.dumps(codes)
        else:
            raise HTTPException(401, "Ungueltiger 2FA-Code")

    token = create_access_token({"user_id": user.id, "role": user.role})
    user.last_login = datetime.utcnow()
    db.commit()

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": _user_dict(user),
    }


# ═══════════════════════════════════════════════════════════
# 2FA Setup
# ═══════════════════════════════════════════════════════════

@router.post("/2fa/setup")
def setup_2fa(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    secret = generate_totp_secret()
    user.totp_secret = secret
    db.commit()
    qr_code = generate_totp_qr(secret, user.email)
    return {"secret": secret, "qr_code_base64": qr_code}


@router.post("/2fa/verify-setup")
def verify_2fa_setup(req: TwoFASetupVerify, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not user.totp_secret:
        raise HTTPException(400, "2FA Setup nicht gestartet")
    if not verify_totp(user.totp_secret, req.totp_code):
        raise HTTPException(400, "Ungueltiger Code")

    codes = generate_backup_codes()
    user.totp_enabled = True
    user.backup_codes = json.dumps(codes)
    db.commit()

    return {"success": True, "backup_codes": codes}


@router.delete("/2fa/disable")
def disable_2fa(req: TwoFADisable, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not verify_password(req.password, user.password_hash or ""):
        raise HTTPException(401, "Passwort falsch")
    if not verify_totp(user.totp_secret or "", req.totp_code):
        raise HTTPException(401, "Ungueltiger 2FA-Code")

    user.totp_enabled = False
    user.totp_secret = None
    user.backup_codes = ""
    db.commit()
    return {"message": "2FA deaktiviert"}


# ═══════════════════════════════════════════════════════════
# Password Management
# ═══════════════════════════════════════════════════════════

@router.post("/forgot-password")
@limiter.limit("3/minute")
def forgot_password(request: Request, req: ForgotPasswordRequest, db: Session = Depends(get_db)):
    import time
    start = time.time()

    user = db.query(User).filter(User.email == req.email.lower().strip()).first()
    if user and user.is_active:
        user.password_reset_token = generate_reset_token()
        user.password_reset_expires = datetime.utcnow() + timedelta(hours=1)
        db.commit()
        try:
            from services.email import send_password_reset
            send_password_reset(user.email, user.password_reset_token)
        except Exception as e:
            logger.error(f"Password reset email failed: {e}")

    # Immer ~300ms — verhindert Timing-Angriff
    time.sleep(max(0, 0.3 - (time.time() - start)))

    # Immer gleiche Antwort — egal ob User existiert oder nicht
    return {"message": "Falls diese E-Mail existiert, erhalten Sie einen Reset-Link."}


@router.post("/reset-password")
def reset_password(req: ResetPasswordRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.password_reset_token == req.token).first()
    if not user or not user.password_reset_expires or user.password_reset_expires < datetime.utcnow():
        raise HTTPException(400, "Ungueltiger oder abgelaufener Reset-Token")
    if len(req.new_password) < 8:
        raise HTTPException(400, "Passwort muss mindestens 8 Zeichen haben")

    user.password_hash = hash_password(req.new_password)
    user.password_reset_token = None
    user.password_reset_expires = None
    db.commit()
    return {"message": "Passwort erfolgreich geaendert"}


@router.post("/change-password")
def change_password(req: ChangePasswordRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not verify_password(req.current_password, user.password_hash or ""):
        raise HTTPException(401, "Aktuelles Passwort falsch")
    if len(req.new_password) < 8:
        raise HTTPException(400, "Neues Passwort muss mindestens 8 Zeichen haben")

    user.password_hash = hash_password(req.new_password)
    db.commit()
    return {"message": "Passwort geaendert"}


# ═══════════════════════════════════════════════════════════
# Profile
# ═══════════════════════════════════════════════════════════

@router.get("/me")
def get_me(user: User = Depends(get_current_user)):
    return _user_dict(user)


@router.patch("/me")
def update_me(req: ProfileUpdate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if req.first_name is not None:
        user.first_name = req.first_name.strip()
    if req.last_name is not None:
        user.last_name = req.last_name.strip()
    if req.phone is not None:
        user.phone = req.phone.strip()
    if req.position is not None and user.role in ("admin", "superadmin", "auditor"):
        user.position = req.position.strip()
    db.commit()
    return _user_dict(user)


@router.post("/me/signature")
def update_signature(req: SignatureUpdate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if user.role not in ("admin", "superadmin", "auditor"):
        raise HTTPException(403, "Nur fuer Auditoren")
    user.signature_data = req.signature_data
    db.commit()
    return {"message": "Unterschrift gespeichert"}


# ═══════════════════════════════════════════════════════════
# Admin User Management
# ═══════════════════════════════════════════════════════════

@admin_router.get("/users")
def list_users(admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    users = db.query(User).order_by(User.created_at.desc()).all()
    return [_user_dict(u) for u in users]


@admin_router.post("/users")
def create_user(req: AdminCreateUser, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == req.email.lower().strip()).first():
        raise HTTPException(400, "E-Mail bereits vergeben")

    import secrets
    temp_password = secrets.token_urlsafe(12)
    user = User(
        email=req.email.lower().strip(),
        password_hash=hash_password(temp_password),
        first_name=req.first_name.strip(),
        last_name=req.last_name.strip(),
        role=req.role if req.role in ("admin", "superadmin", "auditor", "nutzer", "kunde") else "nutzer",
        position=req.position.strip(),
        is_active=True,
        is_verified=True,
        created_by=admin.id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return {
        "user": _user_dict(user),
        "temp_password": temp_password,
        "message": f"Benutzer {user.email} angelegt",
    }


@admin_router.patch("/users/{user_id}")
def update_user(user_id: int, req: AdminUpdateUser, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(404, "Benutzer nicht gefunden")
    if req.role is not None and req.role in ("admin", "superadmin", "auditor", "nutzer", "kunde"):
        # Only superadmin may promote users to superadmin
        if req.role == "superadmin" and admin.role != "superadmin":
            raise HTTPException(403, "Nur Superadmin darf die Superadmin-Rolle vergeben")
        user.role = req.role
    if req.is_active is not None:
        user.is_active = req.is_active
    if req.position is not None:
        user.position = req.position.strip()
    db.commit()
    return _user_dict(user)


@admin_router.delete("/users/{user_id}")
def delete_user(user_id: int, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(404, "Benutzer nicht gefunden")
    if user.id == admin.id:
        raise HTTPException(400, "Eigenen Account nicht loeschen")
    db.delete(user)
    db.commit()
    return {"message": "Benutzer geloescht"}


@admin_router.post("/users/{user_id}/reset-password")
def admin_reset_password(user_id: int, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(404, "Benutzer nicht gefunden")

    import secrets
    temp_password = secrets.token_urlsafe(12)
    user.password_hash = hash_password(temp_password)
    db.commit()

    return {"temp_password": temp_password, "message": f"Passwort fuer {user.email} zurueckgesetzt"}


# ═══════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════

def _user_dict(user: User) -> dict:
    onboarding_done = False
    if user.lead_id:
        try:
            from database import SessionLocal, Lead
            _db = SessionLocal()
            lead = _db.query(Lead).filter(Lead.id == user.lead_id).first()
            onboarding_done = bool(getattr(lead, 'onboarding_completed', False)) if lead else False
            _db.close()
        except Exception:
            pass

    return {
        "id": user.id,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "phone": user.phone,
        "role": user.role,
        "position": user.position,
        "avatar_url": user.avatar_url,
        "totp_enabled": user.totp_enabled,
        "is_active": user.is_active,
        "is_verified": user.is_verified,
        "lead_id": user.lead_id,
        "last_login": user.last_login.isoformat() if user.last_login else None,
        "created_at": user.created_at.isoformat() if user.created_at else None,
        "onboarding_completed": onboarding_done,
    }
