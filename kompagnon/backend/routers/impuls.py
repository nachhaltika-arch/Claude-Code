"""
IMPULS by KOMPAGNON — ISB-158 Beratungsanfragen-Router.
POST /api/impuls/anfrage  — öffentlich, kein Auth nötig.
Legt Lead an, sendet Bestätigungs- + Team-E-Mail.
"""
import logging
import os
import re

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, field_validator
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy import text
from sqlalchemy.orm import Session

# Keine Abhaengigkeit auf email-validator: wir validieren mit einer einfachen Regex.
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

from database import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/impuls", tags=["impuls"])
limiter = Limiter(key_func=get_remote_address)

TEAM_EMAIL   = os.getenv("IMPULS_NOTIFY_EMAIL", "info@kompagnon.eu")
FRONTEND_URL = os.getenv("FRONTEND_URL", "https://kompagnon-frontend.onrender.com")


class ImpulsAnfrage(BaseModel):
    name:    str
    company: str
    email:   str
    phone:   str  = ""
    message: str  = ""

    @field_validator("email")
    @classmethod
    def _check_email(cls, v: str) -> str:
        if not v or not _EMAIL_RE.match(v):
            raise ValueError("Ungültige E-Mail-Adresse")
        return v.strip()


@router.post("/anfrage")
@limiter.limit("5/minute")
def impuls_anfrage(request: Request, body: ImpulsAnfrage, db: Session = Depends(get_db)):
    """
    Öffentlicher Endpunkt — kein Auth erforderlich.
    1. Duplikat-Check per E-Mail
    2. Lead anlegen
    3. Bestätigungs-E-Mail an Interessenten
    4. Team-Benachrichtigung
    """

    # ── 1. Duplikat-Check ──────────────────────────────────────────────────
    existing = db.execute(
        text("SELECT id FROM leads WHERE email = :email"),
        {"email": body.email},
    ).first()

    if existing:
        lead_id = existing.id
        logger.info(f"IMPULS: Bekannte E-Mail {body.email} — Lead #{lead_id} bereits vorhanden")
    else:
        # ── 2. Lead anlegen ───────────────────────────────────────────────
        try:
            result = db.execute(text("""
                INSERT INTO leads (
                    company_name, contact_name, email, phone,
                    lead_source, status, notes,
                    created_at, updated_at
                ) VALUES (
                    :company, :contact, :email, :phone,
                    'impuls_landing', 'neu', :notes,
                    NOW(), NOW()
                )
                RETURNING id
            """), {
                "company": body.company,
                "contact": body.name,
                "email":   body.email,
                "phone":   body.phone or "",
                "notes":   f"IMPULS-Anfrage: {body.message}" if body.message else "IMPULS-Anfrage ohne Nachricht",
            })
            db.commit()
            lead_id = result.fetchone()[0]
            logger.info(f"IMPULS: Lead #{lead_id} angelegt für {body.company}")
        except Exception as e:
            db.rollback()
            logger.error(f"IMPULS Lead-Anlage fehlgeschlagen: {e}")
            raise HTTPException(status_code=500, detail="Anfrage konnte nicht gespeichert werden.")

    # ── 3. E-Mails senden ──────────────────────────────────────────────────
    try:
        from services.email import send_email
        _send_confirmation(body, send_email)
        _send_team_notification(body, lead_id, send_email)
    except Exception as e:
        # E-Mail-Fehler darf den Erfolg nicht blockieren — Lead ist schon angelegt
        logger.error(f"IMPULS E-Mail-Versand fehlgeschlagen: {e}")

    return {"success": True, "lead_id": lead_id}


def _send_confirmation(body: ImpulsAnfrage, send_email):
    """Bestätigungs-E-Mail an den Interessenten."""
    first_name = body.name.strip().split()[0] if body.name.strip() else body.name
    phone_row   = f'<strong>Telefon:</strong> {body.phone}<br>'       if body.phone   else ''
    message_row = f'<strong>Ihre Situation:</strong> {body.message}<br>' if body.message else ''
    steps_html = ''.join([
        f'<div style="display:flex;gap:12px;margin-bottom:10px;font-size:14px;color:#475569;">'
        f'<span style="color:#008EAA;font-weight:900;min-width:20px;">{nr}</span>'
        f'<span>{txt}</span></div>'
        for nr, txt in [
            ('1.', 'Wir prüfen Ihre Förderfähigkeit nach ISB-158'),
            ('2.', 'Sie erhalten einen Terminvorschlag für das Erstgespräch'),
            ('3.', 'Gemeinsam stellen wir den Förderantrag bei der ISB'),
            ('4.', 'Die Beratung beginnt nach Bewilligung'),
        ]
    ])
    html = f"""
    <!DOCTYPE html>
    <html lang="de">
    <head><meta charset="utf-8"></head>
    <body style="font-family: 'Noto Sans', Arial, sans-serif; background: #f0f4f5; margin: 0; padding: 0;">
      <div style="max-width: 600px; margin: 40px auto; background: #fff; border-radius: 12px; overflow: hidden; border: 1px solid #e2e8f0;">
        <div style="background: #004F59; padding: 28px 32px;">
          <div style="color: #FAE600; font-size: 11px; font-weight: 700; letter-spacing: 0.12em; text-transform: uppercase; margin-bottom: 8px;">IMPULS by KOMPAGNON</div>
          <h1 style="color: #fff; font-size: 22px; font-weight: 900; margin: 0;">Ihre Anfrage ist eingegangen</h1>
        </div>
        <div style="padding: 32px;">
          <p style="color: #334155; font-size: 15px; line-height: 1.7; margin: 0 0 16px;">
            Guten Tag {first_name},
          </p>
          <p style="color: #475569; font-size: 14px; line-height: 1.7; margin: 0 0 24px;">
            vielen Dank für Ihre Anfrage zum ISB-158-Förderprogramm. Wir melden uns innerhalb von
            <strong>24 Stunden</strong> bei Ihnen für ein kostenloses Erstgespräch.
          </p>
          <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 10px; padding: 20px; margin-bottom: 24px;">
            <div style="font-size: 11px; font-weight: 700; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 12px;">Ihre Angaben</div>
            <div style="font-size: 14px; color: #475569; line-height: 2;">
              <strong>Name:</strong> {body.name}<br>
              <strong>Unternehmen:</strong> {body.company}<br>
              <strong>E-Mail:</strong> {body.email}<br>
              {phone_row}
              {message_row}
            </div>
          </div>
          <div style="font-size: 11px; font-weight: 700; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 12px;">Was als nächstes passiert</div>
          {steps_html}
          <div style="margin-top: 28px; padding: 18px 20px; background: #004F5912; border-radius: 10px; text-align: center;">
            <div style="font-size: 14px; color: #004F59; font-weight: 600; margin-bottom: 4px;">Haben Sie Fragen?</div>
            <div style="font-size: 13px; color: #64748b;">
              📞 +49 (0) 261 884470 &nbsp;·&nbsp; ✉ info@kompagnon.eu
            </div>
          </div>
        </div>
        <div style="background: #f8fafc; padding: 16px 32px; font-size: 11px; color: #94a3b8; border-top: 1px solid #e2e8f0;">
          KOMPAGNON communications BP GmbH · Koblenz · Akkreditierter ISB-Berater Rheinland-Pfalz
        </div>
      </div>
    </body>
    </html>
    """
    send_email(
        to_email=body.email,
        subject="Ihre IMPULS-Anfrage ist eingegangen – KOMPAGNON",
        html_body=html,
    )


def _send_team_notification(body: ImpulsAnfrage, lead_id: int, send_email):
    """Interne Benachrichtigung ans KOMPAGNON-Team."""
    html = f"""
    <!DOCTYPE html>
    <html lang="de">
    <head><meta charset="utf-8"></head>
    <body style="font-family: Arial, sans-serif; background: #f0f4f5; margin: 0; padding: 20px;">
      <div style="max-width: 560px; margin: 0 auto; background: #fff; border-radius: 10px; border: 1px solid #e2e8f0; overflow: hidden;">
        <div style="background: #FAE600; padding: 16px 24px;">
          <div style="font-size: 13px; font-weight: 900; color: #004F59;">⚡ Neue IMPULS-Anfrage eingegangen</div>
        </div>
        <div style="padding: 24px;">
          <table style="width: 100%; font-size: 14px; color: #334155; border-collapse: collapse;">
            <tr><td style="padding: 6px 0; color: #64748b; width: 130px;">Name</td><td style="font-weight: 600;">{body.name}</td></tr>
            <tr><td style="padding: 6px 0; color: #64748b;">Unternehmen</td><td style="font-weight: 600;">{body.company}</td></tr>
            <tr><td style="padding: 6px 0; color: #64748b;">E-Mail</td><td><a href="mailto:{body.email}" style="color: #008EAA;">{body.email}</a></td></tr>
            <tr><td style="padding: 6px 0; color: #64748b;">Telefon</td><td>{body.phone or '—'}</td></tr>
            <tr><td style="padding: 6px 0; color: #64748b;">Nachricht</td><td>{body.message or '—'}</td></tr>
            <tr><td style="padding: 6px 0; color: #64748b;">Lead-ID</td><td>#{lead_id}</td></tr>
            <tr><td style="padding: 6px 0; color: #64748b;">Quelle</td><td>IMPULS Landing Page</td></tr>
          </table>
          <div style="margin-top: 20px; text-align: center;">
            <a href="{FRONTEND_URL}/app/leads"
               style="display: inline-block; background: #004F59; color: #fff; padding: 12px 24px; border-radius: 8px; font-weight: 700; font-size: 13px; text-decoration: none;">
              → Lead im KAS öffnen
            </a>
          </div>
        </div>
      </div>
    </body>
    </html>
    """
    send_email(
        to_email=TEAM_EMAIL,
        subject=f"⚡ Neue IMPULS-Anfrage: {body.company} ({body.name})",
        html_body=html,
    )
