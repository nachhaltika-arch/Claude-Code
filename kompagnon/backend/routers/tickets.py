"""
Support ticket API routes.
"""
import random
import string
import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel

from database import get_db
from routers.auth_router import get_current_user, require_innendienst

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/tickets", tags=["tickets"])


def _gen_ticket_nr():
    d = datetime.now().strftime("%y%m")
    r = "".join(random.choices(string.digits, k=4))
    return f"TKT-{d}-{r}"


class TicketCreate(BaseModel):
    type: str = "feedback"
    priority: str = "medium"
    title: str
    description: str
    page_url: str = ""
    browser_info: str = ""
    user_email: str = ""
    user_name: str = ""
    screenshot_base64: str = ""


class TicketUpdate(BaseModel):
    status: Optional[str] = None
    priority: Optional[str] = None
    admin_notes: Optional[str] = None


@router.post("/")
def create_ticket(req: TicketCreate, db: Session = Depends(get_db)):
    nr = _gen_ticket_nr()
    db.execute(text(
        "INSERT INTO support_tickets (ticket_number, user_email, user_name, type, priority, status, title, description, page_url, browser_info, screenshot_base64) "
        "VALUES (:nr, :email, :name, :type, :prio, 'open', :title, :desc, :page, :browser, :screenshot)"
    ), {"nr": nr, "email": req.user_email, "name": req.user_name, "type": req.type, "prio": req.priority,
        "title": req.title, "desc": req.description, "page": req.page_url, "browser": req.browser_info, "screenshot": req.screenshot_base64})
    db.commit()

    # Bis zum 26.08.2026 schrieb diese Route eine Zeile und schwieg. Wer ein
    # Ticket aufgab, bekam eine Nummer — und im Innendienst passierte nichts,
    # bis jemand von sich aus in die Ticketliste sah (L-18).
    from services.benachrichtigungen import melden_leise
    melden_leise(db, art="ticket",
                 titel=f"Ticket {nr}: {req.title}"[:300],
                 hinweis=f"{req.user_name or req.user_email} · "
                         f"{req.type} · Priorität {req.priority}",
                 ziel="/app/tickets")

    # **Zusaetzlich per Mail, wenn gewuenscht (26.08.2026).** Der Schalter
    # steht vorgabegemaess **aus**: Ein Ticket meldete bisher nur die Glocke,
    # und die Vorgabe jedes neuen Schalters ist das Verhalten von heute. Wer
    # nichts umstellt, bekommt keine Mail, die er nicht kennt.
    _ticket_mail(db, nr, req)

    return {"ticket_number": nr, "message": "Ticket erstellt"}


def _ticket_mail(db, nr, req) -> None:
    """Ein neues Ticket auch ins Postfach — Beiwerk, kein Vorgang.

    Faellt der Versand aus, ist das Ticket trotzdem angelegt und die Glocke
    meldet es. Dieselbe Reihenfolge wie bei `melden_leise`: Die Sache des
    Kunden ist die Hauptsache.
    """
    import logging
    import os

    empfaenger = os.getenv("SMTP_USER", "").strip()
    if not empfaenger:
        return

    try:
        from services.meldungsvorlieben import soll_melden_leise

        if not soll_melden_leise(db, "ticket_mail"):
            return

        from services.email import send_email

        send_email(
            to_email=empfaenger,
            subject=f"🎫 Ticket {nr}: {req.title}"[:200],
            html_body=(f"<p><strong>{req.user_name or req.user_email}</strong>"
                       f" hat ein Ticket angelegt.</p>"
                       f"<p><strong>{req.title}</strong></p>"
                       f"<blockquote>{req.description or ''}</blockquote>"
                       f"<p>Art: {req.type} · Priorität: {req.priority}</p>"),
        )
    except Exception as fehler:      # noqa: BLE001
        logging.getLogger(__name__).warning(
            "Ticket-Mail nicht versendet: %s", fehler)


@router.get("/my")
def my_tickets(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """Tickets des eingeloggten Benutzers (nach E-Mail)."""
    rows = db.execute(
        text("SELECT * FROM support_tickets WHERE user_email = :email ORDER BY created_at DESC LIMIT 50"),
        {"email": current_user.email},
    ).mappings().all()
    return [dict(r) for r in rows]


@router.get("/", dependencies=[Depends(require_innendienst)])
def list_tickets(status: str = Query(None), type: str = Query(None), priority: str = Query(None), db: Session = Depends(get_db)):
    """Alle Tickets — Innendienstsicht.

    **Bis zum 22.08.2026 ohne jede Anmeldepruefung (L-51).** Die Zeilen
    tragen Name, E-Mail-Adresse, Beschreibung, Seiten-URL, Browser-Angaben
    und `screenshot_base64`. `PATCH /{ticket_id}` daneben trug schon
    `require_innendienst` — die Leserouten wurden uebersehen.

    Der Kundenfall liegt auf `GET /my` und filtert auf die eigene Adresse.
    """
    q = "SELECT * FROM support_tickets WHERE 1=1"
    params = {}
    if status:
        q += " AND status = :status"
        params["status"] = status
    if type:
        q += " AND type = :type"
        params["type"] = type
    if priority:
        q += " AND priority = :priority"
        params["priority"] = priority
    q += " ORDER BY created_at DESC LIMIT 100"
    rows = db.execute(text(q), params).mappings().all()
    return [dict(r) for r in rows]


@router.get("/{ticket_id}", dependencies=[Depends(require_innendienst)])
def get_ticket(ticket_id: int, db: Session = Depends(get_db)):
    """Ein Ticket im Detail — Innendienstsicht.

    Stand ebenfalls ohne Anmeldung offen und war durchzaehlbar (L-51).
    """
    row = db.execute(text("SELECT * FROM support_tickets WHERE id = :id"), {"id": ticket_id}).mappings().first()
    if not row:
        raise HTTPException(404, "Ticket nicht gefunden")
    return dict(row)


@router.patch("/{ticket_id}", dependencies=[Depends(require_innendienst)])
def update_ticket(ticket_id: int, req: TicketUpdate, db: Session = Depends(get_db)):
    updates = []
    params = {"id": ticket_id}
    if req.status:
        updates.append("status = :status")
        params["status"] = req.status
        if req.status == "resolved":
            updates.append("resolved_at = NOW()")
    if req.priority:
        updates.append("priority = :priority")
        params["priority"] = req.priority
    if req.admin_notes is not None:
        updates.append("admin_notes = :notes")
        params["notes"] = req.admin_notes
    if not updates:
        return {"message": "Nichts geaendert"}
    updates.append("updated_at = NOW()")
    db.execute(text(f"UPDATE support_tickets SET {', '.join(updates)} WHERE id = :id"), params)
    db.commit()
    return {"message": "Ticket aktualisiert"}
