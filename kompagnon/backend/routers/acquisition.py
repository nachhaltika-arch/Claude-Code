"""
Einstellungen für die Akquise: Einbett-Widget und E-Mail-Versand.

Liegt im Tool unter Akquise, damit Datenschutz-Link und SMTP-Zugang dort
gepflegt werden können, wo das Widget auch verwendet wird — ohne Umweg über
das Render-Dashboard.
"""
import logging
import os
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import User, WidgetRequest, get_db
from routers.auth_router import require_admin
from services import app_settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/acquisition", tags=["acquisition"])


class WidgetSettings(BaseModel):
    privacy_url: str = ""
    checkout_url: str = ""
    headline: str = ""


class SmtpSettings(BaseModel):
    host: str = ""
    port: int = 587
    user: str = ""
    password: str = ""          # leer lassen = bestehendes Passwort behalten
    sender_name: str = ""
    sender_email: str = ""


class TestEmailRequest(BaseModel):
    to: str


def widget_embed_url() -> str:
    base = os.getenv("FRONTEND_URL", "https://kompagnon-frontend.onrender.com").rstrip("/")
    return f"{base}/embed/audit-widget.html"


# ═══════════════════════════════════════════════════════════════════
# Widget
# ═══════════════════════════════════════════════════════════════════

@router.get("/widget")
def read_widget_settings(_: User = Depends(require_admin), db: Session = Depends(get_db)):
    config = app_settings.widget_config(db)
    return {
        **config,
        "embed_url": widget_embed_url(),
        "requests_total": db.query(WidgetRequest).count(),
        "requests_confirmed": db.query(WidgetRequest).filter(
            WidgetRequest.confirmed_at.isnot(None)).count(),
    }


@router.put("/widget")
def write_widget_settings(
    payload: WidgetSettings,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    for field, value in (("widget_privacy_url", payload.privacy_url),
                         ("widget_checkout_url", payload.checkout_url)):
        if value and not value.startswith(("http://", "https://", "/")):
            raise HTTPException(400, f"'{value}' ist keine gültige Adresse.")

    app_settings.set_many(db, {
        "widget_privacy_url": payload.privacy_url,
        "widget_checkout_url": payload.checkout_url,
        "widget_headline": payload.headline,
    }, admin.id)
    return {"message": "Widget-Einstellungen gespeichert"}


# ═══════════════════════════════════════════════════════════════════
# E-Mail-Versand
# ═══════════════════════════════════════════════════════════════════

@router.get("/smtp")
def read_smtp_settings(_: User = Depends(require_admin), db: Session = Depends(get_db)):
    """Zugangsdaten ohne Passwort — das wird nie zurückgegeben."""
    return app_settings.smtp_status(db)


@router.put("/smtp")
def write_smtp_settings(
    payload: SmtpSettings,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    if payload.password and not app_settings.is_encryption_available():
        raise HTTPException(
            500, "CREDENTIALS_KEY fehlt — ohne diesen Schlüssel wird kein "
                 "Passwort gespeichert, damit es nicht im Klartext liegt.")
    if payload.port not in range(1, 65536):
        raise HTTPException(400, "Port muss zwischen 1 und 65535 liegen.")

    app_settings.set_many(db, {
        "smtp_host": payload.host,
        "smtp_port": str(payload.port),
        "smtp_user": payload.user,
        "smtp_password": payload.password,
        "smtp_sender_name": payload.sender_name,
        "smtp_sender_email": payload.sender_email,
    }, admin.id)
    logger.info(f"SMTP-Einstellungen geändert von Nutzer {admin.id}")
    return app_settings.smtp_status(db)


@router.post("/smtp/test")
def send_test_email(
    payload: TestEmailRequest,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Verschickt eine echte Test-E-Mail über den hinterlegten Zugang."""
    from services.email import send_email

    config = app_settings.smtp_config(db)
    if not config["configured"]:
        raise HTTPException(400, "SMTP ist nicht vollständig eingerichtet "
                                 "(Server und Benutzer werden benötigt).")

    ok = send_email(
        to_email=payload.to.strip(),
        subject="KOMPAGNON — SMTP-Test",
        html_body=(
            "<p>Diese Nachricht bestätigt, dass der E-Mail-Versand aus dem "
            "KOMPAGNON-Tool funktioniert.</p>"
            f"<p style='color:#666;font-size:13px'>Server: {config['host']}:{config['port']} · "
            f"Absender: {config['sender_email']}</p>"
        ),
        db=db,
    )
    if not ok:
        raise HTTPException(502, "Versand fehlgeschlagen — bitte Server, Port, "
                                 "Benutzer und Passwort prüfen.")
    return {"message": f"Test-E-Mail an {payload.to} versendet"}
