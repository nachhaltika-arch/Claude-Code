"""Die Modelle fuer Konten und Rechte (L-25).

`User`, `UserSession`, `SystemSettings`, `RolePermission` — wer sich anmelden
darf, womit, und was er dann sehen darf. Am 2026-08-30 aus `database.py`
herausgeloest; die Datei stand mit 845 Zeilen wieder ueber der Grenze.

**Der Schnitt geht am Thema entlang, nicht an der Zeilenzahl:** Diese vier
Klassen sind der Zugang. Sie stehen an keiner Stelle mit einem Betrieb oder
einem Projekt in Verbindung ausser ueber `User.lead_id` — und das ist ein
Fremdschluessel als Zeichenkette, kein Import.

**Diese Datei muss geladen werden**, wie alle `modelle_*.py` — siehe den
Importblock am Ende von `database.py`.
"""
from datetime import datetime

from sqlalchemy import (Boolean, Column, DateTime, ForeignKey, Integer,
                        String, Text, UniqueConstraint)
from sqlalchemy.orm import relationship

from database import Base


class User(Base):
    """User accounts with roles and 2FA support."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=True)

    # Profile
    first_name = Column(String(100), default="")
    last_name = Column(String(100), default="")
    phone = Column(String(30), default="")
    avatar_url = Column(String(500), default="")

    # Role: superadmin | admin | mitarbeiter | kunde — siehe
    # `services/rollen.py`, dort steht die Liste einmal.
    role = Column(String(20), default="mitarbeiter")

    # Fuer den Pruefer im Audit-Bericht (Innendienst)
    position = Column(String(100), default="")
    signature_data = Column(Text, default="")

    # Customer link
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=True)

    # 2FA
    totp_secret = Column(String(64), nullable=True)
    totp_enabled = Column(Boolean, default=False)
    backup_codes = Column(Text, default="")

    # OAuth
    google_id = Column(String(255), nullable=True)
    apple_id = Column(String(255), nullable=True)
    oauth_provider = Column(String(50), nullable=True)

    # Status
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    email_verify_token = Column(String(100), nullable=True)
    password_reset_token = Column(String(100), nullable=True)
    password_reset_expires = Column(DateTime, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    created_by = Column(Integer, nullable=True)


class UserSession(Base):
    """Active login sessions."""
    __tablename__ = "user_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    token = Column(String(500), unique=True)
    ip_address = Column(String(50), default="")
    user_agent = Column(String(500), default="")
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)
    is_valid = Column(Boolean, default=True)


class SystemSettings(Base):
    """Key-value system settings."""
    __tablename__ = "system_settings"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), unique=True, nullable=False)
    value = Column(Text, default="")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = Column(Integer, nullable=True)


class RolePermission(Base):
    """Permission assignments per role."""
    __tablename__ = "role_permissions"

    id = Column(Integer, primary_key=True, index=True)
    role = Column(String(20), nullable=False)
    permission = Column(String(50), nullable=False)
    is_allowed = Column(Boolean, default=True)

    # Ein Recht je Rolle, genau einmal. `services/rechte.hat_recht` liest mit
    # `.first()` und ohne Sortierung — zwei Zeilen mit verschiedenem
    # `is_allowed` haetten die Antwort dem Zufall ueberlassen, und ein
    # entzogenes Recht waere still zurueckgekommen (L-05, 21.08.2026).
    # Der Bestand wird in `migrations_runtime.py::run_migrations` zusammengefuehrt.
    __table_args__ = (
        UniqueConstraint("role", "permission", name="uq_role_permission"),
    )
