import os
import logging
from fastapi import APIRouter, Request, HTTPException
from sqlalchemy import text
from database import SessionLocal

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/webhooks", tags=["webhooks"])

WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "")


def _check_secret(request: Request):
    if WEBHOOK_SECRET:
        token = request.headers.get("X-Webhook-Secret", "")
        if token != WEBHOOK_SECRET:
            raise HTTPException(403, "Ungueltiger Webhook-Token")


def _upsert_lead(source: str, company: str, email: str,
                 phone: str, website: str, notes: str = ""):
    db = SessionLocal()
    try:
        existing = None
        if email:
            existing = db.execute(text(
                "SELECT id FROM leads WHERE email = :e"
            ), {"e": email}).fetchone()
        if not existing and website:
            existing = db.execute(text(
                "SELECT id FROM leads WHERE website_url ILIKE :w"
            ), {"w": f"%{website}%"}).fetchone()

        if existing:
            db.execute(text(
                "UPDATE leads SET lead_source=:s, updated_at=NOW() WHERE id=:id"
            ), {"s": source, "id": existing.id})
            db.commit()
            return {"action": "updated", "lead_id": existing.id}
        else:
            db.execute(text("""
                INSERT INTO leads
                (company_name, email, phone, website_url, lead_source,
                 status, notes, created_at, updated_at)
                VALUES (:c, :e, :p, :w, :s, 'neu', :n, NOW(), NOW())
            """), {"c": company or "Unbekannt", "e": email,
                   "p": phone, "w": website, "s": source, "n": notes})
            db.commit()
            row = db.execute(text(
                "SELECT id FROM leads ORDER BY id DESC LIMIT 1"
            )).fetchone()
            db.execute(text("""
                INSERT INTO webhook_log (source, email, company, created_at)
                VALUES (:s, :e, :c, NOW())
            """), {"s": source, "e": email, "c": company or ""})
            db.commit()
            return {"action": "created", "lead_id": row.id if row else None}
    except Exception as ex:
        logger.error(f"Webhook upsert Fehler: {ex}")
        return {"action": "error"}
    finally:
        db.close()


@router.post("/facebook")
async def webhook_facebook(request: Request):
    _check_secret(request)
    try:
        body = await request.json()
        field_data = (body.get("entry", [{}])[0]
                      .get("changes", [{}])[0]
                      .get("value", {})
                      .get("field_data", []))
        fields = {f["name"]: f["values"][0] for f in field_data if f.get("values")}
        return _upsert_lead("facebook",
            fields.get("company_name", fields.get("full_name", "")),
            fields.get("email", ""), fields.get("phone_number", ""), "")
    except Exception as e:
        logger.error(f"Facebook Webhook Fehler: {e}")
        return {"ok": True}


@router.post("/linkedin")
async def webhook_linkedin(request: Request):
    _check_secret(request)
    try:
        b = await request.json()
        name = f"{b.get('firstName', '')} {b.get('lastName', '')}".strip()
        return _upsert_lead("linkedin", b.get("companyName", name),
            b.get("emailAddress", ""), b.get("phoneNumber", ""), "")
    except Exception as e:
        logger.error(f"LinkedIn Webhook Fehler: {e}")
        return {"ok": True}


@router.post("/google")
async def webhook_google(request: Request):
    _check_secret(request)
    try:
        b = await request.json()
        cols = {c["column_id"]: c.get("string_value", "")
                for c in b.get("user_column_data", [])}
        return _upsert_lead("google",
            cols.get("FULL_NAME", ""), cols.get("EMAIL", ""),
            cols.get("PHONE_NUMBER", ""), "")
    except Exception as e:
        logger.error(f"Google Webhook Fehler: {e}")
        return {"ok": True}


@router.post("/postkarte")
async def webhook_postkarte(request: Request):
    _check_secret(request)
    try:
        b = await request.json()
        return _upsert_lead("postkarte", b.get("firma", ""),
            b.get("email", ""), b.get("telefon", ""), b.get("website", ""))
    except Exception as e:
        logger.error(f"Postkarte Webhook Fehler: {e}")
        return {"ok": True}


@router.post("/telefon")
async def webhook_telefon(request: Request):
    _check_secret(request)
    try:
        b = await request.json()
        d = b.get("extracted_data", {})
        notes = b.get("transcript", "")[:500]
        return _upsert_lead("telefon", d.get("firma", ""),
            d.get("email", ""), d.get("telefon", ""), "", notes)
    except Exception as e:
        logger.error(f"Telefon Webhook Fehler: {e}")
        return {"ok": True}


@router.get("/log")
def get_webhook_log(limit: int = 50):
    db = SessionLocal()
    try:
        rows = db.execute(text(
            "SELECT * FROM webhook_log ORDER BY created_at DESC LIMIT :l"
        ), {"l": limit}).fetchall()
        return [dict(r._mapping) for r in rows]
    finally:
        db.close()
