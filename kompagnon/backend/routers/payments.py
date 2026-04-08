"""
Stripe payment routes for KOMPAGNON checkout.
Creates Checkout Sessions, handles webhooks, returns session status.
"""
import os
import logging
import secrets
import threading
from datetime import datetime

import stripe
from fastapi import APIRouter, Request, HTTPException, Depends
from sqlalchemy.orm import Session

from database import Lead, User, Project, get_db

try:
    from seed_checklists import create_project_checklists
except ImportError:
    create_project_checklists = None

logger = logging.getLogger(__name__)

stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "")
WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")
FRONTEND_URL = os.getenv("FRONTEND_URL", "https://kompagnon-frontend.onrender.com")

router = APIRouter(prefix="/api/payments", tags=["payments"])

PACKAGE_NAMES = {
    "starter":   "Starter (5 Seiten · 1.500 EUR)",
    "kompagnon": "KOMPAGNON (8 Seiten · 2.000 EUR)",
    "premium":   "Premium (12 Seiten · 2.800 EUR)",
}

PACKAGES = {
    "starter": {
        "name": "Starter",
        "price": 150000,
        "description": "5 Seiten, SEO Basic, Mobiloptimierung, 14 Tage",
    },
    "kompagnon": {
        "name": "Kompagnon",
        "price": 200000,
        "description": "8 Seiten, SEO + GEO, Workshop, Nachbetreuung",
    },
    "premium": {
        "name": "Premium",
        "price": 280000,
        "description": "12 Seiten, Shop-Ready, Fotoshooting, 3 Monate Betreuung",
    },
}


@router.get("/packages")
def get_packages():
    return PACKAGES


@router.post("/create-checkout")
async def create_checkout(request: Request):
    body = await request.json()
    package_id = body.get("package", "kompagnon")
    customer_email = body.get("email", "")
    customer_name = body.get("name", "")
    company_name = body.get("company", "")
    website_url = body.get("website_url", "")
    phone = body.get("phone", "")

    package = PACKAGES.get(package_id)
    if not package:
        raise HTTPException(400, "Ungueltiges Paket")

    if not stripe.api_key:
        raise HTTPException(500, "Stripe nicht konfiguriert")

    try:
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price_data": {
                    "currency": "eur",
                    "product_data": {
                        "name": f"KOMPAGNON {package['name']}",
                        "description": package["description"],
                    },
                    "unit_amount": package["price"],
                },
                "quantity": 1,
            }],
            mode="payment",
            customer_email=customer_email or None,
            metadata={
                "package": package_id,
                "company_name": company_name,
                "customer_name": customer_name,
                "customer_email": customer_email,
                "website_url": website_url,
                "phone": phone,
            },
            success_url=f"{FRONTEND_URL}/checkout/success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{FRONTEND_URL}/checkout?cancelled=1",
            locale="de",
        )
        return {"checkout_url": session.url, "session_id": session.id}
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error: {e}")
        raise HTTPException(400, str(e))


@router.post("/webhook")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    payload = await request.body()
    sig = request.headers.get("stripe-signature")

    if not WEBHOOK_SECRET:
        logger.warning("Stripe webhook secret not configured")
        raise HTTPException(400, "Webhook nicht konfiguriert")

    try:
        event = stripe.Webhook.construct_event(payload, sig, WEBHOOK_SECRET)
    except Exception as e:
        logger.error(f"Webhook verification failed: {e}")
        raise HTTPException(400, "Webhook Fehler")

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        _handle_successful_payment(session, db)

    return {"status": "ok"}


def _handle_successful_payment(session: dict, db: Session):
    """
    Nach erfolgreicher Stripe-Zahlung:
    1. Lead anlegen
    2. User + temporaeres Passwort anlegen
    3. Willkommens-E-Mail senden
    4. Projekt anlegen
    5. Content-Scraper im Hintergrund starten
    """
    meta        = session.get("metadata", {})
    email       = meta.get("customer_email") or session.get("customer_email", "")
    company     = meta.get("company_name", "")
    name        = meta.get("customer_name", "")
    package_id  = meta.get("package", "kompagnon")
    website_url = meta.get("website_url", "")
    phone_nr    = meta.get("phone", "") or \
                  (session.get("customer_details") or {}).get("phone", "")
    amount      = (session.get("amount_total", 0) or 0) / 100

    name_parts = name.split(" ", 1)
    first_name = name_parts[0] if name_parts else ""
    last_name  = name_parts[1] if len(name_parts) > 1 else ""

    # ── 1. LEAD ANLEGEN ──────────────────────────────────────
    lead = Lead(
        company_name = company or email or "Stripe-Kunde",
        contact_name = name,
        email        = email,
        phone        = phone_nr,
        website_url  = website_url,
        lead_source  = "stripe_checkout",
        status       = "won",
        notes        = (
            f"Zahlung: {amount:.2f} EUR | "
            f"Paket: {package_id} | "
            f"Stripe: {session.get('id', '')}"
        ),
    )
    db.add(lead)
    db.flush()  # lead.id jetzt verfuegbar
    logger.info(f"Stripe: Lead {lead.id} angelegt fuer {company}")

    # ── 2. USER ANLEGEN ──────────────────────────────────────
    temp_pw = None
    if email:
        existing = db.query(User).filter(User.email == email).first()
        if not existing:
            from auth import hash_password
            temp_pw = secrets.token_urlsafe(12)
            user = User(
                email         = email,
                password_hash = hash_password(temp_pw),
                first_name    = first_name,
                last_name     = last_name,
                role          = "kunde",
                lead_id       = lead.id,
                is_active     = True,
                is_verified   = True,
            )
            db.add(user)
            logger.info(f"Stripe: User {email} angelegt (kunde)")
        else:
            logger.info(f"Stripe: User {email} existiert bereits")

    # ── 3. PROJEKT ANLEGEN ───────────────────────────────────
    project_id = None
    try:
        existing_project = db.query(Project).filter(
            Project.lead_id == lead.id
        ).first()
        if not existing_project:
            project = Project(
                lead_id      = lead.id,
                status       = "phase_1",
                start_date   = datetime.utcnow(),
                fixed_price  = {
                    "starter":   1500.0,
                    "kompagnon": 2000.0,
                    "premium":   2800.0,
                }.get(package_id, 2000.0),
                hourly_rate   = 45.0,
                ai_tool_costs = 50.0,
            )
            db.add(project)
            db.flush()
            project_id = project.id
            if create_project_checklists:
                create_project_checklists(db, project.id)
            logger.info(f"Stripe: Projekt {project.id} fuer Lead {lead.id} angelegt")
        else:
            project_id = existing_project.id
            logger.info(f"Stripe: Projekt bereits vorhanden ({project_id})")
    except Exception as e:
        logger.error(f"Stripe: Projekt-Anlage fehlgeschlagen: {e}")
        # Kein raise — Commit laeuft trotzdem durch

    # ── COMMIT (Lead + User + Projekt) ───────────────────────
    db.commit()

    # ── AUTO-SEQUENZ FÜR STRIPE-KÄUFER ──────────────────────
    try:
        from services.sequence_runner import start_sequence_for_lead
        import threading
        threading.Thread(
            target=start_sequence_for_lead,
            args=(lead.id,),
            daemon=True,
        ).start()
    except Exception as e:
        logger.warning(f"Stripe Auto-Sequenz Fehler: {e}")

    # ── 4. WILLKOMMENS-E-MAIL ────────────────────────────────
    if email:
        try:
            from services.email import send_email
            portal_url = os.getenv(
                "FRONTEND_URL",
                "https://kompagnon-frontend.onrender.com"
            ) + "/portal/login"
            paket_name = PACKAGE_NAMES.get(package_id, package_id)

            # Passwort-Abschnitt: nur anzeigen wenn neuer User
            if temp_pw:
                pw_section = f"""
                <h3 style="color:#1a2332;font-size:15px;margin:24px 0 10px">
                  Ihre Zugangsdaten:
                </h3>
                <table style="width:100%;border-collapse:collapse;
                              border:1px solid #e2e8f0;border-radius:8px;
                              overflow:hidden">
                  <tr style="background:#f8f9fa">
                    <td style="padding:10px 14px;font-weight:600;
                               font-size:13px;color:#64748b;
                               border-bottom:1px solid #e2e8f0;
                               width:120px">E-Mail</td>
                    <td style="padding:10px 14px;
                               border-bottom:1px solid #e2e8f0;
                               font-size:13px">{email}</td>
                  </tr>
                  <tr>
                    <td style="padding:10px 14px;font-weight:600;
                               font-size:13px;color:#64748b;
                               background:#f8f9fa">Passwort</td>
                    <td style="padding:10px 14px;font-family:monospace;
                               font-size:16px;letter-spacing:2px;
                               font-weight:600;color:#008eaa">
                      {temp_pw}
                    </td>
                  </tr>
                </table>
                <p style="font-size:12px;color:#E24B4A;margin:8px 0 0">
                  Bitte aendern Sie Ihr Passwort nach dem ersten Login.
                </p>
                """
            else:
                pw_section = """
                <p style="color:#64748b;font-size:13px">
                  Melden Sie sich mit Ihren bestehenden Zugangsdaten an.
                </p>
                """

            html_body = f"""
            <div style="font-family:Arial,sans-serif;
                        max-width:600px;margin:0 auto">
              <div style="background:#008eaa;padding:28px;
                          text-align:center;
                          border-radius:12px 12px 0 0">
                <div style="font-size:36px;margin-bottom:8px">🎉</div>
                <h1 style="color:white;margin:0;font-size:22px;
                           font-weight:700">
                  Willkommen bei KOMPAGNON!
                </h1>
              </div>
              <div style="padding:28px 32px;background:#ffffff">
                <p style="font-size:15px;color:#1a2332;margin-top:0">
                  Hallo {first_name or company or 'dort'},
                </p>
                <p style="color:#64748b;line-height:1.7;font-size:14px">
                  vielen Dank fuer Ihren Kauf! Ihre Zahlung ueber
                  <strong>{amount:.2f} EUR</strong> fuer das Paket
                  <strong>{paket_name}</strong> wurde erfolgreich
                  verarbeitet.
                </p>

                {pw_section}

                <div style="text-align:center;margin:28px 0">
                  <a href="{portal_url}"
                     style="display:inline-block;background:#008eaa;
                            color:white;padding:14px 32px;
                            border-radius:8px;text-decoration:none;
                            font-weight:700;font-size:15px">
                    Jetzt einloggen &#8594;
                  </a>
                </div>

                <h3 style="color:#1a2332;font-size:15px;
                           margin:24px 0 10px">
                  Ihre naechsten Schritte:
                </h3>
                <table style="width:100%">
                  <tr>
                    <td style="padding:6px 0;vertical-align:top;
                               width:28px;font-size:16px">1.</td>
                    <td style="padding:6px 0;font-size:13px;
                               color:#64748b;line-height:1.6">
                      Im Kundenportal einloggen und Briefing
                      ausfuellen (ca. 5 Min.)
                    </td>
                  </tr>
                  <tr>
                    <td style="padding:6px 0;vertical-align:top;
                               font-size:16px">2.</td>
                    <td style="padding:6px 0;font-size:13px;
                               color:#64748b;line-height:1.6">
                      Wir melden uns innerhalb von 24 Stunden
                      fuer den Strategy Workshop
                    </td>
                  </tr>
                  <tr>
                    <td style="padding:6px 0;vertical-align:top;
                               font-size:16px">3.</td>
                    <td style="padding:6px 0;font-size:13px;
                               color:#64748b;line-height:1.6">
                      Ihre neue Website ist in 14 Werktagen live
                    </td>
                  </tr>
                </table>

                <p style="color:#94a3b8;font-size:12px;
                          margin-top:24px;line-height:1.6">
                  Fragen? Antworten Sie einfach auf diese E-Mail
                  oder schreiben Sie uns:
                  <a href="mailto:info@kompagnon.eu"
                     style="color:#008eaa">
                    info@kompagnon.eu
                  </a>
                </p>
              </div>
              <div style="padding:16px;background:#f8f9fa;
                          text-align:center;
                          border-radius:0 0 12px 12px">
                <p style="color:#94a3b8;font-size:11px;margin:0">
                  KOMPAGNON Communications BP GmbH &bull;
                  kompagnon.eu
                </p>
              </div>
            </div>
            """

            send_email(
                to_email  = email,
                subject   = "Willkommen bei KOMPAGNON — Ihre Zugangsdaten",
                html_body = html_body,
            )
            logger.info(f"Stripe: Willkommens-E-Mail gesendet an {email}")

        except Exception as e:
            logger.error(f"Stripe: Willkommens-E-Mail Fehler: {e}")
            # E-Mail-Fehler darf Webhook NICHT zum Fehlschlagen bringen

    # ── 5. CONTENT-SCRAPER IM HINTERGRUND ───────────────────
    if website_url and lead.id:
        def _scrape_in_background(lead_id: int):
            try:
                import asyncio
                from database import SessionLocal
                from services.lead_enrichment import enrich_lead
                _db = SessionLocal()
                try:
                    asyncio.run(enrich_lead(lead_id, _db))
                    logger.info(
                        f"Stripe: Content-Scraper abgeschlossen "
                        f"fuer Lead {lead_id}"
                    )
                finally:
                    _db.close()
            except Exception as e:
                logger.error(f"Stripe: Scraper Fehler fuer Lead {lead_id}: {e}")

        t = threading.Thread(
            target=_scrape_in_background,
            args=(lead.id,),
            daemon=True,
        )
        t.start()
        logger.info(
            f"Stripe: Content-Scraper gestartet fuer Lead {lead.id} "
            f"({website_url})"
        )

    logger.info(
        f"Stripe: Zahlung verarbeitet — "
        f"Lead {lead.id} | Projekt {project_id} | {company} | "
        f"{amount:.2f} EUR | {package_id}"
    )


@router.get("/session/{session_id}")
async def get_session_status(session_id: str):
    if not stripe.api_key:
        raise HTTPException(500, "Stripe nicht konfiguriert")
    try:
        session = stripe.checkout.Session.retrieve(session_id)
        return {
            "status": session.payment_status,
            "customer_email": (session.customer_details.email if session.customer_details else ""),
            "amount": (session.amount_total or 0) / 100,
            "package": (session.metadata or {}).get("package", ""),
        }
    except Exception as e:
        raise HTTPException(400, str(e))
