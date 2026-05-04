"""
Nachrichten-API: Admin ↔ Kunde Kommunikation
"""
import os
import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional

from database import get_db, Message, Lead
from routers.auth_router import get_current_user, require_admin

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/messages", tags=["messages"])

SMTP_USER = os.getenv("SMTP_USER", "")


# ── Schemas ───────────────────────────────────────────────────────────────────

class AdminMessageIn(BaseModel):
    content: str
    subject: Optional[str] = None
    channel: str = "in_app"  # "in_app" | "email"


class KundeMessageIn(BaseModel):
    content: str
    token: str


# ── Hilfsfunktion ─────────────────────────────────────────────────────────────

def _email_wrapper(content: str, company_name: str) -> str:
    return f"""
<h3>Nachricht von KOMPAGNON</h3>
<p>{content}</p>
<hr>
<p style="color:gray;font-size:12px">
  Um zu antworten, besuchen Sie Ihr Kundenportal oder
  antworten Sie direkt auf diese E-Mail.
</p>
"""


def _msg_dict(m: Message) -> dict:
    return {
        "id":          m.id,
        "sender_role": m.sender_role,
        "sender_name": m.sender_name,
        "channel":     m.channel,
        "subject":     m.subject,
        "content":     m.content,
        "is_read":     m.is_read,
        "read_at":     m.read_at.isoformat() if m.read_at else None,
        "created_at":  m.created_at.isoformat() if m.created_at else None,
    }


# ── Endpunkt 1: Admin liest Nachrichten ──────────────────────────────────────

@router.get("/{lead_id}")
def get_messages(
    lead_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    messages = (
        db.query(Message)
        .filter(Message.lead_id == lead_id)
        .order_by(Message.created_at.asc())
        .all()
    )

    # Alle Kunden-Nachrichten als gelesen markieren + unread_messages zurücksetzen
    now = datetime.utcnow()
    updated = False
    for m in messages:
        if m.sender_role == "kunde" and not m.is_read:
            m.is_read = True
            m.read_at = now
            updated = True

    if updated:
        lead = db.query(Lead).filter(Lead.id == lead_id).first()
        if lead:
            lead.unread_messages = 0
        db.commit()

    return [_msg_dict(m) for m in messages]


# ── Endpunkt 2: Admin sendet Nachricht ───────────────────────────────────────

@router.post("/{lead_id}")
def send_message_admin(
    lead_id: int,
    body: AdminMessageIn,
    db: Session = Depends(get_db),
    user=Depends(require_admin),
):
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead nicht gefunden")

    sender_name = " ".join(filter(None, [user.first_name, user.last_name])) or user.email

    msg = Message(
        lead_id=lead_id,
        sender_role="admin",
        sender_name=sender_name,
        channel=body.channel,
        subject=body.subject,
        content=body.content,
    )
    db.add(msg)
    db.commit()
    db.refresh(msg)

    if body.channel == "email" and lead.email:
        from services.email import send_email
        ok = send_email(
            to_email=lead.email,
            subject=body.subject or "Nachricht von KOMPAGNON",
            html_body=_email_wrapper(body.content, lead.company_name or ""),
        )
        if not ok:
            logger.warning(f"E-Mail an {lead.email} konnte nicht gesendet werden")

    return {"id": msg.id, "created_at": msg.created_at.isoformat(), "success": True}


# ── Endpunkt 3: Kunde sendet Nachricht ───────────────────────────────────────

@router.post("/{lead_id}/kunde")
def send_message_kunde(
    lead_id: int,
    body: KundeMessageIn,
    db: Session = Depends(get_db),
):
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead or lead.customer_token != body.token:
        raise HTTPException(status_code=403, detail="Ungültiger Token")

    msg = Message(
        lead_id=lead_id,
        sender_role="kunde",
        sender_name=lead.company_name,
        channel="in_app",
        content=body.content,
    )
    db.add(msg)

    lead.unread_messages = (lead.unread_messages or 0) + 1
    db.commit()
    db.refresh(msg)

    # Admin-Benachrichtigung per E-Mail
    if SMTP_USER:
        from services.email import send_email
        ok = send_email(
            to_email=SMTP_USER,
            subject=f"💬 Neue Nachricht von {lead.company_name or 'Kunde'}",
            html_body=f"<p><strong>{lead.company_name}</strong> hat eine neue Nachricht gesendet:</p><blockquote>{body.content}</blockquote>",
        )
        if not ok:
            logger.warning(f"Admin-Benachrichtigung an {SMTP_USER} fehlgeschlagen")

    return {"id": msg.id, "created_at": msg.created_at.isoformat(), "success": True}


# ── Endpunkt 4: Kunde liest Nachrichten ──────────────────────────────────────

@router.get("/{lead_id}/kunde")
def get_messages_kunde(
    lead_id: int,
    token: str = Query(...),
    db: Session = Depends(get_db),
):
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead or lead.customer_token != token:
        raise HTTPException(status_code=403, detail="Ungültiger Token")

    messages = (
        db.query(Message)
        .filter(Message.lead_id == lead_id)
        .order_by(Message.created_at.asc())
        .all()
    )

    # Admin-Nachrichten als gelesen markieren
    now = datetime.utcnow()
    for m in messages:
        if m.sender_role in ("admin", "superadmin") and not m.is_read:
            m.is_read = True
            m.read_at = now
    db.commit()

    return [_msg_dict(m) for m in messages]


# ── Newsletter / Send-Email Endpunkt ─────────────────────────────────────────

class SendEmailBody(BaseModel):
    to: str
    subject: str
    html: str
    lead_id: Optional[int] = None
    project_id: Optional[int] = None


@router.post("/send-email")
def send_email_endpoint(
    body: SendEmailBody,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if not body.to or not body.subject:
        raise HTTPException(status_code=400, detail="to und subject sind Pflichtfelder")
    try:
        from services.email import send_email
        ok = send_email(to_email=body.to, subject=body.subject, html_body=body.html)
        if not ok:
            logger.warning(f"E-Mail an {body.to} konnte nicht gesendet werden")

        if body.lead_id:
            msg = Message(
                lead_id=body.lead_id,
                sender_role="admin",
                channel="email",
                subject=body.subject,
                content="[Newsletter]",
                created_at=datetime.utcnow(),
            )
            db.add(msg)
            db.commit()

        return {"success": True}
    except Exception as e:
        logger.error(f"send-email Fehler: {e}")
        return {"success": False, "error": str(e)}
