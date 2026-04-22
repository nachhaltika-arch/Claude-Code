"""
GEO Add-on Stripe Subscription Router.

Endpunkte:
  POST /api/geo-payments/{project_id}/create-subscription
  POST /api/geo-payments/webhook
  GET  /api/geo-payments/{project_id}/status
  POST /api/geo-payments/{project_id}/cancel

WICHTIG: Dieser Router ist GETRENNT von payments.py (Einmalzahlungen).
Beruehrt payments.py NICHT.
"""

import os
import json
import logging
from datetime import datetime

import stripe
from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks
from sqlalchemy.orm import Session

from database import get_db, GeoAnalysis, Project, Lead
from routers.auth_router import require_any_auth, require_admin

logger = logging.getLogger(__name__)

stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "")
STRIPE_WEBHOOK_SECRET_GEO = os.getenv("STRIPE_WEBHOOK_SECRET_GEO", "")
FRONTEND_URL = os.getenv("FRONTEND_URL", "https://kompagnon-frontend.onrender.com")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

router = APIRouter(prefix="/api/geo-payments", tags=["geo-payments"])


def _get_analysis_or_404(project_id: int, db: Session) -> GeoAnalysis:
    a = db.query(GeoAnalysis).filter(GeoAnalysis.project_id == project_id).first()
    if not a:
        raise HTTPException(404, "Keine GEO-Analyse fuer dieses Projekt gefunden")
    return a


def _get_project_lead(project_id: int, db: Session):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(404, "Projekt nicht gefunden")
    return project, project.lead


# ── 1. Subscription erstellen ────────────────────────────────────────────────

@router.post("/{project_id}/create-subscription")
async def create_geo_subscription(
    project_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_any_auth),
):
    """Erstellt eine Stripe Checkout Session fuer das GEO Add-on Abo."""
    if not stripe.api_key:
        raise HTTPException(500, "Stripe nicht konfiguriert (STRIPE_SECRET_KEY fehlt)")

    analysis = _get_analysis_or_404(project_id, db)
    project, lead = _get_project_lead(project_id, db)

    if not analysis.upsell_price or analysis.upsell_price <= 0:
        raise HTTPException(
            400,
            "Kein Preis hinterlegt. Bitte erst im Admin-Bereich den monatlichen Preis setzen.",
        )

    if analysis.subscription_status == "active":
        raise HTTPException(400, "GEO Add-on ist bereits aktiv")

    customer_email = getattr(lead, "email", "") or ""
    company_name = getattr(lead, "company_name", "") or ""

    from services.geo_stripe_helper import get_or_create_stripe_price
    try:
        price_id = get_or_create_stripe_price(analysis.upsell_price)
    except Exception as e:
        raise HTTPException(500, f"Stripe Preis konnte nicht erstellt werden: {e}")

    try:
        session = stripe.checkout.Session.create(
            payment_method_types=["card", "sepa_debit"],
            line_items=[{"price": price_id, "quantity": 1}],
            mode="subscription",
            customer_email=customer_email or None,
            metadata={
                "project_id": str(project_id),
                "addon_type": "geo",
                "company_name": company_name,
            },
            success_url=f"{FRONTEND_URL}/kundenportal?geo_success=1",
            cancel_url=f"{FRONTEND_URL}/kundenportal?geo_cancelled=1",
            locale="de",
            subscription_data={
                "metadata": {
                    "project_id": str(project_id),
                    "addon_type": "geo",
                },
            },
        )

        analysis.stripe_price_id = price_id
        db.commit()

        return {
            "checkout_url": session.url,
            "session_id": session.id,
            "price_eur": analysis.upsell_price,
        }

    except stripe.error.StripeError as e:
        logger.error("Stripe Checkout Session failed: %s", e)
        raise HTTPException(400, str(e))


# ── 2. Stripe Webhook ────────────────────────────────────────────────────────

@router.post("/webhook")
async def geo_stripe_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Verarbeitet Stripe Webhook Events fuer das GEO Add-on."""
    payload = await request.body()
    sig = request.headers.get("stripe-signature")

    if not STRIPE_WEBHOOK_SECRET_GEO:
        logger.warning("STRIPE_WEBHOOK_SECRET_GEO nicht gesetzt — Signatur wird nicht validiert")
        try:
            event = json.loads(payload)
        except Exception as e:
            logger.error("GEO Webhook Payload nicht parsbar: %s", e)
            raise HTTPException(400, "Ungueltiges Payload")
    else:
        try:
            event = stripe.Webhook.construct_event(payload, sig, STRIPE_WEBHOOK_SECRET_GEO)
        except Exception as e:
            logger.error("GEO Webhook Verifikation fehlgeschlagen: %s", e)
            raise HTTPException(400, "Webhook Fehler")

    event_type = event["type"]
    logger.info("GEO Webhook Event: %s", event_type)

    if event_type == "checkout.session.completed":
        session = event["data"]["object"]
        if session.get("metadata", {}).get("addon_type") == "geo":
            background_tasks.add_task(_handle_geo_subscription_start, session)

    elif event_type in ("customer.subscription.updated", "customer.subscription.deleted"):
        subscription = event["data"]["object"]
        if subscription.get("metadata", {}).get("addon_type") == "geo":
            background_tasks.add_task(_handle_subscription_change, subscription)

    return {"status": "ok"}


def _handle_geo_subscription_start(session: dict):
    """Nach erfolgreichem Kauf: Status setzen, GEO-Analyse + Dateien starten, E-Mail."""
    from database import SessionLocal
    db = SessionLocal()
    try:
        meta = session.get("metadata", {})
        project_id = int(meta.get("project_id", 0))
        if not project_id:
            logger.error("GEO Webhook: project_id fehlt in Metadata")
            return

        analysis = db.query(GeoAnalysis).filter(GeoAnalysis.project_id == project_id).first()
        if not analysis:
            logger.error("GEO Webhook: Keine Analyse fuer Projekt %d", project_id)
            return

        subscription_id = session.get("subscription", "")
        customer_id = session.get("customer", "")

        period_end = None
        try:
            if subscription_id:
                sub = stripe.Subscription.retrieve(subscription_id)
                period_end = datetime.fromtimestamp(sub.current_period_end)
        except Exception:
            pass

        analysis.stripe_subscription_id = subscription_id
        analysis.stripe_customer_id = customer_id
        analysis.subscription_status = "active"
        analysis.upsell_active = True
        analysis.subscription_started_at = datetime.utcnow()
        analysis.subscription_current_period_end = period_end
        analysis.monitoring_enabled = True
        db.commit()
    finally:
        db.close()

    import threading
    threading.Thread(
        target=_run_geo_automation_after_purchase,
        args=(project_id,),
        daemon=True,
    ).start()

    _send_geo_welcome_email(project_id)


def _run_geo_automation_after_purchase(project_id: int):
    """Hintergrund: GEO-Analyse + Datei-Generierung nach Subscription-Start."""
    import asyncio
    from database import SessionLocal

    try:
        db = SessionLocal()
        try:
            project = db.query(Project).filter(Project.id == project_id).first()
            if not project or not project.lead:
                return
            lead = project.lead
            website_url = getattr(lead, "website_url", "") or ""
            gewerk = getattr(lead, "trade", "") or "Handwerk"
            city = getattr(lead, "city", "") or ""
            company_name = getattr(lead, "company_name", "") or ""
            phone = getattr(lead, "phone", "") or ""
            email = getattr(lead, "email", "") or ""
        finally:
            db.close()

        if not website_url:
            logger.warning("GEO Auto-Setup: keine website_url fuer Projekt %d", project_id)
            return

        from services.geo_optimizer import GeoOptimizerAgent
        agent = GeoOptimizerAgent(api_key=ANTHROPIC_API_KEY)
        result = asyncio.run(agent.analyze(website_url, gewerk, city))

        db = SessionLocal()
        try:
            analysis = db.query(GeoAnalysis).filter(
                GeoAnalysis.project_id == project_id
            ).first()
            if not analysis:
                return
            analysis.geo_score_total = result["geo_score_total"]
            analysis.llms_txt_score = result["llms_txt_score"]
            analysis.robots_ai_score = result["robots_ai_score"]
            analysis.structured_data_score = result["structured_data_score"]
            analysis.content_depth_score = result["content_depth_score"]
            analysis.local_signal_score = result["local_signal_score"]
            analysis.raw_checks = result["raw_checks"]
            analysis.recommendations = result["recommendations"]
            analysis.status = "done"
            analysis.updated_at = datetime.utcnow()

            blocked_bots = []
            raw_checks = analysis.raw_checks or {}
            if raw_checks.get("robots_ai"):
                blocked_bots = raw_checks["robots_ai"].get("blocked_bots", [])
            db.commit()
        finally:
            db.close()

        leistungen = []
        try:
            db = SessionLocal()
            from database import Briefing
            b = db.query(Briefing).filter(Briefing.lead_id == project.lead.id).first()
            usp = ""
            if b:
                usp = getattr(b, "usp", "") or ""
                raw = getattr(b, "leistungen", "") or ""
                if raw:
                    leistungen = [l.strip() for l in raw.split(",") if l.strip()]
            db.close()
        except Exception:
            usp = ""

        from services.geo_generator import GeoGeneratorAgent
        generator = GeoGeneratorAgent(api_key=ANTHROPIC_API_KEY)
        files = generator.generate_all(
            company_name=company_name,
            gewerk=gewerk,
            city=city,
            leistungen=leistungen,
            usp=usp,
            phone=phone,
            email=email,
            website_url=website_url,
            blocked_bots=blocked_bots,
        )

        db = SessionLocal()
        try:
            analysis = db.query(GeoAnalysis).filter(
                GeoAnalysis.project_id == project_id
            ).first()
            if analysis:
                analysis.generated_files = files
                db.commit()
        finally:
            db.close()

        logger.info("GEO Auto-Setup nach Kauf abgeschlossen: Projekt %d", project_id)

    except Exception as e:
        logger.error("GEO Auto-Setup fehlgeschlagen fuer Projekt %d: %s", project_id, e)


def _handle_subscription_change(subscription: dict):
    """Status-Aenderungen (Kuendigung, Zahlungsfehler) in DB aktualisieren."""
    from database import SessionLocal
    db = SessionLocal()
    try:
        sub_id = subscription.get("id", "")
        new_status = subscription.get("status", "")
        meta = subscription.get("metadata", {})
        project_id_str = meta.get("project_id", "")
        project_id = int(project_id_str) if project_id_str else 0

        if not project_id:
            analysis = db.query(GeoAnalysis).filter(
                GeoAnalysis.stripe_subscription_id == sub_id
            ).first()
        else:
            analysis = db.query(GeoAnalysis).filter(
                GeoAnalysis.project_id == project_id
            ).first()

        if not analysis:
            logger.warning("GEO Webhook: Analyse nicht gefunden fuer Sub %s", sub_id)
            return

        analysis.subscription_status = new_status
        if new_status in ("canceled", "unpaid"):
            analysis.upsell_active = False
            analysis.subscription_canceled_at = datetime.utcnow()
            analysis.monitoring_enabled = False

        period_end_ts = subscription.get("current_period_end")
        if period_end_ts:
            analysis.subscription_current_period_end = datetime.fromtimestamp(period_end_ts)

        db.commit()
        logger.info("GEO Subscription Status: %s -> %s", sub_id, new_status)

    except Exception as e:
        logger.error("GEO Subscription Change Handler Fehler: %s", e)
    finally:
        db.close()


def _send_geo_welcome_email(project_id: int):
    """Willkommens-E-Mail nach GEO Add-on Kauf."""
    from database import SessionLocal
    db = SessionLocal()
    try:
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project or not project.lead:
            return
        lead = project.lead
        email = getattr(lead, "email", "") or ""
        name = getattr(lead, "company_name", "") or ""
        if not email:
            return

        try:
            from services.email import send_email
        except ImportError:
            logger.warning("services.email nicht verfuegbar")
            return

        portal_url = f"{FRONTEND_URL}/kundenportal"
        html = f"""
<div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto">
  <div style="background:#008eaa;padding:24px;border-radius:12px 12px 0 0">
    <h2 style="color:white;margin:0">Willkommen beim KOMPAGNON KI-Sichtbarkeits-Add-on</h2>
  </div>
  <div style="padding:24px;background:#fff;border:1px solid #e5e7eb">
    <p>Hallo {name},</p>
    <p>vielen Dank fuer Ihre Buchung. Das Add-on ist jetzt aktiv.</p>
    <p><strong>Was wir fuer Sie tun:</strong></p>
    <ul>
      <li>GEO-Analyse Ihrer Website laeuft gerade (fertig in ca. 5 Minuten)</li>
      <li>llms.txt, schema.org-Daten und Ground Page werden automatisch erstellt</li>
      <li>Monatliches Monitoring startet ab dem 1. des naechsten Monats</li>
    </ul>
    <p>Ihre Ergebnisse finden Sie im Kundenportal:</p>
    <p><a href="{portal_url}" style="display:inline-block;background:#008eaa;color:white;padding:12px 24px;text-decoration:none;border-radius:8px;font-weight:bold">Zum Kundenportal &rarr;</a></p>
    <p>Bei Fragen stehen wir Ihnen jederzeit zur Verfuegung.</p>
    <p>Mit freundlichen Gruessen<br>Ihr KOMPAGNON-Team</p>
  </div>
</div>"""

        ok = send_email(
            to_email=email,
            subject="KOMPAGNON KI-Sichtbarkeit — Ihr Add-on ist aktiv",
            html_body=html,
        )
        if ok:
            logger.info("GEO Willkommens-E-Mail an %s versandt", email)
        else:
            logger.warning("GEO Willkommens-E-Mail an %s fehlgeschlagen", email)
    except Exception as e:
        logger.error("GEO Welcome E-Mail fehlgeschlagen: %s", e)
    finally:
        db.close()


# ── 3. Status abrufen ────────────────────────────────────────────────────────

@router.get("/{project_id}/status")
def get_subscription_status(
    project_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_any_auth),
):
    """Gibt den aktuellen Abo-Status zurueck."""
    analysis = db.query(GeoAnalysis).filter(GeoAnalysis.project_id == project_id).first()
    if not analysis:
        return {"subscription_status": None, "upsell_active": False}

    return {
        "subscription_status": analysis.subscription_status,
        "upsell_active": bool(analysis.upsell_active),
        "upsell_price": analysis.upsell_price,
        "subscription_started_at": analysis.subscription_started_at.isoformat() if analysis.subscription_started_at else None,
        "subscription_current_period_end": analysis.subscription_current_period_end.isoformat() if analysis.subscription_current_period_end else None,
        "geo_score_total": analysis.geo_score_total,
        "geo_status": analysis.status,
    }


# ── 4. Kuendigung (Admin only) ───────────────────────────────────────────────

@router.post("/{project_id}/cancel")
def cancel_geo_subscription(
    project_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_admin),
):
    """Admin: GEO Add-on Subscription kuendigen (zum Periodenende)."""
    analysis = _get_analysis_or_404(project_id, db)
    if not analysis.stripe_subscription_id:
        raise HTTPException(400, "Keine aktive Subscription gefunden")

    from services.geo_stripe_helper import cancel_subscription
    success = cancel_subscription(analysis.stripe_subscription_id)
    if success:
        analysis.subscription_status = "cancel_at_period_end"
        db.commit()
        return {"status": "ok", "message": "Kuendigung zum Periodenende eingereicht"}
    else:
        raise HTTPException(500, "Kuendigung bei Stripe fehlgeschlagen")
