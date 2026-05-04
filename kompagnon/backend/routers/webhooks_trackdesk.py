"""
Trackdesk Webhook-Integration
POST /api/webhooks/trackdesk — öffentlicher Webhook (HMAC-Signatur optional)
GET  /api/affiliate-conversions — admin list for dashboard

Einrichten in Trackdesk:
  Tools → Webhooks → Add new webhook
  URL: https://claude-code-znq2.onrender.com/api/webhooks/trackdesk
  Events: conversion_created, conversion_status_changed, affiliate_created
"""
import hashlib
import hmac
import json
import logging
import os

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import text
from sqlalchemy.orm import Session

from database import get_db
from routers.auth_router import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(tags=["webhooks-trackdesk"])

TRACKDESK_SECRET = os.getenv("TRACKDESK_WEBHOOK_SECRET", "")


def _verify_signature(body: bytes, signature: str) -> bool:
    """Trackdesk Webhook-Signatur prüfen (falls konfiguriert)."""
    if not TRACKDESK_SECRET:
        return True  # kein Secret → offen (nicht empfohlen)
    if not signature:
        return False
    expected = hmac.new(
        TRACKDESK_SECRET.encode(),
        body,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, signature)


def _extract_affiliate(payload: dict) -> dict:
    """Trackdesk Payload → normalisierte Affiliate-Daten."""
    aff = payload.get("affiliate") or {}
    return {
        "id":    str(aff.get("id", "") or payload.get("affiliate_id", "") or ""),
        "email": aff.get("email", "") or payload.get("affiliate_email", "") or "",
        "name":  aff.get("name", "") or payload.get("affiliate_name", "") or "",
    }


def _extract_customer(payload: dict) -> dict:
    """Trackdesk Payload → normalisierte Kunden-Daten."""
    cust = payload.get("customer") or payload.get("metadata") or {}
    conv = payload.get("conversion") or payload
    return {
        "email": (cust.get("email") or conv.get("customer_email") or payload.get("email", "") or ""),
        "name":  (cust.get("name")  or conv.get("customer_name")  or payload.get("name",  "") or ""),
    }


@router.post("/api/webhooks/trackdesk")
async def trackdesk_webhook(request: Request, db: Session = Depends(get_db)):
    """Hauptendpunkt für alle Trackdesk-Webhook-Events."""
    body = await request.body()
    signature = request.headers.get("X-Trackdesk-Signature", "")

    # Signatur prüfen (nur wenn Secret gesetzt)
    if TRACKDESK_SECRET and not _verify_signature(body, signature):
        logger.warning("Trackdesk: ungültige Webhook-Signatur")
        raise HTTPException(status_code=401, detail="Ungültige Signatur")

    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Ungültiges JSON")

    event_type = payload.get("event") or payload.get("type") or "unknown"
    td_id = (
        payload.get("id")
        or payload.get("conversion_id")
        or payload.get("click_id")
        or payload.get("affiliate_id")
        or f"evt_{event_type}_{hashlib.md5(body).hexdigest()[:16]}"
    )
    td_id = str(td_id)

    logger.info(f"Trackdesk Webhook: event={event_type} id={td_id}")

    # Raw Payload speichern / upserten
    try:
        db.execute(text("""
            INSERT INTO affiliate_conversions
                (trackdesk_id, event_type, raw_payload, received_at)
            VALUES (:tid, :event, :payload, NOW())
            ON CONFLICT (trackdesk_id) DO UPDATE
                SET event_type = EXCLUDED.event_type,
                    raw_payload = EXCLUDED.raw_payload,
                    received_at = NOW()
        """), {
            "tid":     td_id,
            "event":   event_type,
            "payload": json.dumps(payload, ensure_ascii=False),
        })
        db.commit()
    except Exception as e:
        logger.warning(f"Trackdesk: Payload-Speicherung fehlgeschlagen: {e}")
        try:
            db.rollback()
        except Exception:
            pass

    # Event-spezifische Verarbeitung
    try:
        if event_type == "conversion_created":
            _handle_conversion(payload, td_id, db)
        elif event_type == "conversion_status_changed":
            _handle_conversion_status(payload, td_id, db)
        elif event_type == "affiliate_created":
            aff = _extract_affiliate(payload)
            logger.info(f"Trackdesk: neuer Affiliate {aff.get('name')} ({aff.get('email')})")
        elif event_type == "click_created":
            logger.info(f"Trackdesk: Klick von Affiliate {payload.get('affiliate_id', '?')}")
    except Exception as e:
        logger.error(f"Trackdesk Event-Verarbeitung fehlgeschlagen: {e}")

    return {"received": True, "event": event_type, "id": td_id}


def _handle_conversion(payload: dict, td_id: str, db: Session):
    """
    Neue Conversion: Lead anlegen oder bestehenden Lead verknüpfen.
    Trackdesk liefert: affiliate, customer, conversion_value, etc.
    """
    affiliate = _extract_affiliate(payload)
    customer  = _extract_customer(payload)
    conversion = payload.get("conversion") or payload

    try:
        conv_value = float(conversion.get("value") or conversion.get("revenue") or 0)
    except (TypeError, ValueError):
        conv_value = 0.0
    try:
        commission = float(conversion.get("commission") or payload.get("commission", 0))
    except (TypeError, ValueError):
        commission = 0.0

    logger.info(
        f"Trackdesk Conversion: Affiliate={affiliate['name']} "
        f"Kunde={customer['email']} Wert={conv_value}€"
    )

    # Affiliate-Daten in affiliate_conversions updaten
    db.execute(text("""
        UPDATE affiliate_conversions SET
          affiliate_id     = :aff_id,
          affiliate_email  = :aff_email,
          affiliate_name   = :aff_name,
          customer_email   = :cust_email,
          customer_name    = :cust_name,
          conversion_value = :conv_value,
          commission_value = :commission,
          status           = 'created'
        WHERE trackdesk_id = :tid
    """), {
        "aff_id":     affiliate["id"],
        "aff_email":  affiliate["email"],
        "aff_name":   affiliate["name"],
        "cust_email": customer["email"],
        "cust_name":  customer["name"],
        "conv_value": conv_value,
        "commission": commission,
        "tid":        td_id,
    })

    # Existierenden Lead per E-Mail suchen
    existing_lead = None
    if customer["email"]:
        existing_lead = db.execute(
            text("SELECT id FROM leads WHERE email = :email LIMIT 1"),
            {"email": customer["email"]},
        ).fetchone()

    lead_id = None
    if existing_lead:
        lead_id = existing_lead.id
        db.execute(text("""
            UPDATE leads SET
              affiliate_id    = :aff_id,
              affiliate_name  = :aff_name,
              kampagne_quelle = COALESCE(kampagne_quelle, 'partner'),
              utm_source      = COALESCE(utm_source, 'trackdesk')
            WHERE id = :lid
        """), {
            "aff_id":   affiliate["id"],
            "aff_name": affiliate["name"],
            "lid":      lead_id,
        })
        logger.info(f"Trackdesk: Lead {lead_id} mit Affiliate {affiliate['name']} verknüpft")
    elif customer["email"] or customer["name"]:
        # Neuen Lead anlegen
        try:
            result = db.execute(text("""
                INSERT INTO leads
                  (email, display_name, company_name,
                   affiliate_id, affiliate_name,
                   kampagne_quelle, utm_source,
                   status, lead_source, created_at, updated_at)
                VALUES
                  (:email, :name, :company,
                   :aff_id, :aff_name,
                   'partner', 'trackdesk',
                   'new', 'trackdesk', NOW(), NOW())
                RETURNING id
            """), {
                "email":    customer["email"] or None,
                "name":     customer["name"] or "",
                "company":  customer["name"] or "",
                "aff_id":   affiliate["id"],
                "aff_name": affiliate["name"],
            })
            row = result.fetchone()
            if row:
                lead_id = row[0]
                logger.info(f"Trackdesk: neuer Lead #{lead_id} via Affiliate {affiliate['name']}")
        except Exception as e:
            logger.error(f"Trackdesk: Lead-Anlage fehlgeschlagen: {e}")
            try:
                db.rollback()
            except Exception:
                pass

    if lead_id:
        db.execute(text("""
            UPDATE affiliate_conversions SET lead_id = :lid
            WHERE trackdesk_id = :tid
        """), {"lid": lead_id, "tid": td_id})

    db.commit()


def _handle_conversion_status(payload: dict, td_id: str, db: Session):
    """Conversion-Status aktualisieren (approved/rejected/pending)."""
    status = payload.get("status") or (payload.get("conversion") or {}).get("status") or ""
    db.execute(text("""
        UPDATE affiliate_conversions SET status = :status
        WHERE trackdesk_id = :tid
    """), {"status": status, "tid": td_id})
    db.commit()
    logger.info(f"Trackdesk: Conversion {td_id} → Status {status}")


# ── Admin List Endpoint ────────────────────────────────────────────

@router.get("/api/affiliate-conversions")
def list_conversions(
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    """Alle Affiliate-Conversions — für Dashboard und Admin-Übersicht."""
    rows = db.execute(text("""
        SELECT ac.id, ac.trackdesk_id, ac.event_type,
               ac.affiliate_id, ac.affiliate_email, ac.affiliate_name,
               ac.customer_email, ac.customer_name,
               ac.conversion_value, ac.commission_value, ac.currency,
               ac.status, ac.lead_id, ac.received_at,
               l.company_name AS lead_company_name
        FROM affiliate_conversions ac
        LEFT JOIN leads l ON ac.lead_id = l.id
        ORDER BY ac.received_at DESC
        LIMIT 200
    """)).fetchall()
    return [dict(r._mapping) for r in rows]
