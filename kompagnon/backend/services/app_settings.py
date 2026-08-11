"""
Einstellungen aus der Datenbank mit Rückfall auf Umgebungsvariablen.

Damit lassen sich SMTP-Zugang und Widget-Konfiguration im Tool pflegen, ohne
dass jemand ins Render-Dashboard muss. Umgebungsvariablen bleiben als Rückfall
erhalten — was dort gesetzt ist, gilt weiter, solange in der Datenbank nichts
Eigenes steht.

Geheimnisse (SMTP-Passwort) werden mit Fernet verschlüsselt abgelegt und über
die API nie zurückgegeben — nur die Information, ob eines hinterlegt ist.
"""
import logging
import os
from typing import Dict, Optional

from database import SystemSettings

logger = logging.getLogger(__name__)

ENCRYPTED_PREFIX = "enc:"

# Einstellung → Umgebungsvariable, aus der der Rückfallwert kommt
ENV_FALLBACK = {
    "smtp_host": "SMTP_HOST",
    "smtp_port": "SMTP_PORT",
    "smtp_user": "SMTP_USER",
    "smtp_password": "SMTP_PASSWORD",
    "smtp_sender_name": "SMTP_SENDER_NAME",
    "smtp_sender_email": "SMTP_SENDER_EMAIL",
    "widget_privacy_url": "WIDGET_PRIVACY_URL",
    "widget_checkout_url": "WIDGET_CHECKOUT_URL",
}

SECRET_KEYS = frozenset({"smtp_password"})

DEFAULTS = {
    "smtp_port": "587",
    "smtp_sender_name": "KOMPAGNON",
    "widget_privacy_url": "",
    "widget_checkout_url": "",
    "widget_headline": "Ihre Website jetzt analysieren",
}


# ═══════════════════════════════════════════════════════════════════
# Verschlüsselung
# ═══════════════════════════════════════════════════════════════════

def _fernet():
    from cryptography.fernet import Fernet

    key = os.getenv("CREDENTIALS_KEY", "").strip()
    if not key:
        raise RuntimeError(
            "CREDENTIALS_KEY ist nicht gesetzt — ohne diesen Schlüssel kann das "
            "SMTP-Passwort nicht verschlüsselt gespeichert werden."
        )
    return Fernet(key.encode())


def encrypt_secret(value: str) -> str:
    return ENCRYPTED_PREFIX + _fernet().encrypt(value.encode()).decode()


def decrypt_secret(stored: str) -> str:
    if not stored:
        return ""
    if not stored.startswith(ENCRYPTED_PREFIX):
        # Aus der Umgebungsvariable oder aus der Zeit vor der Verschlüsselung
        return stored
    try:
        return _fernet().decrypt(stored[len(ENCRYPTED_PREFIX):].encode()).decode()
    except Exception as e:  # noqa: BLE001
        logger.error(f"Einstellung konnte nicht entschlüsselt werden: {e}")
        return ""


def is_encryption_available() -> bool:
    try:
        _fernet()
        return True
    except Exception:  # noqa: BLE001
        return False


# ═══════════════════════════════════════════════════════════════════
# Lesen und Schreiben
# ═══════════════════════════════════════════════════════════════════

def _stored(db, key: str) -> Optional[str]:
    row = db.query(SystemSettings).filter(SystemSettings.key == key).first()
    return row.value if row and row.value else None


def get(db, key: str, default: str = "") -> str:
    """Wert einer Einstellung: Datenbank, sonst Umgebung, sonst Vorgabe."""
    value = _stored(db, key)
    if value:
        return decrypt_secret(value) if key in SECRET_KEYS else value

    env_var = ENV_FALLBACK.get(key)
    if env_var:
        from_env = os.getenv(env_var, "").strip()
        if from_env:
            return from_env

    return default or DEFAULTS.get(key, "")


def set_many(db, values: Dict[str, str], admin_id: Optional[int] = None) -> None:
    """Speichert Einstellungen; Geheimnisse werden verschlüsselt abgelegt.

    Ein leerer Wert bei einem Geheimnis lässt das bestehende unangetastet —
    sonst würde das Passwort gelöscht, sobald jemand das Formular speichert,
    ohne es erneut einzutippen.
    """
    for key, raw in values.items():
        value = (raw or "").strip()

        if key in SECRET_KEYS:
            if not value:
                continue
            value = encrypt_secret(value)

        row = db.query(SystemSettings).filter(SystemSettings.key == key).first()
        if row:
            row.value = value
            row.updated_by = admin_id
        else:
            db.add(SystemSettings(key=key, value=value, updated_by=admin_id))
    db.commit()


def clear(db, key: str) -> None:
    db.query(SystemSettings).filter(SystemSettings.key == key).delete()
    db.commit()


# ═══════════════════════════════════════════════════════════════════
# Zusammengesetzte Konfigurationen
# ═══════════════════════════════════════════════════════════════════

def smtp_config(db) -> dict:
    """SMTP-Zugang inklusive Passwort — nur für den Versand, nie für die API."""
    host = get(db, "smtp_host")
    user = get(db, "smtp_user")
    try:
        port = int(get(db, "smtp_port", "587") or 587)
    except ValueError:
        port = 587

    return {
        "host": host,
        "port": port,
        "user": user,
        "password": get(db, "smtp_password"),
        "sender_name": get(db, "smtp_sender_name", "KOMPAGNON"),
        "sender_email": get(db, "smtp_sender_email") or user,
        "configured": bool(host and user),
    }


def smtp_status(db) -> dict:
    """Wie smtp_config, aber ohne Passwort — für die Anzeige im Tool."""
    config = smtp_config(db)
    stored = _stored(db, "smtp_password")
    return {
        "host": config["host"],
        "port": config["port"],
        "user": config["user"],
        "sender_name": config["sender_name"],
        "sender_email": config["sender_email"],
        "configured": config["configured"],
        "password_set": bool(config["password"]),
        "password_source": "datenbank" if stored else ("umgebung" if config["password"] else "keins"),
        "encryption_available": is_encryption_available(),
    }


def mail_channel(db) -> dict:
    """Welcher Weg die Einzelmails tatsächlich verschickt."""
    from services import brevo_mail

    smtp = smtp_config(db)
    if brevo_mail.is_available():
        return {"channel": "brevo", "label": "Brevo-Transaktions-API",
                "ready": True, "detail": "BREVO_API_KEY ist gesetzt"}
    if smtp["configured"]:
        return {"channel": "smtp", "label": "Eigener SMTP-Server",
                "ready": True, "detail": f"{smtp['host']}:{smtp['port']}"}
    return {"channel": "keiner", "label": "Nicht eingerichtet", "ready": False,
            "detail": "Weder BREVO_API_KEY noch SMTP-Zugang hinterlegt"}


def widget_config(db) -> dict:
    return {
        "privacy_url": get(db, "widget_privacy_url"),
        "checkout_url": get(db, "widget_checkout_url"),
        "headline": get(db, "widget_headline"),
    }
