import os
import hashlib
import hmac
import logging
from fastapi import APIRouter, BackgroundTasks, Request, HTTPException
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


# ── Netlify Webhook-Endpunkte ─────────────────────────────────────────────────

def _verify_netlify_signature(payload: bytes, signature: str) -> bool:
    """Verifiziert Netlify-Webhook-Signatur (optional, falls NETLIFY_WEBHOOK_SECRET gesetzt)."""
    secret = os.getenv("NETLIFY_WEBHOOK_SECRET", "")
    if not secret:
        return True
    expected = "sha256=" + hmac.new(
        secret.encode(), payload, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature or "")


async def _parse_netlify_payload(request: Request) -> dict:
    """Liest Netlify-Payload als JSON oder Form-Daten."""
    body_bytes = await request.body()
    sig = request.headers.get("x-webhook-signature", "")
    if not _verify_netlify_signature(body_bytes, sig):
        raise HTTPException(401, "Ungültige Webhook-Signatur")
    content_type = request.headers.get("content-type", "")
    if "application/json" in content_type:
        import json
        return json.loads(body_bytes)
    form = await request.form()
    return dict(form)


@router.post("/netlify/audit-anfrage")
async def netlify_audit_anfrage(
    request: Request,
    background_tasks: BackgroundTasks,
):
    """
    Netlify sendet diesen Webhook wenn jemand ein Audit-Formular ausfüllt.
    Legt Lead an und startet Audit im Hintergrund.
    """
    data = await _parse_netlify_payload(request)

    email       = (data.get("email") or "").strip().lower()
    website_url = (data.get("website_url") or data.get("url") or "").strip()
    phone       = (data.get("phone") or data.get("telefon") or "").strip()
    company     = (data.get("company") or data.get("firma") or "").strip()
    utm_source  = data.get("utm_source", "netlify_audit")

    if not email:
        raise HTTPException(400, "E-Mail fehlt")

    if website_url and not website_url.startswith("http"):
        website_url = "https://" + website_url

    db = SessionLocal()
    try:
        existing = db.execute(
            text("SELECT id FROM leads WHERE email = :email LIMIT 1"),
            {"email": email}
        ).fetchone()

        if existing:
            lead_id = existing[0]
            db.execute(text("""
                UPDATE leads
                SET website_url  = COALESCE(NULLIF(website_url,''), :url),
                    lead_source  = COALESCE(NULLIF(lead_source,''), :src),
                    updated_at   = NOW()
                WHERE id = :id
            """), {"url": website_url, "src": utm_source, "id": lead_id})
            db.commit()
        else:
            result = db.execute(text("""
                INSERT INTO leads
                  (email, website_url, phone, company_name,
                   lead_source, status, created_at, updated_at)
                VALUES
                  (:email, :url, :phone, :company,
                   :src, 'new', NOW(), NOW())
                RETURNING id
            """), {
                "email":   email,
                "url":     website_url,
                "phone":   phone,
                "company": company,
                "src":     utm_source,
            })
            lead_id = result.fetchone()[0]
            db.commit()
            logger.info(f"Netlify Audit-Webhook: Neuer Lead {lead_id} ({email})")
    finally:
        db.close()

    if website_url:
        background_tasks.add_task(
            _start_audit_background, lead_id, website_url, company or email
        )

    return {
        "status":  "ok",
        "lead_id": lead_id,
        "audit":   bool(website_url),
        "message": "Lead angelegt, Audit gestartet" if website_url else "Lead angelegt",
    }


async def _start_audit_background(lead_id: int, website_url: str, company: str):
    """Startet Audit asynchron nach Netlify-Webhook."""
    import httpx
    try:
        api_base = os.getenv("RENDER_INTERNAL_HOSTNAME", "")
        base_url = f"http://{api_base}" if api_base else os.getenv("API_BASE_URL", "http://localhost:8000")
        async with httpx.AsyncClient(timeout=10.0) as client:
            await client.post(
                f"{base_url}/api/audit/start",
                json={"website_url": website_url, "lead_id": lead_id, "company_name": company},
            )
        logger.info(f"Audit gestartet für Lead {lead_id}: {website_url}")
    except Exception as e:
        logger.warning(f"Audit-Start im Hintergrund fehlgeschlagen: {e}")


@router.post("/netlify/kontakt")
async def netlify_kontakt(request: Request):
    """
    Netlify sendet diesen Webhook bei Kontaktformular-Einsendungen.
    Legt Lead an ohne Audit zu starten.
    """
    data = await _parse_netlify_payload(request)

    email   = (data.get("email") or "").strip().lower()
    name    = (data.get("name")  or "").strip()
    phone   = (data.get("phone") or "").strip()
    message = (data.get("message") or data.get("nachricht") or "").strip()
    source  = data.get("utm_source", "netlify_kontakt")

    if not email:
        raise HTTPException(400, "E-Mail fehlt")

    db = SessionLocal()
    try:
        existing = db.execute(
            text("SELECT id FROM leads WHERE email = :email LIMIT 1"),
            {"email": email}
        ).fetchone()

        if existing:
            lead_id = existing[0]
        else:
            result = db.execute(text("""
                INSERT INTO leads
                  (email, contact_name, phone, lead_source, status,
                   notes, created_at, updated_at)
                VALUES
                  (:email, :name, :phone, :src, 'new',
                   :notes, NOW(), NOW())
                RETURNING id
            """), {
                "email": email,
                "name":  name,
                "phone": phone,
                "src":   source,
                "notes": f"Kontaktformular: {message[:500]}" if message else "",
            })
            lead_id = result.fetchone()[0]
            db.commit()
            logger.info(f"Netlify Kontakt-Webhook: Neuer Lead {lead_id} ({email})")
    finally:
        db.close()

    return {"status": "ok", "lead_id": lead_id}
