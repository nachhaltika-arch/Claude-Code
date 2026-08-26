from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from routers.auth_router import get_current_user, require_innendienst
from database import get_db
from services.brevo_service import BrevoError, BrevoService

# Bei Massenimporten werden nicht alle Fehler zurueckgemeldet — eine Handvoll
# reicht, um die Ursache zu erkennen, ohne die Antwort aufzublaehen.
MAX_REPORTED_ERRORS = 10


@contextmanager
def _brevo():
    """
    Uebersetzt Brevo-Fehler in HTTP-Antworten und schliesst die Verbindung.

    503, wenn der Dienst gar nicht einsatzbereit ist (fehlender Schluessel) —
    502, wenn Brevo selbst ablehnt oder nicht erreichbar ist.
    """
    try:
        service = BrevoService()
    except BrevoError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    try:
        yield service
    except BrevoError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    finally:
        service.close()


# Innendienst-Bestand (L-67, 22.08.2026). Die Sperre haengt am **Router**,
# nicht je Route: Sonst ist die naechste Route, die jemand hinzufuegt, wieder
# offen — genau die Bauart, die am 19.08. 55 offene Werkzeug-Routen erzeugt
# hat (L-51). Vor dem Setzen gemessen, wer diese Adressen aufruft:
# ausschliesslich Innendienst-Bildschirme, kein Pfad unter `pages/customer/`.
router = APIRouter(prefix="/api/newsletter", tags=["Newsletter"],
                    dependencies=[Depends(require_innendienst)])


# ---------------------------------------------------------------------------
# Pydantic Request-/Response-Modelle
# ---------------------------------------------------------------------------

class CampaignCreate(BaseModel):
    title: str
    subject: str
    preview_text: Optional[str] = None
    html_content: Optional[str] = None
    json_content: Optional[dict] = None


class CampaignUpdate(BaseModel):
    title: Optional[str] = None
    subject: Optional[str] = None
    preview_text: Optional[str] = None
    html_content: Optional[str] = None
    json_content: Optional[dict] = None


class CampaignSend(BaseModel):
    list_ids: list[int]
    scheduled_at: Optional[datetime] = None


class ListCreate(BaseModel):
    name: str
    description: Optional[str] = None
    source: Optional[str] = "manual"


class ContactItem(BaseModel):
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None


class ImportRequest(BaseModel):
    contacts: list[ContactItem]


# ---------------------------------------------------------------------------
# Campaigns
# ---------------------------------------------------------------------------

@router.get("/campaigns")
def list_campaigns(user=Depends(get_current_user), db: Session = Depends(get_db)):
    rows = db.execute(text(
        "SELECT id, title, subject, preview_text, status, brevo_campaign_id, "
        "scheduled_at, sent_at, created_at, updated_at "
        "FROM newsletters ORDER BY created_at DESC"
    )).mappings().all()
    return [dict(r) for r in rows]


@router.post("/campaigns", status_code=201)
def create_campaign(
    body: CampaignCreate,
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    row = db.execute(text("""
        INSERT INTO newsletters (title, subject, preview_text, html_content, json_content, status)
        VALUES (:title, :subject, :preview_text, :html_content, CAST(:json_content AS JSONB), 'draft')
        RETURNING *
    """), {
        "title": body.title,
        "subject": body.subject,
        "preview_text": body.preview_text,
        "html_content": body.html_content,
        "json_content": str(body.json_content) if body.json_content else None,
    }).mappings().fetchone()
    db.commit()
    return dict(row)


@router.put("/campaigns/{campaign_id}")
def update_campaign(
    campaign_id: int,
    body: CampaignUpdate,
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    existing = db.execute(
        text("SELECT status FROM newsletters WHERE id = :id"),
        {"id": campaign_id},
    ).mappings().fetchone()

    if not existing:
        raise HTTPException(status_code=404, detail="Newsletter nicht gefunden")
    if existing["status"] != "draft":
        raise HTTPException(status_code=400, detail="Nur Entwuerfe koennen bearbeitet werden")

    fields = []
    values: dict = {}
    for field in ("title", "subject", "preview_text", "html_content"):
        value = getattr(body, field)
        if value is not None:
            fields.append(f"{field} = :{field}")
            values[field] = value
    if body.json_content is not None:
        fields.append("json_content = CAST(:json_content AS JSONB)")
        values["json_content"] = str(body.json_content)

    if not fields:
        raise HTTPException(status_code=400, detail="Keine Felder zum Aktualisieren angegeben")

    fields.append("updated_at = :updated_at")
    values["updated_at"] = datetime.now(timezone.utc)
    values["id"] = campaign_id

    row = db.execute(
        text(f"UPDATE newsletters SET {', '.join(fields)} WHERE id = :id RETURNING *"),
        values,
    ).mappings().fetchone()
    db.commit()
    return dict(row)


@router.post("/campaigns/{campaign_id}/send")
def send_campaign(
    campaign_id: int,
    body: CampaignSend,
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    newsletter = db.execute(
        text("SELECT * FROM newsletters WHERE id = :id"),
        {"id": campaign_id},
    ).mappings().fetchone()
    if not newsletter:
        raise HTTPException(status_code=404, detail="Newsletter nicht gefunden")

    brevo_list_rows = db.execute(
        text("SELECT brevo_list_id FROM newsletter_lists WHERE id = ANY(:ids)"),
        {"ids": body.list_ids},
    ).mappings().all()
    if not brevo_list_rows:
        raise HTTPException(status_code=400, detail="Keine gueltigen Listen gefunden")

    # **Alle gewaehlten Listen, nicht die erste (26.08.2026).** Hier stand
    # `brevo_list_rows[0]`: Wer drei Listen waehlte, erreichte eine — still,
    # ohne Fehler, und die Antwort meldete Erfolg. Aufgefallen beim
    # Anschliessen des Senden-Knopfs (L-105), also bevor der erste echte
    # Rundbrief hinausging.
    brevo_list_ids = [z["brevo_list_id"] for z in brevo_list_rows
                      if z["brevo_list_id"]]
    if not brevo_list_ids:
        raise HTTPException(status_code=400,
                            detail="Die gewählten Listen haben keine "
                                   "Brevo-Kennung — bitte zuerst abgleichen.")

    with _brevo() as brevo:
        brevo_campaign_id = brevo.create_email_campaign(
            title=newsletter["title"],
            subject=newsletter["subject"],
            html_content=newsletter["html_content"] or "",
            list_ids=brevo_list_ids,
            scheduled_at=body.scheduled_at.isoformat() if body.scheduled_at else None,
        )

        now = datetime.now(timezone.utc)

        if body.scheduled_at:
            db.execute(text(
                "UPDATE newsletters "
                "SET brevo_campaign_id = :bcid, status = 'scheduled', scheduled_at = :sched, updated_at = :now "
                "WHERE id = :id"
            ), {"bcid": brevo_campaign_id, "sched": body.scheduled_at, "now": now, "id": campaign_id})
        else:
            # Erst senden, dann als gesendet vermerken. Wirft der Versand, bleibt
            # der Status stehen — frueher wurde er trotzdem auf 'sent' gesetzt.
            brevo.send_campaign_now(brevo_campaign_id)
            db.execute(text(
                "UPDATE newsletters "
                "SET brevo_campaign_id = :bcid, status = 'sent', sent_at = :now, updated_at = :now "
                "WHERE id = :id"
            ), {"bcid": brevo_campaign_id, "now": now, "id": campaign_id})

    db.commit()
    return {"success": True, "brevo_campaign_id": brevo_campaign_id}


@router.get("/campaigns/{campaign_id}/stats")
def campaign_stats(
    campaign_id: int,
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    row = db.execute(
        text("SELECT brevo_campaign_id FROM newsletters WHERE id = :id"),
        {"id": campaign_id},
    ).mappings().fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Newsletter nicht gefunden")
    if not row["brevo_campaign_id"]:
        raise HTTPException(status_code=400, detail="Kampagne wurde noch nicht an Brevo gesendet")

    with _brevo() as brevo:
        return brevo.get_campaign_stats(row["brevo_campaign_id"])


# ---------------------------------------------------------------------------
# Lists
# ---------------------------------------------------------------------------

@router.get("/lists")
def list_lists(user=Depends(get_current_user), db: Session = Depends(get_db)):
    rows = db.execute(text("""
        SELECT nl.id, nl.name, nl.brevo_list_id, nl.description, nl.source, nl.created_at,
               COUNT(nc.id) AS contact_count
        FROM newsletter_lists nl
        LEFT JOIN newsletter_contacts nc ON nc.list_id = nl.id
        GROUP BY nl.id
        ORDER BY nl.created_at DESC
    """)).mappings().all()
    return [dict(r) for r in rows]


@router.post("/lists", status_code=201)
def create_list(
    body: ListCreate,
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    with _brevo() as brevo:
        brevo_list_id = brevo.create_list(body.name)

    row = db.execute(text("""
        INSERT INTO newsletter_lists (name, description, source, brevo_list_id)
        VALUES (:name, :description, :source, :brevo_list_id)
        RETURNING *
    """), {
        "name": body.name,
        "description": body.description,
        "source": body.source,
        "brevo_list_id": brevo_list_id,
    }).mappings().fetchone()
    db.commit()
    return dict(row)


@router.post("/lists/{list_id}/sync-crm")
def sync_crm(
    list_id: int,
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    nl = db.execute(
        text("SELECT brevo_list_id FROM newsletter_lists WHERE id = :id"),
        {"id": list_id},
    ).mappings().fetchone()
    if not nl:
        raise HTTPException(status_code=404, detail="Liste nicht gefunden")

    customers = db.execute(
        text("SELECT id, email, first_name, last_name FROM users WHERE role = 'customer'")
    ).mappings().all()

    synced = 0
    failed = []

    with _brevo() as brevo:
        for c in customers:
            exists = db.execute(
                text("SELECT id FROM newsletter_contacts WHERE email = :email AND list_id = :list_id"),
                {"email": c["email"], "list_id": list_id},
            ).mappings().fetchone()
            if exists:
                continue

            # Ein abgelehnter Kontakt darf den Rest des Laufs nicht abbrechen —
            # aber er wird gemeldet und NICHT als synchronisiert eingetragen.
            try:
                brevo_contact_id = brevo.create_contact(
                    email=c["email"],
                    first_name=c.get("first_name", "") or "",
                    last_name=c.get("last_name", "") or "",
                    list_ids=[nl["brevo_list_id"]],
                )
            except BrevoError as exc:
                failed.append({"email": c["email"], "reason": str(exc)})
                continue

            db.execute(text("""
                INSERT INTO newsletter_contacts (email, first_name, last_name, list_id, crm_user_id, brevo_contact_id)
                VALUES (:email, :first_name, :last_name, :list_id, :crm_user_id, :brevo_contact_id)
            """), {
                "email": c["email"],
                "first_name": c.get("first_name"),
                "last_name": c.get("last_name"),
                "list_id": list_id,
                "crm_user_id": c["id"],
                "brevo_contact_id": brevo_contact_id,
            })
            synced += 1

    db.commit()
    return {
        "synced_count": synced,
        "failed_count": len(failed),
        "errors": failed[:MAX_REPORTED_ERRORS],
    }


@router.post("/lists/{list_id}/import")
def import_contacts(
    list_id: int,
    body: ImportRequest,
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    nl = db.execute(
        text("SELECT brevo_list_id FROM newsletter_lists WHERE id = :id"),
        {"id": list_id},
    ).mappings().fetchone()
    if not nl:
        raise HTTPException(status_code=404, detail="Liste nicht gefunden")

    imported = 0
    failed = []

    with _brevo() as brevo:
        for contact in body.contacts:
            # Wie beim CRM-Abgleich: eine unbrauchbare Adresse stoppt den Import
            # nicht, wird aber gezaehlt statt mit leerer Brevo-ID abgelegt.
            try:
                brevo_contact_id = brevo.create_contact(
                    email=contact.email,
                    first_name=contact.first_name or "",
                    last_name=contact.last_name or "",
                    list_ids=[nl["brevo_list_id"]],
                )
            except BrevoError as exc:
                failed.append({"email": contact.email, "reason": str(exc)})
                continue

            db.execute(text("""
                INSERT INTO newsletter_contacts (email, first_name, last_name, list_id, brevo_contact_id)
                VALUES (:email, :first_name, :last_name, :list_id, :brevo_contact_id)
            """), {
                "email": contact.email,
                "first_name": contact.first_name,
                "last_name": contact.last_name,
                "list_id": list_id,
                "brevo_contact_id": brevo_contact_id,
            })
            imported += 1

    db.commit()
    return {
        "imported_count": imported,
        "failed_count": len(failed),
        "errors": failed[:MAX_REPORTED_ERRORS],
    }
