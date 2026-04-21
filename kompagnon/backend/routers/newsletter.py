from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from routers.auth_router import get_current_user
from database import get_db
from services.brevo_service import BrevoService

router = APIRouter(prefix="/api/newsletter", tags=["Newsletter"])


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

    brevo_list_id = brevo_list_rows[0]["brevo_list_id"]

    brevo = BrevoService()
    result = brevo.create_email_campaign(
        title=newsletter["title"],
        subject=newsletter["subject"],
        html_content=newsletter["html_content"] or "",
        list_id=brevo_list_id,
        scheduled_at=body.scheduled_at.isoformat() if body.scheduled_at else None,
    )

    if isinstance(result, str):
        raise HTTPException(status_code=502, detail=result)

    brevo_campaign_id = result
    now = datetime.now(timezone.utc)

    if body.scheduled_at:
        db.execute(text(
            "UPDATE newsletters "
            "SET brevo_campaign_id = :bcid, status = 'scheduled', scheduled_at = :sched, updated_at = :now "
            "WHERE id = :id"
        ), {"bcid": brevo_campaign_id, "sched": body.scheduled_at, "now": now, "id": campaign_id})
    else:
        send_result = brevo.send_campaign_now(brevo_campaign_id)
        if isinstance(send_result, str):
            raise HTTPException(status_code=502, detail=send_result)
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

    brevo = BrevoService()
    stats = brevo.get_campaign_stats(row["brevo_campaign_id"])
    if isinstance(stats, str):
        raise HTTPException(status_code=502, detail=stats)
    return stats


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
    brevo = BrevoService()
    brevo_list_id = brevo.create_list(body.name)
    if isinstance(brevo_list_id, str):
        raise HTTPException(status_code=502, detail=brevo_list_id)

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

    brevo = BrevoService()
    synced = 0

    for c in customers:
        exists = db.execute(
            text("SELECT id FROM newsletter_contacts WHERE email = :email AND list_id = :list_id"),
            {"email": c["email"], "list_id": list_id},
        ).mappings().fetchone()
        if exists:
            continue

        brevo_contact_id = brevo.create_contact(
            email=c["email"],
            first_name=c.get("first_name", "") or "",
            last_name=c.get("last_name", "") or "",
            list_ids=[nl["brevo_list_id"]],
        )

        db.execute(text("""
            INSERT INTO newsletter_contacts (email, first_name, last_name, list_id, crm_user_id, brevo_contact_id)
            VALUES (:email, :first_name, :last_name, :list_id, :crm_user_id, :brevo_contact_id)
        """), {
            "email": c["email"],
            "first_name": c.get("first_name"),
            "last_name": c.get("last_name"),
            "list_id": list_id,
            "crm_user_id": c["id"],
            "brevo_contact_id": brevo_contact_id if not isinstance(brevo_contact_id, str) else None,
        })
        synced += 1

    db.commit()
    return {"synced_count": synced}


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

    brevo = BrevoService()
    imported = 0

    for contact in body.contacts:
        brevo_contact_id = brevo.create_contact(
            email=contact.email,
            first_name=contact.first_name or "",
            last_name=contact.last_name or "",
            list_ids=[nl["brevo_list_id"]],
        )

        db.execute(text("""
            INSERT INTO newsletter_contacts (email, first_name, last_name, list_id, brevo_contact_id)
            VALUES (:email, :first_name, :last_name, :list_id, :brevo_contact_id)
        """), {
            "email": contact.email,
            "first_name": contact.first_name,
            "last_name": contact.last_name,
            "list_id": list_id,
            "brevo_contact_id": brevo_contact_id if not isinstance(brevo_contact_id, str) else None,
        })
        imported += 1

    db.commit()
    return {"imported_count": imported}
