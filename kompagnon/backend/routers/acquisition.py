"""
Einstellungen für die Akquise: Einbett-Widget und E-Mail-Versand.

Liegt im Tool unter Akquise, damit Anzeige und Links des Widgets dort gepflegt
werden können, wo das Widget auch verwendet wird — ohne Umweg über das
Render-Dashboard.

Der Versandweg wird hier nur noch **angezeigt**, nicht eingestellt: seit die
Einzelmails über die Brevo-Transaktions-API laufen, kommt der Zugang aus
``BREVO_API_KEY``. Ein SMTP-Formular im Tool hätte nur vorgetäuscht, dass dort
etwas einzurichten wäre — und sperrte tatsächlich den Test-Versand, solange
niemand einen ungenutzten SMTP-Server eintrug.
"""
import logging
import os
from datetime import timezone
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


class TestEmailRequest(BaseModel):
    to: str


# Wie viele der letzten Anfragen die Übersicht im Tool zeigt.
REQUEST_HISTORY_LIMIT = 25


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
# Anfragen aus dem Widget
# ═══════════════════════════════════════════════════════════════════

def _als_utc(zeitpunkt) -> Optional[str]:
    """Zeitstempel mit Zonenangabe.

    In der Datenbank stehen naive UTC-Werte. Ohne das angehängte 'Z' liest der
    Browser sie als Ortszeit und zeigt jede Anfrage zwei Stunden zu früh an.
    """
    if not zeitpunkt:
        return None
    return zeitpunkt.replace(tzinfo=timezone.utc).isoformat()


@router.get("/widget/requests")
def read_widget_requests(_: User = Depends(require_admin), db: Session = Depends(get_db)):
    """Die letzten Anfragen mit ihrem Zustellstand.

    Ohne diese Liste zeigt das Tool nur eine Gesamtzahl — ob die Berichte
    tatsächlich rausgingen, war daran nicht zu erkennen.
    """
    rows = (
        db.query(WidgetRequest)
        .order_by(WidgetRequest.created_at.desc())
        .limit(REQUEST_HISTORY_LIMIT)
        .all()
    )
    return {
        "requests": [
            {
                "id": row.id,
                "email": row.email,
                "website_url": row.website_url,
                "created_at": _als_utc(row.created_at),
                # Der Weg hat jetzt drei Stufen: Bestätigung angefragt,
                # Adresse bestätigt, Bericht versendet.
                "verify_sent": row.verify_sent_at is not None,
                "verified": row.verified_at is not None,
                "report_sent": row.report_sent_at is not None,
                # Der Klick auf den Berichtslink. Er belegt, dass die Adresse
                # dem Empfänger gehört — ohne ihn ist offen, ob der Bericht
                # bei der richtigen Person gelandet ist.
                "report_opened": row.report_confirmed_at is not None,
                "consent_marketing": bool(row.consent_marketing),
                "consent_confirmed": row.confirmed_at is not None,
            }
            for row in rows
        ],
        "limit": REQUEST_HISTORY_LIMIT,
    }


# ═══════════════════════════════════════════════════════════════════
# E-Mail-Versand — reine Anzeige plus Probeversand
# ═══════════════════════════════════════════════════════════════════

@router.get("/mail")
def read_mail_status(_: User = Depends(require_admin), db: Session = Depends(get_db)):
    """Über welchen Weg die Berichts-Mails rausgehen. Enthält nie ein Passwort."""
    config = app_settings.smtp_config(db)
    return {
        **app_settings.mail_channel(db),
        "sender_name": config["sender_name"],
        "sender_email": config["sender_email"],
    }


@router.post("/mail/test")
def send_test_email(
    payload: TestEmailRequest,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Verschickt eine echte Test-E-Mail über den aktiven Versandweg."""
    from services.email import send_email_detailed

    kanal = app_settings.mail_channel(db)
    if not kanal["ready"]:
        raise HTTPException(400, "Es ist kein Versandweg eingerichtet: "
                                 + kanal["detail"])
    config = app_settings.smtp_config(db)

    ok, grund = send_email_detailed(
        to_email=payload.to.strip(),
        subject="KOMPAGNON — Test des E-Mail-Versands",
        html_body=(
            "<p>Diese Nachricht bestätigt, dass der E-Mail-Versand aus dem "
            "KOMPAGNON-Tool funktioniert.</p>"
            f"<p style='color:#666;font-size:13px'>Versandweg: {kanal['label']} · "
            f"Absender: {config['sender_email'] or 'Vorgabe'}</p>"
        ),
        db=db,
    )
    if not ok:
        raise HTTPException(502, f"Versand fehlgeschlagen — {grund}")
    return {"message": f"Test-E-Mail an {payload.to} versendet",
            "channel": kanal["label"], "detail": grund}
