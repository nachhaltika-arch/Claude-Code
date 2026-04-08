from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from psycopg2.extras import Json

from auth import get_current_user
from database import get_db
from services.brevo_service import BrevoService

router = APIRouter(prefix="/newsletter", tags=["Newsletter"])


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
def list_campaigns(user: dict = Depends(get_current_user), db=Depends(get_db)):
    cur = db.cursor()
    cur.execute("""
        SELECT id, title, subject, status, sent_at, brevo_campaign_id
        FROM newsletters
        ORDER BY created_at DESC
    """)
    rows = cur.fetchall()
    cur.close()
    return rows


@router.post("/campaigns", status_code=201)
def create_campaign(
    body: CampaignCreate,
    user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    cur = db.cursor()
    cur.execute(
        """
        INSERT INTO newsletters (title, subject, preview_text, html_content, json_content, status)
        VALUES (%s, %s, %s, %s, %s, 'draft')
        RETURNING *
        """,
        (body.title, body.subject, body.preview_text, body.html_content, Json(body.json_content)),
    )
    row = cur.fetchone()
    db.commit()
    cur.close()
    return row


@router.get("/campaigns/{campaign_id}")
def get_campaign(
    campaign_id: int,
    user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    cur = db.cursor()
    cur.execute("SELECT * FROM newsletters WHERE id = %s", (campaign_id,))
    row = cur.fetchone()
    cur.close()
    if not row:
        raise HTTPException(status_code=404, detail="Newsletter nicht gefunden")
    return row


@router.put("/campaigns/{campaign_id}")
def update_campaign(
    campaign_id: int,
    body: CampaignUpdate,
    user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    cur = db.cursor()

    # Nur Drafts duerfen bearbeitet werden
    cur.execute("SELECT status FROM newsletters WHERE id = %s", (campaign_id,))
    row = cur.fetchone()
    if not row:
        cur.close()
        raise HTTPException(status_code=404, detail="Newsletter nicht gefunden")
    if row["status"] != "draft":
        cur.close()
        raise HTTPException(status_code=400, detail="Nur Entwuerfe koennen bearbeitet werden")

    fields = []
    values = []
    for field in ("title", "subject", "preview_text", "html_content", "json_content"):
        value = getattr(body, field)
        if value is not None:
            fields.append(f"{field} = %s")
            values.append(Json(value) if field == "json_content" else value)

    if not fields:
        cur.close()
        raise HTTPException(status_code=400, detail="Keine Felder zum Aktualisieren angegeben")

    fields.append("updated_at = %s")
    values.append(datetime.now(timezone.utc))
    values.append(campaign_id)

    cur.execute(
        f"UPDATE newsletters SET {', '.join(fields)} WHERE id = %s RETURNING *",
        values,
    )
    updated = cur.fetchone()
    db.commit()
    cur.close()
    return updated


@router.delete("/campaigns/{campaign_id}")
def delete_campaign(
    campaign_id: int,
    user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    cur = db.cursor()
    cur.execute("SELECT id FROM newsletters WHERE id = %s", (campaign_id,))
    if not cur.fetchone():
        cur.close()
        raise HTTPException(status_code=404, detail="Newsletter nicht gefunden")
    cur.execute("DELETE FROM newsletters WHERE id = %s", (campaign_id,))
    db.commit()
    cur.close()
    return {"deleted": True}


@router.post("/campaigns/{campaign_id}/send")
def send_campaign(
    campaign_id: int,
    body: CampaignSend,
    user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    cur = db.cursor()
    cur.execute("SELECT * FROM newsletters WHERE id = %s", (campaign_id,))
    newsletter = cur.fetchone()
    if not newsletter:
        cur.close()
        raise HTTPException(status_code=404, detail="Newsletter nicht gefunden")

    # Brevo-Liste IDs aus newsletter_lists holen
    cur.execute(
        "SELECT brevo_list_id FROM newsletter_lists WHERE id = ANY(%s)",
        (body.list_ids,),
    )
    brevo_list_rows = cur.fetchall()
    if not brevo_list_rows:
        cur.close()
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
        cur.close()
        raise HTTPException(status_code=502, detail=result)

    brevo_campaign_id = result

    if body.scheduled_at:
        new_status = "scheduled"
        cur.execute(
            """
            UPDATE newsletters
            SET brevo_campaign_id = %s, status = %s, scheduled_at = %s, updated_at = %s
            WHERE id = %s
            """,
            (brevo_campaign_id, new_status, body.scheduled_at, datetime.now(timezone.utc), campaign_id),
        )
    else:
        send_result = brevo.send_campaign_now(brevo_campaign_id)
        if isinstance(send_result, str):
            cur.close()
            raise HTTPException(status_code=502, detail=send_result)
        new_status = "sent"
        now = datetime.now(timezone.utc)
        cur.execute(
            """
            UPDATE newsletters
            SET brevo_campaign_id = %s, status = %s, sent_at = %s, updated_at = %s
            WHERE id = %s
            """,
            (brevo_campaign_id, new_status, now, now, campaign_id),
        )

    db.commit()
    cur.close()
    return {"success": True, "brevo_campaign_id": brevo_campaign_id}


@router.get("/campaigns/{campaign_id}/stats")
def campaign_stats(
    campaign_id: int,
    user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    cur = db.cursor()
    cur.execute("SELECT brevo_campaign_id FROM newsletters WHERE id = %s", (campaign_id,))
    row = cur.fetchone()
    cur.close()

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
def list_lists(user: dict = Depends(get_current_user), db=Depends(get_db)):
    cur = db.cursor()
    cur.execute("""
        SELECT
            nl.id, nl.name, nl.source,
            COUNT(nc.id) AS contact_count
        FROM newsletter_lists nl
        LEFT JOIN newsletter_contacts nc ON nc.list_id = nl.id
        GROUP BY nl.id
        ORDER BY nl.created_at DESC
    """)
    rows = cur.fetchall()
    cur.close()
    return rows


@router.post("/lists", status_code=201)
def create_list(
    body: ListCreate,
    user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    brevo = BrevoService()
    brevo_list_id = brevo.create_list(body.name)
    if isinstance(brevo_list_id, str):
        raise HTTPException(status_code=502, detail=brevo_list_id)

    cur = db.cursor()
    cur.execute(
        """
        INSERT INTO newsletter_lists (name, description, source, brevo_list_id)
        VALUES (%s, %s, %s, %s)
        RETURNING *
        """,
        (body.name, body.description, body.source, brevo_list_id),
    )
    row = cur.fetchone()
    db.commit()
    cur.close()
    return row


@router.post("/lists/{list_id}/sync-crm")
def sync_crm(
    list_id: int,
    user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    cur = db.cursor()

    # Liste pruefen
    cur.execute("SELECT brevo_list_id FROM newsletter_lists WHERE id = %s", (list_id,))
    nl = cur.fetchone()
    if not nl:
        cur.close()
        raise HTTPException(status_code=404, detail="Liste nicht gefunden")

    # Alle Kunden aus der users-Tabelle holen
    cur.execute("SELECT id, email, first_name, last_name FROM users WHERE role = 'customer'")
    customers = cur.fetchall()

    brevo = BrevoService()
    synced = 0

    for c in customers:
        # Pruefen ob Kontakt bereits existiert
        cur.execute(
            "SELECT id FROM newsletter_contacts WHERE email = %s AND list_id = %s",
            (c["email"], list_id),
        )
        if cur.fetchone():
            continue

        brevo_contact_id = brevo.create_contact(
            email=c["email"],
            first_name=c.get("first_name", ""),
            last_name=c.get("last_name", ""),
            list_ids=[nl["brevo_list_id"]],
        )

        cur.execute(
            """
            INSERT INTO newsletter_contacts (email, first_name, last_name, list_id, crm_user_id, brevo_contact_id)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (
                c["email"],
                c.get("first_name"),
                c.get("last_name"),
                list_id,
                c["id"],
                brevo_contact_id if not isinstance(brevo_contact_id, str) else None,
            ),
        )
        synced += 1

    db.commit()
    cur.close()
    return {"synced_count": synced}


@router.post("/lists/{list_id}/import")
def import_contacts(
    list_id: int,
    body: ImportRequest,
    user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    cur = db.cursor()

    # Liste pruefen
    cur.execute("SELECT brevo_list_id FROM newsletter_lists WHERE id = %s", (list_id,))
    nl = cur.fetchone()
    if not nl:
        cur.close()
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

        cur.execute(
            """
            INSERT INTO newsletter_contacts (email, first_name, last_name, list_id, brevo_contact_id)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (
                contact.email,
                contact.first_name,
                contact.last_name,
                list_id,
                brevo_contact_id if not isinstance(brevo_contact_id, str) else None,
            ),
        )
        imported += 1

    db.commit()
    cur.close()
    return {"imported_count": imported}
