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
from routers.auth_router import get_current_user

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
    page_name: str = ""
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
        "INSERT INTO support_tickets (ticket_number, user_email, user_name, type, priority, status, title, description, page_url, page_name, browser_info, screenshot_base64) "
        "VALUES (:nr, :email, :name, :type, :prio, 'open', :title, :desc, :page, :page_name, :browser, :screenshot)"
    ), {"nr": nr, "email": req.user_email, "name": req.user_name, "type": req.type, "prio": req.priority,
        "title": req.title, "desc": req.description, "page": req.page_url, "page_name": req.page_name,
        "browser": req.browser_info, "screenshot": req.screenshot_base64})
    db.commit()
    return {"ticket_number": nr, "message": "Ticket erstellt"}


@router.get("/my")
def my_tickets(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """Tickets des eingeloggten Benutzers (nach E-Mail)."""
    rows = db.execute(
        text("SELECT * FROM support_tickets WHERE user_email = :email ORDER BY created_at DESC LIMIT 50"),
        {"email": current_user.email},
    ).mappings().all()
    return [dict(r) for r in rows]


@router.get("/")
def list_tickets(status: str = Query(None), type: str = Query(None), priority: str = Query(None), db: Session = Depends(get_db)):
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


@router.get("/{ticket_id}")
def get_ticket(ticket_id: int, db: Session = Depends(get_db)):
    row = db.execute(text("SELECT * FROM support_tickets WHERE id = :id"), {"id": ticket_id}).mappings().first()
    if not row:
        raise HTTPException(404, "Ticket nicht gefunden")
    return dict(row)


@router.patch("/{ticket_id}")
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
